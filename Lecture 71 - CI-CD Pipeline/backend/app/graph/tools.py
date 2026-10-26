import json
from dataclasses import dataclass
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.money import format_usd
from app.rag.store import KnowledgeBase
from app.schemas.tools import (
    CheckRefundEligibilityInput,
    EscalateToHumanInput,
    IssueRefundInput,
    IssueReplacementInput,
    LookupOrderInput,
    SearchKnowledgeBaseInput,
)
from app.tools.escalation import escalate_to_human
from app.tools.knowledge import search_knowledge_base
from app.tools.orders import check_refund_eligibility, lookup_order
from app.tools.refunds import issue_refund, issue_replacement


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_schema: type[BaseModel]
    activity: str


@dataclass(frozen=True)
class ToolContext:
    session: AsyncSession
    kb: KnowledgeBase | None
    min_score: float | None
    thread_id: str
    tool_call_id: str
    verified_order: str | None


SAFE_TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="search_knowledge_base",
        description=(
            "Search NorthPeak's policy and FAQ documents. Use it before answering any question "
            "about returns, refunds, shipping, warranty, product care, order statuses or "
            "contacting support. Returns passages with their source file and section, or an "
            "empty list when nothing relevant exists."
        ),
        args_schema=SearchKnowledgeBaseInput,
        activity="Looking up our policies",
    ),
    ToolSpec(
        name="lookup_order",
        description=(
            "Look up an order. Needs both the order number and the email address on the order. "
            "Returns the order, its items and delivery date, or an error when no order matches "
            "(the same error whether the number or the email is wrong)."
        ),
        args_schema=LookupOrderInput,
        activity="Checking your order",
    ),
    ToolSpec(
        name="check_refund_eligibility",
        description=(
            "Check whether one item of a verified order can be refunded under the store's "
            "rules. Look up the order first. `reason` is why the customer wants the refund. "
            "Returns a decision (eligible, needs_human_judgment, ineligible, not_applicable), "
            "the maximum refund and an explanation."
        ),
        args_schema=CheckRefundEligibilityInput,
        activity="Checking refund eligibility",
    ),
    ToolSpec(
        name="escalate_to_human",
        description=(
            "Open a support ticket so a human takes over. Summarise the situation so the "
            "customer does not have to repeat themselves. Use priority 'high' only for legal "
            "threats or chargebacks."
        ),
        args_schema=EscalateToHumanInput,
        activity="Passing your request to our team",
    ),
)

SENSITIVE_TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="issue_refund",
        description=(
            "Ask for a refund of one item of a verified order. Only call it after "
            "check_refund_eligibility returned eligible or needs_human_judgment for that item. "
            "`amount_cents` is your proposal and must not exceed the maximum refund from the "
            "eligibility check; set include_shipping only when the check says shipping is "
            "included. A human reviews every refund before money moves, so the call pauses "
            "until they decide; the result tells you the outcome."
        ),
        args_schema=IssueRefundInput,
        activity="Sending your refund for review",
    ),
    ToolSpec(
        name="issue_replacement",
        description=(
            "Ask for a replacement of one damaged, defective or wrong item from a verified, "
            "delivered order. A human reviews every replacement before it is created, so the "
            "call pauses until they decide; the result tells you the outcome."
        ),
        args_schema=IssueReplacementInput,
        activity="Sending your replacement for review",
    ),
)

ALL_TOOLS: tuple[ToolSpec, ...] = SAFE_TOOLS + SENSITIVE_TOOLS
TOOLS_BY_NAME = {spec.name: spec for spec in ALL_TOOLS}
SENSITIVE_TOOL_NAMES = frozenset(spec.name for spec in SENSITIVE_TOOLS)


async def _never_run(**_: Any) -> None:
    raise RuntimeError("Tools are run by the run_tools node, not by the model wrapper")


def bindable_tools(specs: tuple[ToolSpec, ...] = ALL_TOOLS) -> list[BaseTool]:
    return [
        StructuredTool(
            name=spec.name,
            description=spec.description,
            args_schema=spec.args_schema,
            coroutine=_never_run,
        )
        for spec in specs
    ]


async def execute_tool(name: str, raw_args: dict[str, Any], ctx: ToolContext) -> Any:
    match name:
        case "search_knowledge_base":
            args = SearchKnowledgeBaseInput.model_validate(raw_args)
            if ctx.kb is None:
                return {"error": "knowledge_base_unavailable"}
            return await search_knowledge_base(ctx.kb, args, min_score=ctx.min_score)
        case "lookup_order":
            return await lookup_order(ctx.session, LookupOrderInput.model_validate(raw_args))
        case "check_refund_eligibility":
            return await check_refund_eligibility(
                ctx.session,
                CheckRefundEligibilityInput.model_validate(raw_args),
                verified_order=ctx.verified_order,
            )
        case "escalate_to_human":
            return await escalate_to_human(
                ctx.session, EscalateToHumanInput.model_validate(raw_args), thread_id=ctx.thread_id
            )
        case "issue_refund":
            return await issue_refund(
                ctx.session,
                IssueRefundInput.model_validate(raw_args),
                thread_id=ctx.thread_id,
                tool_call_id=ctx.tool_call_id,
                verified_order=ctx.verified_order,
            )
        case "issue_replacement":
            return await issue_replacement(
                ctx.session,
                IssueReplacementInput.model_validate(raw_args),
                thread_id=ctx.thread_id,
                tool_call_id=ctx.tool_call_id,
                verified_order=ctx.verified_order,
            )
        case _:
            return {"error": "unknown_tool"}


def with_usd(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            out[key] = with_usd(item)
            if key.endswith("_cents") and isinstance(item, int) and not isinstance(item, bool):
                out[key.removesuffix("_cents") + "_usd"] = format_usd(item)
        return out
    if isinstance(value, list):
        return [with_usd(item) for item in value]
    return value


def observation(result: Any) -> str:
    return json.dumps(with_usd(result), default=str)
