import json
import logging
import uuid

import httpx
import pytest
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import func, select

from app.db.models import Ticket
from app.logging_config import JsonFormatter
from app.main import app
from scripts.seed import CUSTOMER_EMAIL
from tests.fakes import ai, tool_call
from tests.helpers import chat, plain_url

SECRETS = ["lookup_order", "search_knowledge_base", "check_refund_eligibility", CUSTOMER_EMAIL]


async def test_a_new_conversation_streams_thread_tokens_and_done(serve):
    client, _ = serve(ai("Hello! How can I help?"))

    response, events = await chat(client, "hi")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    kinds = [kind for kind, _ in events]
    assert kinds[0] == "thread" and kinds[-1] == "done"
    assert events[0][1]["thread_id"].startswith("t-")
    assert "".join(d["text"] for k, d in events if k == "token") == "Hello! How can I help?"


async def test_tool_activity_is_shown_without_tool_names_or_arguments(serve):
    client, _ = serve(
        ai("", tool_call("lookup_order", order_number="1042", email=CUSTOMER_EMAIL)),
        ai("I found your order."),
    )

    response, events = await chat(client, "Where is order 1042?")

    assert [d for k, d in events if k == "tool_call"] == [{"name": "Checking your order"}]
    for secret in SECRETS:
        assert secret not in response.text


async def test_the_conversation_continues_across_requests_with_the_same_thread_id(serve):
    client, model = serve(ai("Hello!"), ai("You said hi."))

    _, first = await chat(client, "hi")
    thread_id = first[0][1]["thread_id"]
    _, second = await chat(client, "what did I say?", thread_id)

    assert second[0] == ("thread", {"thread_id": thread_id})
    seen = [m.text for m in model.seen[1]]
    assert "hi" in seen and "Hello!" in seen and "what did I say?" in seen

    history = (await client.get(f"/threads/{thread_id}")).json()
    assert history == {
        "thread_id": thread_id,
        "status": "idle",
        "messages": [
            {"role": "customer", "content": "hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "customer", "content": "what did I say?"},
            {"role": "assistant", "content": "You said hi."},
        ],
    }


async def test_the_history_hides_tool_traffic(serve):
    client, _ = serve(
        ai("", tool_call("lookup_order", order_number="1042", email=CUSTOMER_EMAIL)),
        ai("I found your order."),
    )
    _, events = await chat(client, "Where is order 1042?")

    history = (await client.get(f"/threads/{events[0][1]['thread_id']}")).json()

    assert [m["role"] for m in history["messages"]] == ["customer", "assistant"]
    for secret in ["lookup_order", "Alpine"]:
        assert secret not in json.dumps(history)


async def test_a_new_app_instance_on_the_same_database_continues_the_thread(
    serve, migrated_test_db
):
    client, _ = serve(ai("Hello!"))
    _, events = await chat(client, "hi")
    thread_id = events[0][1]["thread_id"]

    async with AsyncPostgresSaver.from_conn_string(plain_url(migrated_test_db)) as other_saver:
        second_client, second_model = serve(ai("Welcome back."), saver=other_saver)
        await chat(second_client, "I am back", thread_id)

    assert "Hello!" in [m.text for m in second_model.seen[0]]


async def test_a_runaway_model_ends_with_the_handoff_message_and_a_ticket(serve, session_factory):
    counter = iter(range(1000))
    client, _ = serve(
        then=lambda _: ai("", tool_call("search_knowledge_base", query=f"topic {next(counter)}"))
    )

    response, events = await chat(client, "Tell me everything")

    text = "".join(d["text"] for k, d in events if k == "token")
    assert "ticket #" in text
    assert events[-1][0] == "done"
    async with session_factory() as session:
        thread_id = events[0][1]["thread_id"]
        assert (
            await session.scalar(
                select(func.count()).select_from(Ticket).where(Ticket.thread_id == thread_id)
            )
            == 1
        )
    for secret in SECRETS:
        assert secret not in response.text


async def test_a_failing_model_gives_a_generic_error_event(serve):
    def explode(_):
        raise RuntimeError("secret internal detail: postgres://user:pw@host")

    client, _ = serve(explode)

    response, events = await chat(client, "hi")

    assert events[-1] == (
        "error",
        {"code": "internal_error", "message": "Something went wrong. Please try again."},
    )
    assert "done" not in [kind for kind, _ in events]
    assert "secret" not in response.text and "Traceback" not in response.text


async def test_an_unknown_thread_is_a_404(serve):
    client, _ = serve()

    response, _ = await chat(client, "hi", f"t-{uuid.uuid4().hex}")
    assert response.status_code == 404
    assert response.json()["code"] == "thread_not_found"

    history = await client.get("/threads/t-nope")
    assert history.status_code == 404
    assert history.json()["code"] == "thread_not_found"


@pytest.mark.parametrize(
    "body",
    [
        {"message": ""},
        {"message": "   "},
        {"message": "x" * 2001},
        {"message": "hi", "thread_id": "../etc/passwd"},
        {},
    ],
)
async def test_invalid_chat_requests_are_rejected(serve, body):
    client, _ = serve()
    assert (await client.post("/chat", json=body)).status_code == 422


async def test_chat_is_unavailable_when_no_agent_is_configured(session_factory, customer_auth):
    app.state.graph = None
    app.state.session_factory = session_factory
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", headers=customer_auth
    ) as client:
        response = await client.post("/chat", json={"message": "hi"})
    app.state.session_factory = None
    assert response.status_code == 503
    assert response.json()["code"] == "agent_unavailable"


async def test_unexpected_errors_become_a_generic_500(serve, monkeypatch, customer_auth):
    client, _ = serve(ai("Hello!"))
    _, events = await chat(client, "hi")
    thread_id = events[0][1]["thread_id"]
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    async def explode(*_, **__):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(type(app.state.graph), "aget_state", explode)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", headers=customer_auth
    ) as quiet:
        response = await quiet.get(f"/threads/{thread_id}")

    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error",
        "message": "Something went wrong. Please try again.",
    }
    assert "secret" not in response.text


async def test_logs_carry_the_thread_and_tool_but_no_emails_or_arguments(serve):
    lines: list[str] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            lines.append(JsonFormatter().format(record))

    handler = Capture()
    logging.getLogger("app").addHandler(handler)
    try:
        client, _ = serve(
            ai("", tool_call("lookup_order", order_number="1042", email=CUSTOMER_EMAIL)),
            ai("I found your order."),
        )
        _, events = await chat(client, "Where is order 1042?")
    finally:
        logging.getLogger("app").removeHandler(handler)

    thread_id = events[0][1]["thread_id"]
    entries = [json.loads(line) for line in lines]
    runs = [e for e in entries if e.get("event") == "tool_run"]
    assert runs and runs[0]["thread_id"] == thread_id and runs[0]["tool"] == "lookup_order"
    assert {"chat_started", "chat_finished"} <= {e.get("event") for e in entries}
    joined = "\n".join(lines)
    assert CUSTOMER_EMAIL not in joined and "1042" not in joined
