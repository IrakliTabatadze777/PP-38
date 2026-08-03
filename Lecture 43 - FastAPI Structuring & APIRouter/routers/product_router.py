
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from services.product_service import ProductService

router = APIRouter(prefix='/products', tags=['Products'])


@router.get('/')
async def get_product(db: AsyncSession = Depends(get_db)):
    products_srv = ProductService(db)
    products = await products_srv.get_all_products()

    return {'message': 'get_products'}

@router.get('/{product_id}')
async def get_user(product_id: int, db: AsyncSession = Depends(get_db)):
    product_srv = ProductService(db)
    product = await product_srv.get_product_by_id(product_id)

    return {'message': 'get_product'}
