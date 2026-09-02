from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import UserRegisterRequest, UserResponseSchema, UserLoginRequest, TokenPair, TokenRefresh, RefreshRequest
from services import AuthService, PermissionService
from core.database import get_db
from models import User
from core.dependencies import get_current_user


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
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
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


@router.get('/me/permissions')
async def my_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    permission_service = PermissionService(db)
    permissions = await permission_service.get_codes_for_role(current_user.role)
    return {
        'role': current_user.role,
        'permissions': sorted(permissions),
    }






async def back_task_numbers(number):
    print(f'back task number: {number}')
    # for i in range(number):
        # print(i*i)


async def back_task_text(txt):
    print(f'back task text: {txt}')
    # for i in range(1000000):
    #     print('Hello BackgroundTasks')


@router.get('/me')
async def me(back_task: BackgroundTasks):

    back_task.add_task(back_task_numbers, 123456789)
    back_task.add_task(back_task_text, txt='Hello *ARGS')

    return {'back': 'task'}