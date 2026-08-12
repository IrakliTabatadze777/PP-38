from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import UserRequestSchema
from services import UserService
from core.database import get_db
from core.dependencies import require_permission
from models import User
from models.permission import PermissionCode


router = APIRouter(prefix='/users', tags=['Users'])


@router.get('/')
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.USERS_READ)),
):
    return {'message': 'get_users'}


@router.get('/{user_id}')
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.USERS_READ)),
):
    user_srv = UserService(db)
    user = await user_srv.get_user_by_id(user_id)

    return {'message': 'get_user', 'user_id': user.id}


@router.post('/')
async def create_user(
    user: UserRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.USERS_CREATE)),
):
    return {'message': 'create_user'}


@router.delete('/{user_id}')
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.USERS_DELETE)),
):
    return {'message': 'delete_user'}
