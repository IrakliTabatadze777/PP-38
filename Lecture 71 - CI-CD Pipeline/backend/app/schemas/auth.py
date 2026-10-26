import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Role = Literal["customer", "reviewer", "admin"]


class UserInfo(BaseModel):
    email: str
    name: str
    role: Role


MAX_EMAIL_LENGTH = 254
_EMAIL_SHAPE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class RegisterRequest(BaseModel):
    email: str
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _clean_email(cls, value: str) -> str:
        email = value.strip().lower()
        if len(email) > MAX_EMAIL_LENGTH or not _EMAIL_SHAPE.fullmatch(email):
            raise ValueError("not a valid email address")
        return email

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("name is required")
        return name


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    refresh_expires_in: int
    user: UserInfo


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=200)
