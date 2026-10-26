import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api import approvals, auth, chat, documents
from app.api.errors import install_error_handlers
from app.config.settings import Settings, settings
from app.config.tracing import configure_tracing
from app.db.session import create_engine, create_session_factory
from app.graph.build import build_graph
from app.graph.model import ModelNotConfigured, make_chat_model
from app.logging_config import configure_logging
from app.rag.embeddings import EmbeddingsNotConfigured, make_embeddings
from app.rag.store import KnowledgeBase

configure_logging()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str


async def _start_knowledge_base(settings: Settings, stack: AsyncExitStack) -> KnowledgeBase | None:
    try:
        kb = KnowledgeBase(make_embeddings(settings), settings.database_url)
    except EmbeddingsNotConfigured as exc:
        logger.warning("Knowledge base disabled: %s", exc)
        return None
    stack.push_async_callback(kb.aclose)
    return kb


async def _start_agent(
    settings: Settings,
    stack: AsyncExitStack,
    kb: KnowledgeBase | None,
    session_factory: async_sessionmaker[AsyncSession],
):
    try:
        model = make_chat_model(settings)
    except ModelNotConfigured as exc:
        logger.warning("Agent disabled: %s", exc)
        return None
    checkpointer = await stack.enter_async_context(
        AsyncPostgresSaver.from_conn_string(settings.checkpoint_db_url)
    )
    await checkpointer.setup()
    return build_graph(
        model=model,
        session_factory=session_factory,
        kb=kb,
        checkpointer=checkpointer,
        max_steps=settings.max_agent_steps,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_tracing(settings)
    app.state.kb = None
    app.state.graph = None
    app.state.session_factory = None
    async with AsyncExitStack() as stack:
        if settings.database_url:
            engine = create_engine(settings.database_url)
            stack.push_async_callback(engine.dispose)
            app.state.session_factory = create_session_factory(engine)
            app.state.kb = await _start_knowledge_base(settings, stack)
            if settings.checkpoint_db_url:
                app.state.graph = await _start_agent(
                    settings, stack, app.state.kb, app.state.session_factory
                )
        yield


app = FastAPI(title="Customer Support Agent", lifespan=lifespan)
install_error_handlers(app)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(approvals.router)


@app.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
