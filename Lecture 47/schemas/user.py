from pydantic import BaseModel, ConfigDict
from models.user import UserRole

class UserRequestSchema(BaseModel):
    name: str
    email: str = None

class UserResponseSchema(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
