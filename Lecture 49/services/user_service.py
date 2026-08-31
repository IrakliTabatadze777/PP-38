from sqlalchemy.ext.asyncio import AsyncSession
from repositories import UserRepository
from fastapi import HTTPException, status

class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def get_user_by_id(self, user_id: int):
        user = await self.repository.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'User with id {user_id} was not found.'
            )

        return user