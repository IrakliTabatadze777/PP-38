from sqlalchemy.ext.asyncio import AsyncSession
from repositories import ProductRepository
from fastapi import HTTPException, status

class ProductService:
    def __init__(self, db: AsyncSession):
        self.repository = ProductRepository(db)

    async def get_all_products(self):
        products = self.repository.get_all_products()
        return products

    async def get_product_by_id(self, product_id: int):
        product = await self.repository.get_product_by_id(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'User with id {product_id} was not found.'
            )

        return product