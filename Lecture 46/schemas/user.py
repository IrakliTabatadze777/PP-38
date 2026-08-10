from pydantic import BaseModel, ConfigDict

class UserRequestSchema(BaseModel):
    name: str
    email: str = None

class UserResponseSchema(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)