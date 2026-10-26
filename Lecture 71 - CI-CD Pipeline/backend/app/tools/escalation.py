from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import tickets
from app.schemas.tools import EscalateToHumanInput


async def escalate_to_human(
    session: AsyncSession, args: EscalateToHumanInput, *, thread_id: str
) -> dict[str, Any]:
    ticket = await tickets.create(
        session, thread_id=thread_id, summary=args.summary, priority=args.priority
    )
    return {"ticket_id": ticket.id}
