import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import settings
from app.db.models import User
from app.repositories import refresh_tokens, users
from app.schemas.auth import LoginResponse, RegisterRequest, Role, UserInfo
from app.security import (
    DUMMY_HASH,
    create_access_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    secret_is_usable,
    verify_password,
)
from app.services.errors import Conflict, NotAuthenticated, Unavailable

SessionFactory = async_sessionmaker[AsyncSession]


@dataclass(frozen=True)
class CurrentUser:
    id: int
    email: str
    name: str
    role: Role


def _secret() -> str:
    secret = settings.jwt_secret
    if not secret_is_usable(secret):
        raise Unavailable("auth_unavailable", "Sign-in is not available right now")
    return secret


def _not_authenticated() -> NotAuthenticated:
    return NotAuthenticated("not_authenticated", "Please sign in again")


def _invalid_credentials() -> NotAuthenticated:
    return NotAuthenticated("invalid_credentials", "Wrong email or password")


def _invalid_refresh_token() -> NotAuthenticated:
    return NotAuthenticated("invalid_refresh_token", "Please sign in again")


def _new_family() -> str:
    return uuid.uuid4().hex


def _start_tokens(session: AsyncSession, user: User, secret: str, family_id: str) -> LoginResponse:
    access_lifetime = timedelta(minutes=settings.jwt_access_expire_minutes)
    refresh_lifetime = timedelta(days=settings.jwt_refresh_expire_days)
    refresh_token = new_refresh_token()
    refresh_tokens.add(
        session,
        user_id=user.id,
        family_id=family_id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.now(UTC) + refresh_lifetime,
    )
    return LoginResponse(
        access_token=create_access_token(user.id, user.role, secret, access_lifetime),
        refresh_token=refresh_token,
        expires_in=int(access_lifetime.total_seconds()),
        refresh_expires_in=int(refresh_lifetime.total_seconds()),
        user=UserInfo(email=user.email, name=user.name, role=user.role),
    )


async def authenticate(factory: SessionFactory, access_token: str | None) -> CurrentUser:
    secret = _secret()
    if access_token is None:
        raise _not_authenticated()
    try:
        user_id = decode_access_token(access_token, secret)
    except jwt.InvalidTokenError:
        raise _not_authenticated() from None
    async with factory() as session:
        user = await users.get(session, user_id)
    if user is None or not user.is_active:
        raise _not_authenticated()
    return CurrentUser(id=user.id, email=user.email, name=user.name, role=user.role)


async def login(factory: SessionFactory, email: str, password: str) -> LoginResponse:
    secret = _secret()
    async with factory() as session:
        user = await users.get_by_email(session, email.strip().lower())
    password_ok = verify_password(password, user.password_hash if user else DUMMY_HASH)
    if user is None or not user.is_active or not password_ok:
        raise _invalid_credentials()
    async with factory() as session:
        await refresh_tokens.delete_expired(session, user.id, datetime.now(UTC))
        response = _start_tokens(session, user, secret, _new_family())
        await session.commit()
    return response


async def register(factory: SessionFactory, body: RegisterRequest) -> LoginResponse:
    secret = _secret()
    async with factory() as session:
        user = await users.create(
            session,
            email=body.email,
            name=body.name,
            password_hash=hash_password(body.password),
            role="customer",
        )
        if user is None:
            raise Conflict("email_taken", "An account with this email already exists")
        response = _start_tokens(session, user, secret, _new_family())
        await session.commit()
    return response


async def refresh(factory: SessionFactory, refresh_token: str) -> LoginResponse:
    secret = _secret()
    now = datetime.now(UTC)
    response: LoginResponse | None = None
    async with factory() as session:
        row = await refresh_tokens.get_by_hash(
            session, hash_refresh_token(refresh_token), lock=True
        )
        if row is not None:
            user = await users.get(session, row.user_id)
            usable = row.revoked_at is None and row.expires_at > now
            if usable and user is not None and user.is_active:
                refresh_tokens.revoke(row, now)
                response = _start_tokens(session, user, secret, row.family_id)
            elif row.revoked_at is not None or row.expires_at > now:
                await refresh_tokens.revoke_family(session, row.family_id, now)
        await session.commit()
    if response is None:
        raise _invalid_refresh_token()
    return response


async def logout(factory: SessionFactory, refresh_token: str) -> None:
    async with factory() as session:
        row = await refresh_tokens.get_by_hash(session, hash_refresh_token(refresh_token))
        if row is not None:
            await refresh_tokens.revoke_family(session, row.family_id, datetime.now(UTC))
        await session.commit()
