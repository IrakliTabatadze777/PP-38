from pydantic import BaseModel, Field
from typing import Literal

class ChatRequest(BaseModel):
    message: str
    session_id: str

class AgentResponse(BaseModel):
    status: Literal['completed', 'awaiting_approval']
    user_request: str
    tool_result: str
    plan: dict
    general_answer: str
    final_note: str

class Decision(BaseModel):
    session_id: str
    action: Literal['approve', 'edit']
    daily_budget_usd: float| None = Field(default=None)