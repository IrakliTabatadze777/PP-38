from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import UserRegisterRequest, UserResponseSchema, UserLoginRequest, TokenPair, TokenRefresh, RefreshRequest
from services import AuthService
from core.database import get_db
from models import User
from models.user import UserRole
from core.dependencies import get_current_user, require_role


router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/register', response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db=db)
    user = await auth_service.register(data)

    return user


@router.post('/login', response_model=TokenPair, status_code=status.HTTP_200_OK)
async def login(data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db=db)
    token = await auth_service.login(data)

    return token

@router.post('/refresh', response_model=TokenRefresh, status_code=status.HTTP_200_OK)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    auth_service = AuthService(db=db)
    response = await auth_service.refresh(data.refresh_token)

    return response

@router.post('/logout', status_code=status.HTTP_200_OK)
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db=db)
    await auth_service.logout(data.refresh_token)

    return {'message': 'You have been logged out'}

# @router.get('/me', response_model=UserResponseSchema)
# async def me(current_user: User = Depends(get_current_user)):
#     return current_user


@router.get('/me', response_model=UserResponseSchema)
async def me(current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.CUSTOMER))):
    return current_user