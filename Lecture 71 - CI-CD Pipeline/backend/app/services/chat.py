import logging
import uuid
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import settings
from app.graph.build import recursion_limit
from app.graph.tools import TOOLS_BY_NAME
from app.repositories import conversations
from app.schemas.chat import ThreadMessage, ThreadResponse, ThreadSummary
from app.services.auth import CurrentUser
from app.services.errors import Conflict, NotFound

logger = logging.getLogger(__name__)

SessionFactory = async_sessionmaker[AsyncSession]
ChatEvent = tuple[str, dict]

ERROR_EVENT = {"code": "internal_error", "message": "Something went wrong. Please try again."}
CUSTOMER_FACING_NODES = {"agent", "limit_escalation"}
TITLE_LENGTH = 60
THREAD_LIST_LIMIT = 50


def conversation_title(message: str) -> str:
    text = " ".join(message.split())
    return text if len(text) <= TITLE_LENGTH else text[: TITLE_LENGTH - 1].rstrip() + "…"


def run_config(thread_id: str) -> RunnableConfig:
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": recursion_limit(settings.max_agent_steps),
    }


async def pending_approval_id(graph: CompiledStateGraph, thread_id: str) -> str | None:
    snapshot = await graph.aget_state(run_config(thread_id))
    for task in snapshot.tasks:
        for interrupt in task.interrupts:
            return interrupt.value["approval_id"]
    return None


async def _require_own_conversation(
    factory: SessionFactory, thread_id: str, user: CurrentUser
) -> None:
    async with factory() as session:
        owner = await conversations.get_owner(session, thread_id)
    if owner is None or owner != user.email:
        raise NotFound("thread_not_found", "No such conversation")


async def _record_conversation(factory: SessionFactory, thread_id: str) -> None:
    try:
        async with factory() as session:
            await conversations.touch(session, thread_id)
            await session.commit()
    except Exception:
        logger.exception(
            "Conversation update failed",
            extra={"event": "conversation_update_failed", "thread_id": thread_id},
        )


async def open_thread(
    graph: CompiledStateGraph,
    factory: SessionFactory,
    user: CurrentUser,
    message: str,
    thread_id: str | None,
) -> str:
    if thread_id is None:
        thread_id = f"t-{uuid.uuid4().hex}"
        async with factory() as session:
            conversations.create(
                session,
                thread_id=thread_id,
                title=conversation_title(message),
                customer_email=user.email,
            )
            await session.commit()
        return thread_id
    await _require_own_conversation(factory, thread_id, user)
    if not (await graph.aget_state(run_config(thread_id))).values:
        raise NotFound("thread_not_found", "No such conversation")
    if await pending_approval_id(graph, thread_id):
        raise Conflict("thread_awaiting_approval", "Your request is still under review")
    return thread_id


async def stream_chat(
    graph: CompiledStateGraph, factory: SessionFactory, thread_id: str, message: str
) -> AsyncIterator[ChatEvent]:
    yield "thread", {"thread_id": thread_id}
    logger.info("Chat started", extra={"event": "chat_started", "thread_id": thread_id})
    try:
        async for part in graph.astream(
            {"messages": [HumanMessage(message)], "steps": 0},
            run_config(thread_id),
            stream_mode=["messages", "updates"],
            version="v2",
        ):
            if part["type"] == "messages":
                chunk, metadata = part["data"]
                if (
                    isinstance(chunk, AIMessage)
                    and chunk.text
                    and metadata.get("langgraph_node") in CUSTOMER_FACING_NODES
                ):
                    yield "token", {"text": chunk.text}
            elif part["type"] == "updates":
                for node, update_ in part["data"].items():
                    if node == "__interrupt__":
                        await _record_conversation(factory, thread_id)
                        yield "awaiting_approval", {"approval_id": update_[0].value["approval_id"]}
                        logger.info(
                            "Chat paused", extra={"event": "chat_paused", "thread_id": thread_id}
                        )
                        return
                    if node != "agent":
                        continue
                    for reply in update_["messages"]:
                        for call in reply.tool_calls:
                            spec = TOOLS_BY_NAME.get(call["name"])
                            if spec:
                                yield "tool_call", {"name": spec.activity}
    except Exception:
        logger.exception("Chat run failed", extra={"event": "chat_failed", "thread_id": thread_id})
        yield "error", ERROR_EVENT
        return
    await _record_conversation(factory, thread_id)
    logger.info("Chat finished", extra={"event": "chat_finished", "thread_id": thread_id})
    yield "done", {}


async def list_threads(factory: SessionFactory, user: CurrentUser) -> list[ThreadSummary]:
    async with factory() as session:
        rows = await conversations.list_for_customer(session, user.email, THREAD_LIST_LIMIT)
        return [
            ThreadSummary(thread_id=row.thread_id, title=row.title, updated_at=row.updated_at)
            for row in rows
        ]


async def get_thread(
    graph: CompiledStateGraph, factory: SessionFactory, user: CurrentUser, thread_id: str
) -> ThreadResponse:
    await _require_own_conversation(factory, thread_id, user)
    state = await graph.aget_state(run_config(thread_id))
    if not state.values:
        raise NotFound("thread_not_found", "No such conversation")
    messages = []
    for message in state.values["messages"]:
        if isinstance(message, HumanMessage):
            messages.append(ThreadMessage(role="customer", content=message.text))
        elif isinstance(message, AIMessage) and message.text:
            messages.append(ThreadMessage(role="assistant", content=message.text))
    awaiting = await pending_approval_id(graph, thread_id) is not None
    return ThreadResponse(
        thread_id=thread_id,
        status="awaiting_approval" if awaiting else "idle",
        messages=messages,
    )
