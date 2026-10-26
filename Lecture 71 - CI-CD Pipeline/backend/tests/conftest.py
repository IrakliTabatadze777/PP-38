import uuid
from collections.abc import AsyncIterator, Callable
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import pool, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import Settings, settings
from app.db.models import User
from app.db.session import create_session_factory
from app.graph.build import build_graph
from app.main import app
from app.rag.ingest import ingest_directory
from app.rag.store import KnowledgeBase
from app.security import create_access_token, hash_password
from scripts.seed import CUSTOMER_EMAIL, seed, seed_users, truncate_all
from tests.fakes import HashEmbeddings, ScriptedChatModel
from tests.helpers import (
    ADMIN_EMAIL,
    JWT_SECRET,
    OTHER_CUSTOMER_EMAIL,
    REVIEWER_EMAIL,
    plain_url,
)

KB_DIR = Path(__file__).resolve().parents[1] / "data" / "kb"


@pytest.fixture(scope="session")
def test_db_url() -> str:
    dev_url = settings.database_url
    if not dev_url:
        pytest.skip("DATABASE_URL is not set")
    parsed = make_url(dev_url)
    return parsed.set(database=f"{parsed.database}_test").render_as_string(hide_password=False)


@pytest.fixture(scope="session")
def migrated_test_db(test_db_url: str) -> str:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", test_db_url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    return test_db_url


@pytest.fixture
async def db_session(migrated_test_db: str) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(migrated_test_db, poolclass=pool.NullPool)
    async with create_session_factory(engine)() as session:
        await truncate_all(session)
        await session.commit()
        yield session
    await engine.dispose()


@pytest.fixture
async def kb(migrated_test_db: str) -> AsyncIterator[KnowledgeBase]:
    knowledge_base = KnowledgeBase(
        HashEmbeddings(), migrated_test_db, collection=f"kb_test_{uuid.uuid4().hex[:8]}"
    )
    yield knowledge_base
    await knowledge_base.drop()
    await knowledge_base.aclose()


@pytest.fixture
async def session_factory(db_session: AsyncSession) -> async_sessionmaker[AsyncSession]:
    await seed(db_session)
    await seed_users(db_session)
    await db_session.commit()
    return create_session_factory(db_session.bind)


@pytest.fixture
async def loaded_kb(kb: KnowledgeBase) -> KnowledgeBase:
    await ingest_directory(kb, KB_DIR)
    return kb


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.auth.settings",
        Settings(jwt_secret=JWT_SECRET, jwt_access_expire_minutes=15, jwt_refresh_expire_days=7),
    )


async def bearer_for(
    factory: async_sessionmaker[AsyncSession], email: str, expires_in: timedelta | None = None
) -> dict[str, str]:
    async with factory() as session:
        user = await session.scalar(select(User).where(User.email == email))
    token = create_access_token(user.id, user.role, JWT_SECRET, expires_in or timedelta(minutes=5))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def customer_auth(session_factory) -> dict[str, str]:
    return await bearer_for(session_factory, CUSTOMER_EMAIL)


@pytest.fixture
async def other_customer_auth(session_factory) -> dict[str, str]:
    async with session_factory() as session:
        session.add(
            User(
                email=OTHER_CUSTOMER_EMAIL,
                name="Sam Other",
                role="customer",
                password_hash=hash_password("irrelevant"),
            )
        )
        await session.commit()
    return await bearer_for(session_factory, OTHER_CUSTOMER_EMAIL)


@pytest.fixture
async def reviewer_auth(session_factory) -> dict[str, str]:
    return await bearer_for(session_factory, REVIEWER_EMAIL)


@pytest.fixture
async def admin_auth(session_factory) -> dict[str, str]:
    return await bearer_for(session_factory, ADMIN_EMAIL)


@pytest.fixture
async def checkpointer(migrated_test_db: str) -> AsyncIterator[AsyncPostgresSaver]:
    async with AsyncPostgresSaver.from_conn_string(plain_url(migrated_test_db)) as saver:
        await saver.setup()
        yield saver


@pytest.fixture
async def serve(checkpointer, session_factory, loaded_kb, customer_auth) -> AsyncIterator[Callable]:
    clients: list[httpx.AsyncClient] = []

    def mount(*steps, then=None, saver=None) -> tuple[httpx.AsyncClient, ScriptedChatModel]:
        model = ScriptedChatModel(steps=list(steps), then=then)
        app.state.session_factory = session_factory
        app.state.graph = build_graph(
            model=model,
            session_factory=session_factory,
            kb=loaded_kb,
            checkpointer=saver or checkpointer,
            max_steps=settings.max_agent_steps,
            min_score=0.3,
        )
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=customer_auth
        )
        clients.append(client)
        return client, model

    yield mount
    app.state.graph = None
    app.state.session_factory = None
    for client in clients:
        await client.aclose()
