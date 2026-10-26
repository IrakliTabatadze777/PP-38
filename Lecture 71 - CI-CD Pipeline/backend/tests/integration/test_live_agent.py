import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from sqlalchemy import func, select

from app.config.settings import settings
from app.db.models import Order, OrderItem, Refund, Ticket
from app.graph.build import build_graph, recursion_limit
from app.graph.model import ModelNotConfigured, make_chat_model
from app.main import app
from app.rag.embeddings import EmbeddingsNotConfigured, make_embeddings
from app.rag.ingest import ingest_directory
from app.rag.store import KnowledgeBase
from scripts.seed import CUSTOMER_EMAIL
from tests.conftest import KB_DIR
from tests.helpers import chat

pytestmark = pytest.mark.live


@pytest.fixture
async def live_ask(migrated_test_db: str, session_factory) -> AsyncIterator:
    try:
        model = make_chat_model(settings)
        embeddings = make_embeddings(settings)
    except (ModelNotConfigured, EmbeddingsNotConfigured) as exc:
        pytest.skip(str(exc))
    kb = KnowledgeBase(embeddings, migrated_test_db, collection=f"kb_live_{uuid.uuid4().hex[:8]}")
    await ingest_directory(kb, KB_DIR)
    graph = build_graph(
        model=model,
        session_factory=session_factory,
        kb=kb,
        checkpointer=InMemorySaver(),
        max_steps=settings.max_agent_steps,
    )
    thread = {
        "configurable": {"thread_id": "t-live"},
        "recursion_limit": recursion_limit(settings.max_agent_steps),
    }

    async def ask(text: str) -> dict:
        return await graph.ainvoke({"messages": [HumanMessage(text)], "steps": 0}, thread)

    yield ask
    await kb.drop()
    await kb.aclose()


def tool_names(result: dict) -> list[str]:
    return [m.name for m in result["messages"] if isinstance(m, ToolMessage)]


async def test_t1_policy_question_is_answered_from_the_documents(live_ask):
    result = await live_ask("Can I return boots I wore once?")

    assert "search_knowledge_base" in tool_names(result)
    assert "returns_policy.md" in result["messages"][-1].text


async def test_t2_a_topic_outside_the_documents_is_admitted_and_escalation_offered(live_ask):
    result = await live_ask("Do you sell gift cards?")
    reply = result["messages"][-1].text.lower()

    admits = ("don't know", "do not know", "not sure", "don't have", "do not have", "unable")
    admits += ("couldn't find", "could not find", "no information", "not able", "can't")
    offers = ("human", "team", "person", "agent", "colleague", "representative", "staff")
    assert any(phrase in reply for phrase in admits), reply
    assert any(phrase in reply for phrase in offers), reply


async def test_t3_a_wrong_email_reveals_nothing(live_ask):
    result = await live_ask("Where is order 1042? My email is someone.else@example.com")
    reply = result["messages"][-1].text

    assert "Alpine" not in reply and "delivered" not in reply.lower()
    assert result.get("verified_order") is None


async def test_a_customer_who_asks_for_a_person_gets_a_ticket(live_ask, session_factory):
    result = await live_ask("I want to talk to a real person.")

    assert "escalate_to_human" in tool_names(result)
    assert result.get("ticket_id") is not None
    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(Ticket))
    assert count == 1


async def test_a_customer_can_check_an_order(live_ask):
    result = await live_ask(f"Where is order 1042? The email on it is {CUSTOMER_EMAIL}")

    assert result["verified_order"] == "1042"
    assert "Alpine" in result["messages"][-1].text


@pytest.fixture
async def live_api(checkpointer, session_factory, migrated_test_db, customer_auth):
    try:
        model = make_chat_model(settings)
        embeddings = make_embeddings(settings)
    except (ModelNotConfigured, EmbeddingsNotConfigured) as exc:
        pytest.skip(str(exc))
    kb = KnowledgeBase(embeddings, migrated_test_db, collection=f"kb_live_{uuid.uuid4().hex[:8]}")
    await ingest_directory(kb, KB_DIR)
    app.state.session_factory = session_factory
    app.state.graph = build_graph(
        model=model,
        session_factory=session_factory,
        kb=kb,
        checkpointer=checkpointer,
        max_steps=settings.max_agent_steps,
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        timeout=120,
        headers=customer_auth,
    ) as client:
        yield client
    app.state.graph = None
    app.state.session_factory = None
    await kb.drop()
    await kb.aclose()


async def test_reference_scenario_a_damaged_jacket_refund_with_approval(
    live_api, session_factory, reviewer_auth
):
    messages = [
        "Order 1042 arrived with a broken zipper and I want my money back.",
        f"The email on the order is {CUSTOMER_EMAIL}",
        "Yes, please go ahead and submit the refund request.",
        "Yes, I confirm. Please submit it now.",
    ]
    thread_id = None
    for text in messages:
        _, events = await chat(live_api, text, thread_id)
        thread_id = events[0][1]["thread_id"]
        if events[-1][0] == "awaiting_approval":
            break
    else:
        pytest.fail("The agent never asked for a refund")

    approval_id = events[-1][1]["approval_id"]
    async with session_factory() as session:
        assert (
            await session.scalar(
                select(func.count())
                .select_from(Refund)
                .join(OrderItem)
                .join(Order)
                .where(Order.order_number == "1042")
            )
            == 0
        )

    detail = (await live_api.get(f"/approvals/{approval_id}", headers=reviewer_auth)).json()
    assert detail["args"]["order_number"] == "1042" and detail["max_allowed_cents"] == 9850

    done = await live_api.post(
        f"/approvals/{approval_id}/decision",
        headers=reviewer_auth,
        json={"decision": "approve"},
    )

    assert done.status_code == 200
    reply = done.json()["agent_reply"]
    assert "5" in reply and "7" in reply
    async with session_factory() as session:
        refund = await session.scalar(
            select(Refund).join(OrderItem).join(Order).where(Order.order_number == "1042")
        )
    assert refund is not None and refund.amount_cents <= 9850
