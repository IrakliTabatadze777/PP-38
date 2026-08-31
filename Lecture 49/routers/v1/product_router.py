from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import UserRequestSchema
from core.database import get_db
from core.dependencies import require_permission
from models import User
from models.permission import PermissionCode


router = APIRouter(prefix='/products', tags=['Products'])


@router.get('/')
async def get_products(db: AsyncSession = Depends(get_db)):
    return {'message': 'get_products'}


@router.get('/{product_id}')
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    return {'message': 'get_product', 'product_id': product_id}


@router.post('/')
async def create_product(
    product: UserRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_CREATE)),
):
    return {'message': 'create_product'}


@router.delete('/{product_id}')
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_DELETE)),
):
    return {'message': 'delete_product'}
