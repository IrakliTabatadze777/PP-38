from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.db.models import Approval

APPROVED_STATUSES = ("approved", "edited")


async def get(session: AsyncSession, approval_id: str) -> Approval | None:
    return await session.get(Approval, approval_id)


async def list_recent(session: AsyncSession, status: str | None, limit: int) -> list[Approval]:
    query = select(Approval).order_by(Approval.created_at.desc(), Approval.id).limit(limit)
    if status:
        query = query.where(Approval.status == status)
    return list(await session.scalars(query))


async def find_approved(
    session: AsyncSession, thread_id: str, tool_call_id: str, tool: str
) -> Approval | None:
    return await session.scalar(
        select(Approval).where(
            Approval.thread_id == thread_id,
            Approval.tool_call_id == tool_call_id,
            Approval.tool == tool,
            Approval.status.in_(APPROVED_STATUSES),
        )
    )


async def insert_pending(
    session: AsyncSession,
    *,
    approval_id: str,
    thread_id: str,
    tool_call_id: str,
    tool: str,
    args: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    await session.execute(
        insert(Approval)
        .values(
            id=approval_id,
            thread_id=thread_id,
            tool_call_id=tool_call_id,
            tool=tool,
            args_json=args,
            payload=payload,
            status="pending",
        )
        .on_conflict_do_nothing(constraint="approvals_thread_tool_call_key")
    )


async def claim_pending(
    session: AsyncSession,
    approval_id: str,
    *,
    status: str,
    reviewer_id: str,
    reason: str | None,
    args: dict[str, Any],
) -> bool:
    claimed = await session.scalar(
        update(Approval)
        .where(Approval.id == approval_id, Approval.status == "pending")
        .values(
            status=status,
            reviewer_id=reviewer_id,
            reason=reason,
            args_json=args,
            decided_at=func.now(),
        )
        .returning(Approval.id)
    )
    return claimed is not None
