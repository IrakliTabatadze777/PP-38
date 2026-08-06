from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import UserRegisterRequest, UserResponseSchema, UserLoginRequest
from services import AuthService
from core.database import get_db
from models import User
from core.dependencies import get_current_user


router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/register', response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db=db)
    user = await auth_service.register(data)

    return user


@router.post('/login')
async def login(data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db=db)
    token = await auth_service.login(data)

    return token



@router.get('/me', response_model=UserResponseSchema)
async def me(current_user: User = Depends(get_current_user)):
    return current_user