from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
from typing import Optional
from datetime import date
from enum import Enum

# class UserCreateRequest(BaseModel):
#     name: str
#     age: int = None
#     email: Optional[str] = None
#     courses: list[str] = []


class PermissionEnum(str, Enum):
    user_create_permission = 'user_create_permission'
    user_edit_permission = 'user_edit_permission'
    user_delete_permission = 'user_delete_permission'

class PermissionsRequest(BaseModel):
    name: PermissionEnum


class UserCreateRequest(BaseModel):
    name: str
    age: int = None
    email: Optional[str] = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$", description='Email address')
    courses: list[str] = []
    start_date: date
    end_date: date
    permissions: list[PermissionsRequest]


    @field_validator('email')
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


    @model_validator(mode='after')
    def check_date(self):
        if self.end_date <= self.start_date:
            raise ValueError('end_date must be after start_date')
        return self


class UserCreateResponse(BaseModel):
    name: str
    age: int = None
