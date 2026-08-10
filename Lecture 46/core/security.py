from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from .config import settings
import uuid

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

blacklist_token = []

def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()

    current_time = datetime.utcnow()
    access_token_lifetime = timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES)


    expire_time = current_time + access_token_lifetime

    to_encode.update({'exp': expire_time, 'type': 'access', 'jti': str(uuid.uuid4())})

    jwt_obj = jwt.encode(to_encode, settings.secret, algorithm=settings.algorithm)

    return jwt_obj


def create_refresh_token(data: dict):
    to_encode = data.copy()

    current_time = datetime.utcnow()
    refresh_token_lifetime = timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS)

    expire_time = current_time + refresh_token_lifetime

    to_encode.update({'exp': expire_time, 'type': 'refresh', 'jti': str(uuid.uuid4())})

    jwt_obj = jwt.encode(to_encode, settings.secret, algorithm=settings.algorithm)

    return jwt_obj


def decode_token(token: str) -> dict:
    try:
        decoded = jwt.decode(token, settings.secret, algorithms=[settings.algorithm])

        return decoded
    except Exception as e:
        print(e)


def revoke_token(jti: str):
    blacklist_token.append(jti)

def is_token_blacklisted(jti: str):
    return jti in blacklist_token