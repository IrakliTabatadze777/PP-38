from pydantic import BaseModel

class UserRequestSchema(BaseModel):
    name: str
    email: str = None

class UserResponseSchema(BaseModel):
    pass