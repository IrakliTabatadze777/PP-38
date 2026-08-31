from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Product


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_products(self):
        select_all = select(Product)
        result = await self.db.execute(select_all)

        return result.all()

    async def get_product_by_id(self, product_id: int):
        select_product = select(Product).where(Product.id == product_id)
        result = await self.db.scalars(select_product)

        product = result.first()

        return product

    async def create_product(self, name: str, price: float):
        product = Product(name=name, price=price)
        self.db.add(product)
        await self.db.commit()

        return product

    async def delete_product(self, product_id: int):
        product = await self.get_product_by_id(product_id)

        await self.db.delete(product)
        await self.db.commit()

        return product