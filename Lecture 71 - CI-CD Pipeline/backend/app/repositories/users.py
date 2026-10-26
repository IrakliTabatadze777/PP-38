from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


async def get(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email))


async def create(
    session: AsyncSession, *, email: str, name: str, password_hash: str, role: str
) -> User | None:
    user = User(email=email, name=name, password_hash=password_hash, role=role)
    session.add(user)
    try:
        await session.flush()
    except IntegrityError:
        return None
    return user
