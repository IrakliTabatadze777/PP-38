from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_users(self):
        select_all = select(User)
        result = await self.db.execute(select_all)

        return result.all()

    async def get_user_by_id(self, user_id: int):
        select_user = select(User).where(User.id == user_id)
        result = await self.db.scalars(select_user)

        user = result.first()

        return user


    async def get_user_by_email(self, email: str):
        result = await self.db.scalars(select(User).where(User.email == email))
        return result.first()


    async def create_user(self, name: str, email: str, hashed_password: str):
        user = User(name=name, email=email, hashed_password=hashed_password)
        self.db.add(user)
        await self.db.commit()

        return user

    async def delete_user(self, user_id: int):
        user = await self.get_user_by_id(user_id)

        await self.db.delete(user)
        await self.db.commit()

        return user