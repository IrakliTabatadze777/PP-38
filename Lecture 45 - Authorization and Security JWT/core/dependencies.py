from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .security import decode_token
from jose import JWTError



from services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v2/auth/login')


creadentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):

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