from typing import Literal

from pydantic import BaseModel, Field

RefundReason = Literal["damaged", "defective", "changed_mind", "wrong_item", "other"]
ReplacementReason = Literal["damaged", "defective", "wrong_item"]


class LookupOrderInput(BaseModel):
    order_number: str = Field(description="The order number the customer gave.")
    email: str = Field(description="The email address on the order.")


class CheckRefundEligibilityInput(BaseModel):
    order_number: str
    item_id: int = Field(description="The item_id returned by the order lookup.")
    reason: RefundReason


class IssueRefundInput(BaseModel):
    order_number: str
    item_id: int
    amount_cents: int = Field(ge=0, description="Proposed refund in cents.")
    include_shipping: bool
    reason: RefundReason


class IssueReplacementInput(BaseModel):
    order_number: str
    item_id: int
    reason: ReplacementReason


class EscalateToHumanInput(BaseModel):
    summary: str = Field(min_length=1, description="What the customer needs and what was tried.")
    priority: Literal["normal", "high"] = "normal"


class SearchKnowledgeBaseInput(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=4, ge=1, le=10)
