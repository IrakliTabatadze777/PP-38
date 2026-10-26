from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm

from app.api.deps import SessionFactoryDep
from app.schemas.auth import LoginResponse, RefreshRequest, RegisterRequest, Role, UserInfo
from app.services import auth as service
from app.services.auth import CurrentUser
from app.services.errors import Forbidden

router = APIRouter(prefix="/auth", tags=["auth"])

bearer = HTTPBearer(auto_error=False, description="The access token from POST /auth/login")


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    factory: SessionFactoryDep,
) -> CurrentUser:
    token = credentials.credentials if credentials else None
    return await service.authenticate(factory, token)


def _require_roles(*roles: Role):
    async def check(user: Annotated[CurrentUser, Depends(current_user)]) -> CurrentUser:
        if user.role not in roles:
            raise Forbidden("forbidden", "You do not have access to this")
        return user

    return check


_customer = _require_roles("customer")
_reviewer = _require_roles("reviewer")
_admin = _require_roles("admin")

CustomerOnly = Depends(_customer)
ReviewerOnly = Depends(_reviewer)
AdminOnly = Depends(_admin)
CustomerUser = Annotated[CurrentUser, CustomerOnly]
ReviewerUser = Annotated[CurrentUser, ReviewerOnly]
AnyUser = Annotated[CurrentUser, Depends(current_user)]


@router.post("/login")
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], factory: SessionFactoryDep
) -> LoginResponse:
    return await service.login(factory, form.username, form.password)


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, factory: SessionFactoryDep) -> LoginResponse:
    return await service.register(factory, body)


@router.post("/refresh")
async def refresh(body: RefreshRequest, factory: SessionFactoryDep) -> LoginResponse:
    return await service.refresh(factory, body.refresh_token)


@router.post("/logout", status_code=204)
async def logout(body: RefreshRequest, factory: SessionFactoryDep) -> Response:
    await service.logout(factory, body.refresh_token)
    return Response(status_code=204)


@router.get("/me")
async def me(user: AnyUser) -> UserInfo:
    return UserInfo(email=user.email, name=user.name, role=user.role)
