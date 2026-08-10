
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import UserRequestSchema
from services import UserService
from core.database import get_db
from core.config import settings


router = APIRouter(prefix='/users', tags=['Users'])


@router.get('/')
async def get_users(db: AsyncSession = Depends(get_db)):
    # user_rep = UserRepository(db)
    # users = user_rep.get_all_users()

    return {'message': 'get_users'}

@router.get('/{user_id}')
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user_srv = UserService(db)
    user = await user_srv.get_user_by_id(user_id)

    return {'message': 'get_user'}

@router.post('/')
async def create_user(user: UserRequestSchema, db: AsyncSession = Depends(get_db)):
    # user_rep = UserRepository(db)
    # user = user_rep.create_user(user.name, user.email)

    return {'message': 'create_user'}

@router.delete('/{user_id}')
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    # user_rep = UserRepository(db)
    # user = user_rep.delete_user(user_id)

    return {'message': 'delete_user'}