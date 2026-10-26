import json
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Request
from langgraph.graph.state import CompiledStateGraph
from sse_starlette.sse import EventSourceResponse

from app.api.auth import CustomerOnly, CustomerUser
from app.api.deps import SessionFactoryDep
from app.api.errors import ApiError
from app.schemas.chat import (
    THREAD_ID_PATTERN,
    ChatRequest,
    ThreadResponse,
    ThreadSummary,
)
from app.services import chat as service

router = APIRouter(tags=["chat"], dependencies=[CustomerOnly])


def get_graph(request: Request) -> CompiledStateGraph:
    graph: CompiledStateGraph | None = getattr(request.app.state, "graph", None)
    if graph is None:
        raise ApiError(503, "agent_unavailable", "The assistant is not available right now")
    return graph


GraphDep = Annotated[CompiledStateGraph, Depends(get_graph)]


def sse(event: str, data: dict[str, Any]) -> dict[str, str]:
    return {"event": event, "data": json.dumps(data)}


async def sse_events(events: AsyncIterator[service.ChatEvent]) -> AsyncIterator[dict[str, str]]:
    async for event, data in events:
        yield sse(event, data)


@router.post("/chat")
async def chat(
    body: ChatRequest, graph: GraphDep, factory: SessionFactoryDep, user: CustomerUser
) -> EventSourceResponse:
    thread_id = await service.open_thread(graph, factory, user, body.message, body.thread_id)
    return EventSourceResponse(
        sse_events(service.stream_chat(graph, factory, thread_id, body.message))
    )


@router.get("/threads")
async def list_threads(factory: SessionFactoryDep, user: CustomerUser) -> list[ThreadSummary]:
    return await service.list_threads(factory, user)


@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: Annotated[str, Path(pattern=THREAD_ID_PATTERN)],
    graph: GraphDep,
    factory: SessionFactoryDep,
    user: CustomerUser,
) -> ThreadResponse:
    return await service.get_thread(graph, factory, user, thread_id)
