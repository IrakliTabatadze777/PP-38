from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import require_permission
from models import User
from models.permission import PermissionCode


router = APIRouter(prefix='/orders', tags=['Orders'])


@router.get('/')
async def get_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.ORDERS_READ)),
):
    return {'message': 'get_orders'}


@router.get('/{order_id}')
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.ORDERS_READ)),
):
    return {'message': 'get_order', 'order_id': order_id}


@router.post('/')
async def create_order(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.ORDERS_CREATE)),
):
    return {'message': 'create_order', 'user_id': current_user.id}


@router.delete('/{order_id}')
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.ORDERS_DELETE)),
):
    return {'message': 'delete_order'}
