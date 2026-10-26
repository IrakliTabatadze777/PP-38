from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation


def create(session: AsyncSession, *, thread_id: str, title: str, customer_email: str) -> None:
    session.add(Conversation(thread_id=thread_id, title=title, customer_email=customer_email))


async def get_owner(session: AsyncSession, thread_id: str) -> str | None:
    return await session.scalar(
        select(Conversation.customer_email).where(Conversation.thread_id == thread_id)
    )


async def touch(session: AsyncSession, thread_id: str) -> None:
    await session.execute(
        update(Conversation)
        .where(Conversation.thread_id == thread_id)
        .values(updated_at=func.now())
    )


async def list_for_customer(
    session: AsyncSession, customer_email: str, limit: int
) -> list[Conversation]:
    rows = await session.scalars(
        select(Conversation)
        .where(Conversation.customer_email == customer_email)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    return list(rows)
