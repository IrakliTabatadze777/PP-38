from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .security import decode_token
from jose import JWTError
from models.user import UserRole, User
from models.permission import PermissionCode

from services.user_service import UserService
from services.permission_service import PermissionService

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

    if 'permissions' in payload:
        user.token_permissions = list(payload.get('permissions') or [])
    else:
        user.token_permissions = None
    user.token_payload = payload

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


def require_permission(*permission_codes: str | PermissionCode):
    required = {
        code.value if isinstance(code, PermissionCode) else code
        for code in permission_codes
    }

    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        token_permissions = getattr(current_user, 'token_permissions', None)
        if token_permissions is not None:
            user_permissions = set(token_permissions)
        else:
            permission_service = PermissionService(db)
            user_permissions = await permission_service.get_codes_for_role(current_user.role)

        if not required.intersection(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required permission",
            )

        return current_user

    return permission_checker
