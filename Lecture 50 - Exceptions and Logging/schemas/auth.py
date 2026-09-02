from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


class TokenRefresh(BaseModel):
    access_token: str

class RefreshRequest(BaseModel):
    refresh_token: str