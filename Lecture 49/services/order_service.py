from sqlalchemy.ext.asyncio import AsyncSession

from repositories import OrderRepository


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repository = OrderRepository(db)

    async def create_order(self, data: dict):
        return await self.order_repository.create_order(data)
