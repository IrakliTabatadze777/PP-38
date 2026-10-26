from typing import Literal

from langchain_core.messages import AIMessage

from app.graph.state import SupportState

Route = Literal["tools", "limit_escalation", "end"]


def route_after_agent(state: SupportState, *, max_steps: int) -> Route:
    last = state["messages"][-1]
    if not (isinstance(last, AIMessage) and last.tool_calls):
        return "end"
    if state.get("steps", 0) > max_steps:
        return "limit_escalation"
    return "tools"
