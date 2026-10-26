import logging
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Approval
from app.repositories import approvals
from app.schemas.approvals import (
    ApprovalDetail,
    ApprovalStatus,
    ApprovalSummary,
    DecisionRequest,
    DecisionResponse,
)
from app.services.auth import CurrentUser
from app.services.chat import run_config
from app.services.errors import Conflict, InvalidInput, NotFound, OutOfRange

logger = logging.getLogger(__name__)

SessionFactory = async_sessionmaker[AsyncSession]

STATUS_FOR_DECISION = {"approve": "approved", "edit": "edited", "reject": "rejected"}
STILL_WAITING_REPLY = "Your request has been decided. Another request is still waiting for review."
FALLBACK_REPLY = "The decision was recorded, but the assistant could not write its reply."


def _payload(approval: Approval) -> dict[str, Any]:
    payload = approval.payload or {}
    return {
        "args": payload.get("args", approval.args_json),
        "max_allowed_cents": payload.get("max_allowed_cents"),
        "flags": payload.get("flags", []),
        "agent_explanation": payload.get("agent_explanation", ""),
        "policy_sources": payload.get("policy_sources", []),
    }


def _summary(approval: Approval) -> ApprovalSummary:
    return ApprovalSummary(
        approval_id=approval.id,
        thread_id=approval.thread_id,
        tool=approval.tool,
        status=approval.status,
        flags=_payload(approval)["flags"],
        amount_cents=approval.args_json.get("amount_cents"),
        created_at=approval.created_at,
    )


async def _load(session: AsyncSession, approval_id: str) -> Approval:
    approval = await approvals.get(session, approval_id)
    if approval is None:
        raise NotFound("approval_not_found", "No such approval")
    return approval


def _final_args(approval: Approval, body: DecisionRequest) -> dict[str, Any]:
    args = dict(_payload(approval)["args"])
    if body.decision != "edit":
        return args
    edited = body.edited_args or {}
    amount = edited.get("amount_cents")
    if (
        approval.tool != "issue_refund"
        or set(edited) != {"amount_cents"}
        or not isinstance(amount, int)
        or isinstance(amount, bool)
    ):
        raise InvalidInput("invalid_edit", "Only the refund amount (amount_cents) can be edited")
    maximum = _payload(approval)["max_allowed_cents"]
    if maximum is None or not 0 <= amount <= maximum:
        raise OutOfRange("amount_out_of_range", "The amount is outside the allowed range")
    args["amount_cents"] = amount
    return args


async def _resume(graph: CompiledStateGraph, thread_id: str, resume: dict[str, Any]) -> str:
    try:
        result = await graph.ainvoke(Command(resume=resume), run_config(thread_id))
    except Exception:
        logger.exception(
            "Resuming a thread failed", extra={"event": "resume_failed", "thread_id": thread_id}
        )
        return FALLBACK_REPLY
    if result.get("__interrupt__"):
        return STILL_WAITING_REPLY
    last = result["messages"][-1]
    return last.text if isinstance(last, AIMessage) else ""


async def list_approvals(
    factory: SessionFactory, status: ApprovalStatus | None, limit: int
) -> list[ApprovalSummary]:
    async with factory() as session:
        return [_summary(a) for a in await approvals.list_recent(session, status, limit)]


async def get_approval(factory: SessionFactory, approval_id: str) -> ApprovalDetail:
    async with factory() as session:
        approval = await _load(session, approval_id)
    return ApprovalDetail(
        **_summary(approval).model_dump(),
        **{k: v for k, v in _payload(approval).items() if k != "flags"},
        reviewer_id=approval.reviewer_id,
        reason=approval.reason,
        decided_at=approval.decided_at,
    )


async def decide(
    graph: CompiledStateGraph,
    factory: SessionFactory,
    reviewer: CurrentUser,
    approval_id: str,
    body: DecisionRequest,
) -> DecisionResponse:
    async with factory() as session:
        approval = await _load(session, approval_id)
        if approval.status != "pending":
            raise Conflict("approval_already_decided", "This approval was already decided")
        final_args = _final_args(approval, body)
        status = STATUS_FOR_DECISION[body.decision]
        claimed = await approvals.claim_pending(
            session,
            approval_id,
            status=status,
            reviewer_id=reviewer.email,
            reason=body.reason,
            args=final_args,
        )
        await session.commit()
        if not claimed:
            raise Conflict("approval_already_decided", "This approval was already decided")
        thread_id = approval.thread_id

    logger.info(
        "Approval decided",
        extra={
            "event": "approval_decided",
            "approval_id": approval_id,
            "thread_id": thread_id,
            "decision": body.decision,
            "reviewer_id": reviewer.email,
        },
    )
    resume = {
        "decision": body.decision,
        "reviewer_id": reviewer.email,
        "args": final_args,
        "reason": body.reason,
    }
    reply = await _resume(graph, thread_id, resume)
    return DecisionResponse(
        approval_id=approval_id, status=status, thread_id=thread_id, agent_reply=reply
    )
