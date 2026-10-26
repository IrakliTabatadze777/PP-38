from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RefreshToken


def add(
    session: AsyncSession, *, user_id: int, family_id: str, token_hash: str, expires_at: datetime
) -> None:
    session.add(
        RefreshToken(
            user_id=user_id, family_id=family_id, token_hash=token_hash, expires_at=expires_at
        )
    )


async def get_by_hash(
    session: AsyncSession, token_hash: str, *, lock: bool = False
) -> RefreshToken | None:
    query = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    if lock:
        query = query.with_for_update()
    return await session.scalar(query)


def revoke(token: RefreshToken, now: datetime) -> None:
    token.revoked_at = now


async def revoke_family(session: AsyncSession, family_id: str, now: datetime) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )


async def delete_expired(session: AsyncSession, user_id: int, now: datetime) -> None:
    await session.execute(
        delete(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.expires_at < now)
    )
