from sqlalchemy.ext.asyncio import AsyncSession
from models.order import Order


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def create_order(self, data: dict):
        new_order = Order(
            user_id=data['user_id'],
            total=data['total']
        )

        self.db.add(new_order)
        await self.db.commit()

        return new_order