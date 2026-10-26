from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class SupportState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    verified_order: str | None
    verified_email: str | None
    approval_decisions: dict[str, dict]
    steps: int
    ticket_id: str | None
