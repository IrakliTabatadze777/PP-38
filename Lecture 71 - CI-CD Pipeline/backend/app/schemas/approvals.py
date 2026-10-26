from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Flag = Literal["high_value", "exception"]
ApprovalStatus = Literal["pending", "approved", "edited", "rejected"]


class ApprovalPayload(BaseModel):
    approval_id: str
    thread_id: str
    tool: str
    args: dict[str, Any]
    max_allowed_cents: int | None
    flags: list[Flag]
    agent_explanation: str
    policy_sources: list[str]


class ApprovalSummary(BaseModel):
    approval_id: str
    thread_id: str
    tool: str
    status: ApprovalStatus
    flags: list[Flag]
    amount_cents: int | None
    created_at: datetime


class ApprovalDetail(ApprovalSummary):
    args: dict[str, Any]
    max_allowed_cents: int | None
    agent_explanation: str
    policy_sources: list[str]
    reviewer_id: str | None
    reason: str | None
    decided_at: datetime | None


class DecisionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    decision: Literal["approve", "edit", "reject"]
    edited_args: dict[str, Any] | None = None
    reason: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _required_fields(self) -> DecisionRequest:
        if self.decision == "edit" and not self.edited_args:
            raise ValueError("edited_args is required when the decision is edit")
        if self.decision == "reject" and not self.reason:
            raise ValueError("reason is required when the decision is reject")
        return self


class DecisionResponse(BaseModel):
    approval_id: str
    status: Literal["approved", "edited", "rejected"]
    thread_id: str
    agent_reply: str
