from app.services.chat import TITLE_LENGTH, conversation_title
from scripts.seed import CUSTOMER_EMAIL
from tests.fakes import ai, tool_call
from tests.helpers import chat


def lookup(email: str = CUSTOMER_EMAIL):
    return ai("", tool_call("lookup_order", order_number="1042", email=email))


async def listed(client, headers=None) -> list[dict]:
    response = await client.get("/threads", **({"headers": headers} if headers else {}))
    assert response.status_code == 200
    return response.json()


async def test_a_conversation_is_listed_for_the_signed_in_customer(serve):
    client, _ = serve(ai("Hello!"))
    _, events = await chat(client, "Where is order 1042?")
    thread_id = events[0][1]["thread_id"]

    threads = await listed(client)

    assert [(t["thread_id"], t["title"]) for t in threads] == [(thread_id, "Where is order 1042?")]
    assert threads[0]["updated_at"]


async def test_another_customer_sees_and_reaches_nothing(serve, other_customer_auth):
    client, _ = serve(ai("Hello!"))
    _, events = await chat(client, "private question")
    thread_id = events[0][1]["thread_id"]

    assert await listed(client, other_customer_auth) == []
    history = await client.get(f"/threads/{thread_id}", headers=other_customer_auth)
    assert history.status_code == 404 and history.json()["code"] == "thread_not_found"
    resumed = await client.post(
        "/chat", json={"message": "hi", "thread_id": thread_id}, headers=other_customer_auth
    )
    assert resumed.status_code == 404 and resumed.json()["code"] == "thread_not_found"
    assert "private question" not in history.text + resumed.text
    assert len(await listed(client)) == 1


async def test_a_conversation_without_an_owner_is_unreachable(serve, session_factory):
    from app.db.models import Conversation

    client, _ = serve(ai("Hello!"))
    _, events = await chat(client, "hi")
    thread_id = events[0][1]["thread_id"]
    async with session_factory() as session:
        row = await session.get(Conversation, thread_id)
        row.customer_email = None
        await session.commit()

    assert await listed(client) == []
    assert (await client.get(f"/threads/{thread_id}")).status_code == 404


async def test_a_verified_email_does_not_move_the_conversation(serve, other_customer_auth):
    client, _ = serve(lookup("stranger@example.com"), ai("I could not find that order."))
    _, events = await chat(client, "Where is order 1042?")

    assert [t["thread_id"] for t in await listed(client)] == [events[0][1]["thread_id"]]
    assert await listed(client, other_customer_auth) == []


async def test_the_most_recently_used_conversation_comes_first(serve):
    client, _ = serve(ai("One."), ai("Two."), ai("Three."))
    _, first = await chat(client, "first question")
    _, second = await chat(client, "second question")
    first_id, second_id = first[0][1]["thread_id"], second[0][1]["thread_id"]
    assert [t["thread_id"] for t in await listed(client)] == [second_id, first_id]

    await chat(client, "one more thing", first_id)

    assert [t["thread_id"] for t in await listed(client)] == [first_id, second_id]


def test_titles_are_one_line_and_cut_to_the_title_length():
    assert conversation_title("  Where is\n my   order? ") == "Where is my order?"
    title = conversation_title("word " * 40)
    assert len(title) == TITLE_LENGTH and title.endswith("…")
