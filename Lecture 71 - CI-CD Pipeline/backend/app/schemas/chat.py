from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

THREAD_ID_PATTERN = r"^[A-Za-z0-9_-]{1,100}$"


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    thread_id: str | None = Field(default=None, pattern=THREAD_ID_PATTERN)
    message: str = Field(min_length=1, max_length=2000)


class ThreadMessage(BaseModel):
    role: Literal["customer", "assistant"]
    content: str


class ThreadResponse(BaseModel):
    thread_id: str
    status: Literal["idle", "awaiting_approval"]
    messages: list[ThreadMessage]


class ThreadSummary(BaseModel):
    thread_id: str
    title: str
    updated_at: datetime
