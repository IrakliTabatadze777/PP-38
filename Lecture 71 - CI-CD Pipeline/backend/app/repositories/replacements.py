from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Replacement


async def get_by_approval(session: AsyncSession, approval_id: str) -> Replacement | None:
    return await session.scalar(select(Replacement).where(Replacement.approval_id == approval_id))


async def create(
    session: AsyncSession, *, order_item_id: int, reason: str, approval_id: str
) -> Replacement:
    replacement = Replacement(order_item_id=order_item_id, reason=reason, approval_id=approval_id)
    session.add(replacement)
    await session.flush()
    return replacement
