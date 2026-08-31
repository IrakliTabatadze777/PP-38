from pydantic import BaseModel

class CreateOrderRequest(BaseModel):
    total: int


class CreateOrderResponse(BaseModel):
    id: int
    user_id: int
    total: int