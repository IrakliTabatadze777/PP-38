from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Ticket


async def create(session: AsyncSession, *, thread_id: str, summary: str, priority: str) -> Ticket:
    ticket = Ticket(thread_id=thread_id, summary=summary, priority=priority)
    session.add(ticket)
    await session.flush()
    return ticket
