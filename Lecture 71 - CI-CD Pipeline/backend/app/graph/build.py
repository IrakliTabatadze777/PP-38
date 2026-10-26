from functools import partial

from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.graph.nodes import (
    GraphDeps,
    make_agent_node,
    make_approval_gate_node,
    make_limit_escalation_node,
    make_run_tools_node,
)
from app.graph.routing import route_after_agent
from app.graph.state import SupportState
from app.rag.store import KnowledgeBase


def recursion_limit(max_steps: int) -> int:
    return 4 * (max_steps + 1) + 5


def build_graph(
    *,
    model: BaseChatModel,
    session_factory: async_sessionmaker[AsyncSession],
    kb: KnowledgeBase | None,
    checkpointer: BaseCheckpointSaver,
    max_steps: int,
    min_score: float | None = None,
) -> CompiledStateGraph:
    deps = GraphDeps(model=model, session_factory=session_factory, kb=kb, min_score=min_score)

    graph = StateGraph(SupportState)
    graph.add_node("agent", make_agent_node(deps))
    graph.add_node("approval_gate", make_approval_gate_node(deps))
    graph.add_node("run_tools", make_run_tools_node(deps))
    graph.add_node("limit_escalation", make_limit_escalation_node(deps))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        partial(route_after_agent, max_steps=max_steps),
        {"tools": "approval_gate", "limit_escalation": "limit_escalation", "end": END},
    )
    graph.add_edge("approval_gate", "run_tools")
    graph.add_edge("run_tools", "agent")
    graph.add_edge("limit_escalation", END)
    return graph.compile(checkpointer=checkpointer)
