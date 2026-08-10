from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .security import decode_token
from jose import JWTError
from models.user import UserRole, User

from services.user_service import UserService

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v2/auth/login')

bearer_schema = HTTPBearer()


creadentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
        credential: HTTPAuthorizationCredentials = Depends(bearer_schema),
        db: AsyncSession = Depends(get_db)
):

    token = credential.credentials

    print(token)
    try:
        payload = decode_token(token)
    except JWTError:
        raise creadentials_exception


    if payload.get('type') != 'access':
        raise creadentials_exception


    user_id = payload.get('sub')
    if not user_id:
        raise creadentials_exception


    user_service = UserService(db)
    user = await user_service.get_user_by_id(int(user_id))

    if user is None or not user.is_active:
        raise creadentials_exception

    return user


def require_role(*allowed_roles: UserRole):

    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required role",
            )

        return current_user

    return role_checker