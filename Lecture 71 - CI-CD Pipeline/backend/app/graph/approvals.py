import hashlib
import json
from typing import Any

from langchain_core.messages import BaseMessage, ToolMessage
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import policy
from app.repositories import approvals
from app.schemas.approvals import ApprovalPayload, Flag
from app.schemas.tools import IssueRefundInput, IssueReplacementInput
from app.tools.refunds import plan_refund, plan_replacement


def approval_id_for(thread_id: str, tool_call_id: str) -> str:
    digest = hashlib.sha1(f"{thread_id}:{tool_call_id}".encode()).hexdigest()
    return f"appr_{digest[:12]}"


def policy_sources_in(messages: list[BaseMessage]) -> list[str]:
    sources: list[str] = []
    for message in messages:
        if isinstance(message, ToolMessage) and message.name == "search_knowledge_base":
            try:
                passages = json.loads(message.text)
            except ValueError:
                continue
            if isinstance(passages, list):
                for passage in passages:
                    source = passage.get("source") if isinstance(passage, dict) else None
                    if source and source not in sources:
                        sources.append(source)
    return sources


def approval_flags(*, tool: str, amount_cents: int | None, decision: str) -> list[Flag]:
    flags: list[Flag] = []
    if tool == "issue_refund" and (amount_cents or 0) > policy.HIGH_VALUE_THRESHOLD_CENTS:
        flags.append("high_value")
    if decision == "needs_human_judgment":
        flags.append("exception")
    return flags


async def prepare_approval(
    session: AsyncSession,
    *,
    tool: str,
    raw_args: dict[str, Any],
    thread_id: str,
    tool_call_id: str,
    verified_order: str | None,
    policy_sources: list[str],
) -> ApprovalPayload | dict[str, Any]:
    approval_id = approval_id_for(thread_id, tool_call_id)
    try:
        if tool == "issue_refund":
            refund_args = IssueRefundInput.model_validate(raw_args)
            plan = await plan_refund(session, refund_args, verified_order=verified_order)
            if isinstance(plan, dict):
                return plan
            if refund_args.amount_cents > plan.limit_cents:
                return {"error": "amount_exceeds_limit", "max_refund_cents": plan.limit_cents}
            return ApprovalPayload(
                approval_id=approval_id,
                thread_id=thread_id,
                tool=tool,
                args=refund_args.model_dump(),
                max_allowed_cents=plan.limit_cents,
                flags=approval_flags(
                    tool=tool,
                    amount_cents=refund_args.amount_cents,
                    decision=plan.eligibility.decision,
                ),
                agent_explanation=plan.eligibility.explanation,
                policy_sources=policy_sources,
            )
        replacement_args = IssueReplacementInput.model_validate(raw_args)
        item = await plan_replacement(session, replacement_args, verified_order=verified_order)
        if isinstance(item, dict):
            return item
        return ApprovalPayload(
            approval_id=approval_id,
            thread_id=thread_id,
            tool=tool,
            args=replacement_args.model_dump(),
            max_allowed_cents=None,
            flags=[],
            agent_explanation=f"Replacement requested for a delivered item. Reason: "
            f"{replacement_args.reason}.",
            policy_sources=policy_sources,
        )
    except ValidationError as exc:
        fields = sorted({".".join(str(p) for p in err["loc"]) for err in exc.errors()})
        return {"error": "invalid_arguments", "fields": fields}


async def record_pending(
    session: AsyncSession, payload: ApprovalPayload, tool_call_id: str
) -> None:
    await approvals.insert_pending(
        session,
        approval_id=payload.approval_id,
        thread_id=payload.thread_id,
        tool_call_id=tool_call_id,
        tool=payload.tool,
        args=payload.args,
        payload=payload.model_dump(),
    )
