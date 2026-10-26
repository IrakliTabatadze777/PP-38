import json
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.graph.approvals import policy_sources_in, prepare_approval, record_pending
from app.graph.prompts import LIMIT_REACHED_MESSAGE, build_system_prompt
from app.graph.state import SupportState
from app.graph.tools import (
    SENSITIVE_TOOL_NAMES,
    ToolContext,
    bindable_tools,
    execute_tool,
    observation,
)
from app.rag.store import KnowledgeBase
from app.schemas.tools import EscalateToHumanInput
from app.tools.escalation import escalate_to_human

logger = logging.getLogger(__name__)

SUMMARY_MESSAGES = 3
SUMMARY_CHARS = 300


@dataclass(frozen=True)
class GraphDeps:
    model: BaseChatModel
    session_factory: async_sessionmaker[AsyncSession]
    kb: KnowledgeBase | None
    min_score: float | None = None


def thread_id_of(config: RunnableConfig) -> str:
    return config["configurable"]["thread_id"]


def call_key(name: str, args: dict[str, Any]) -> tuple[str, str]:
    return name, json.dumps(args, sort_keys=True, default=str)


def calls_made_this_turn(messages: list[BaseMessage]) -> set[tuple[str, str]]:
    made: set[tuple[str, str]] = set()
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            break
        if isinstance(message, AIMessage):
            made.update(call_key(call["name"], call["args"]) for call in message.tool_calls)
    return made


def summarize_for_ticket(messages: list[BaseMessage]) -> str:
    said = [m.text[:SUMMARY_CHARS] for m in messages if isinstance(m, HumanMessage)]
    recent = " | ".join(said[-SUMMARY_MESSAGES:])
    return f"The assistant reached its step limit without resolving the request. Customer: {recent}"


def make_agent_node(deps: GraphDeps) -> Callable[[SupportState], Awaitable[dict[str, Any]]]:
    model = deps.model.bind_tools(bindable_tools())
    system = SystemMessage(build_system_prompt())

    async def agent(state: SupportState) -> dict[str, Any]:
        reply = await model.ainvoke([system, *state["messages"]])
        return {"messages": [reply], "steps": state.get("steps", 0) + 1}

    return agent


def make_approval_gate_node(
    deps: GraphDeps,
) -> Callable[[SupportState, RunnableConfig], Awaitable[dict[str, Any]]]:
    async def approval_gate(state: SupportState, config: RunnableConfig) -> dict[str, Any]:
        last = state["messages"][-1]
        assert isinstance(last, AIMessage)
        thread_id = thread_id_of(config)
        decisions = dict(state.get("approval_decisions") or {})
        sources = policy_sources_in(state["messages"])

        for call in last.tool_calls:
            if call["name"] not in SENSITIVE_TOOL_NAMES or call["id"] in decisions:
                continue
            async with deps.session_factory() as session:
                prepared = await prepare_approval(
                    session,
                    tool=call["name"],
                    raw_args=call["args"],
                    thread_id=thread_id,
                    tool_call_id=call["id"],
                    verified_order=state.get("verified_order"),
                    policy_sources=sources,
                )
                if not isinstance(prepared, dict):
                    await record_pending(session, prepared, call["id"])
                    await session.commit()
            if isinstance(prepared, dict):
                decisions[call["id"]] = {"decision": "invalid", **prepared}
                continue
            logger.info(
                "Approval requested",
                extra={
                    "event": "approval_requested",
                    "thread_id": thread_id,
                    "approval_id": prepared.approval_id,
                    "tool": call["name"],
                    "flags": prepared.flags,
                },
            )
            decisions[call["id"]] = interrupt(prepared.model_dump())
        return (
            {"approval_decisions": decisions}
            if decisions != state.get("approval_decisions")
            else {}
        )

    return approval_gate


def make_run_tools_node(
    deps: GraphDeps,
) -> Callable[[SupportState, RunnableConfig], Awaitable[dict[str, Any]]]:
    async def run_tools(state: SupportState, config: RunnableConfig) -> dict[str, Any]:
        *earlier, last = state["messages"]
        assert isinstance(last, AIMessage)
        seen = calls_made_this_turn(earlier)
        updates: dict[str, Any] = {}
        results: list[ToolMessage] = []
        verified_order = state.get("verified_order")

        for call in last.tool_calls:
            key = call_key(call["name"], call["args"])
            if key in seen:
                result: Any = {"error": "duplicate_call", "hint": "Use the earlier result."}
            else:
                seen.add(key)
                result = await _run_call(deps, call, state, thread_id_of(config), verified_order)

            if call["name"] == "lookup_order" and "error" not in result:
                verified_order = result["order_number"]
                updates["verified_order"] = verified_order
                updates["verified_email"] = call["args"]["email"].strip().lower()
            if call["name"] == "escalate_to_human" and "ticket_id" in result:
                updates["ticket_id"] = str(result["ticket_id"])

            results.append(
                ToolMessage(
                    content=observation(result),
                    tool_call_id=call["id"],
                    name=call["name"],
                    status="error" if isinstance(result, dict) and "error" in result else "success",
                )
            )
        return {"messages": results, **updates}

    return run_tools


async def _run_call(
    deps: GraphDeps,
    call: dict[str, Any],
    state: SupportState,
    thread_id: str,
    verified_order: str | None,
) -> Any:
    name, args = call["name"], call["args"]
    if name in SENSITIVE_TOOL_NAMES:
        decision = (state.get("approval_decisions") or {}).get(call["id"])
        if decision is None:
            return {"error": "not_approved"}
        match decision["decision"]:
            case "reject":
                return {"status": "rejected", "reason": decision.get("reason")}
            case "invalid":
                return {k: v for k, v in decision.items() if k != "decision"}
            case "approve" | "edit":
                args = decision["args"]
            case _:
                return {"error": "not_approved"}
    return await _run_one(deps, name, args, thread_id, verified_order, call["id"])


async def _run_one(
    deps: GraphDeps,
    name: str,
    args: dict[str, Any],
    thread_id: str,
    verified_order: str | None,
    tool_call_id: str,
) -> Any:
    async with deps.session_factory() as session:
        ctx = ToolContext(
            session=session,
            kb=deps.kb,
            min_score=deps.min_score,
            thread_id=thread_id,
            tool_call_id=tool_call_id,
            verified_order=verified_order,
        )
        started = time.perf_counter()
        try:
            result = await execute_tool(name, args, ctx)
            await session.commit()
            outcome = result.get("error") if isinstance(result, dict) else None
            logger.info(
                "Tool finished",
                extra={
                    "event": "tool_run",
                    "thread_id": thread_id,
                    "tool": name,
                    "outcome": outcome or "ok",
                    "duration_ms": round((time.perf_counter() - started) * 1000),
                },
            )
            return result
        except ValidationError as exc:
            await session.rollback()
            fields = sorted({".".join(str(p) for p in err["loc"]) for err in exc.errors()})
            return {"error": "invalid_arguments", "fields": fields}
        except Exception:
            await session.rollback()
            logger.exception(
                "Tool failed", extra={"event": "tool_failed", "thread_id": thread_id, "tool": name}
            )
            return {"error": "tool_failed"}


def make_limit_escalation_node(
    deps: GraphDeps,
) -> Callable[[SupportState, RunnableConfig], Awaitable[dict[str, Any]]]:
    async def limit_escalation(state: SupportState, config: RunnableConfig) -> dict[str, Any]:
        last = state["messages"][-1]
        assert isinstance(last, AIMessage)
        skipped = [
            ToolMessage(
                content=json.dumps({"error": "step_limit_reached"}),
                tool_call_id=call["id"],
                name=call["name"],
                status="error",
            )
            for call in last.tool_calls
        ]
        async with deps.session_factory() as session:
            ticket = await escalate_to_human(
                session,
                EscalateToHumanInput(summary=summarize_for_ticket(state["messages"])),
                thread_id=thread_id_of(config),
            )
            await session.commit()
        ticket_id = str(ticket["ticket_id"])
        logger.warning(
            "Step limit reached",
            extra={
                "event": "step_limit_reached",
                "thread_id": thread_id_of(config),
                "ticket_id": ticket_id,
            },
        )
        closing = AIMessage(content=LIMIT_REACHED_MESSAGE.format(ticket_id=ticket_id))
        return {"messages": [*skipped, closing], "ticket_id": ticket_id}

    return limit_escalation
