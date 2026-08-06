from pydantic import BaseModel, EmailStr


class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenPair(BaseModel):
    access_token: str