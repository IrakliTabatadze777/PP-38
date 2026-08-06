
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password, verify_password, create_access_token
from repositories import UserRepository
from schemas import UserRegisterRequest, UserLoginRequest, TokenPair


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def register(self, user: UserRegisterRequest):
        existing = await self.repository.get_user_by_email(user.email)

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )


        hashed_password = hash_password(user.password)

        user = await self.repository.create_user(name=user.name, email=user.email, hashed_password=hashed_password)

        return user


    async def login(self, data: UserLoginRequest):
        user = await self.repository.get_user_by_email(email=data.email)

        hashed_password = user.hashed_password
        plain_password = data.password

        password_ok = verify_password(plain_password, hashed_password)

        if user is None or not password_ok or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = await self._issue_token(user)

        return token



    async def _issue_token(self, user):
        token_data = {'sub': str(user.id), 'email': user.email, 'name': user.name, 'is_active': user.is_active}

        access_token = create_access_token(data=token_data)

        return TokenPair(
            access_token=access_token,
        )