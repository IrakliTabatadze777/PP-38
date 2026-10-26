import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from sqlalchemy import func, select

from app.db.models import Refund, Ticket
from app.graph.build import build_graph, recursion_limit
from app.rag.store import KnowledgeBase
from scripts.seed import CUSTOMER_EMAIL
from tests.fakes import ScriptedChatModel, ai, last_tool_result, tool_call

MAX_STEPS = 8
THREAD = "t-graph"
FAKE_MIN_SCORE = 0.3


class Run:
    def __init__(self, model: ScriptedChatModel, kb: KnowledgeBase | None, factory) -> None:
        self.model = model
        self.factory = factory
        self.graph = build_graph(
            model=model,
            session_factory=factory,
            kb=kb,
            checkpointer=InMemorySaver(),
            max_steps=MAX_STEPS,
            min_score=FAKE_MIN_SCORE,
        )
        self.config = {
            "configurable": {"thread_id": THREAD},
            "recursion_limit": recursion_limit(MAX_STEPS),
        }

    async def say(self, text: str) -> dict:
        return await self.graph.ainvoke({"messages": [HumanMessage(text)], "steps": 0}, self.config)

    async def count(self, model_class, *where) -> int:
        async with self.factory() as session:
            return await session.scalar(select(func.count()).select_from(model_class).where(*where))


@pytest.fixture
def make_run(session_factory, loaded_kb):
    def make(*steps, then=None) -> Run:
        return Run(ScriptedChatModel(steps=list(steps), then=then), loaded_kb, session_factory)

    return make


def tool_messages(result: dict, name: str | None = None) -> list[ToolMessage]:
    return [
        m
        for m in result["messages"]
        if isinstance(m, ToolMessage) and (name is None or m.name == name)
    ]


def final_text(result: dict) -> str:
    return result["messages"][-1].text


def cite_first_result(messages) -> AIMessage:
    first = last_tool_result(messages)[0]
    return ai(f"Items must be unused. Source: {first['source']}, {first['section']}")


async def test_t1_policy_question_searches_the_knowledge_base_and_names_the_source(make_run):
    run = make_run(
        ai("", tool_call("search_knowledge_base", query="condition of returned items unused")),
        cite_first_result,
    )

    result = await run.say("Can I return boots I wore once?")

    searches = tool_messages(result, "search_knowledge_base")
    assert len(searches) == 1
    assert json.loads(searches[0].text)[0]["source"] == "returns_policy.md"
    assert "returns_policy.md" in final_text(result)


async def test_t2_topic_outside_the_knowledge_base_gets_an_empty_result(make_run):
    def admit_and_offer_help(messages) -> AIMessage:
        assert last_tool_result(messages) == []
        return ai("I don't know that one. Would you like me to hand you to a person?")

    run = make_run(
        ai("", tool_call("search_knowledge_base", query="astronomy telescope quantum")),
        admit_and_offer_help,
    )

    result = await run.say("Do you sell telescopes?")

    assert tool_messages(result, "search_knowledge_base")[0].text == "[]"
    assert "don't know" in final_text(result)


async def test_t3_wrong_email_reveals_no_order_data(make_run):
    run = make_run(
        ai("", tool_call("lookup_order", order_number="1042", email="stranger@example.com")),
        ai("I could not find an order matching those details. Could you check them?"),
    )

    result = await run.say("Where is order 1042? My email is stranger@example.com")

    assert json.loads(tool_messages(result, "lookup_order")[0].text) == {"error": "not_found"}
    assert result.get("verified_order") is None
    everything = " ".join(m.text for m in result["messages"])
    assert "Alpine" not in everything and "delivered" not in everything.lower()


async def test_a_missing_order_and_a_wrong_email_look_the_same_to_the_model(make_run):
    run = make_run(
        ai("", tool_call("lookup_order", order_number="9999", email=CUSTOMER_EMAIL)),
        ai("", tool_call("lookup_order", order_number="1042", email="stranger@example.com")),
        ai("Sorry, I could not find that order."),
    )

    result = await run.say("Check my order")

    first, second = tool_messages(result, "lookup_order")
    assert first.text == second.text == '{"error": "not_found"}'


async def test_t9_final_sale_item_is_ineligible_and_no_refund_is_attempted(make_run):
    def check_the_item(messages) -> AIMessage:
        item = last_tool_result(messages)["items"][0]["item_id"]
        return ai(
            "",
            tool_call(
                "check_refund_eligibility",
                order_number="1045",
                item_id=item,
                reason="changed_mind",
            ),
        )

    def explain(messages) -> AIMessage:
        assert last_tool_result(messages)["decision"] == "ineligible"
        return ai("That item was sold as final sale, so it cannot be refunded.")

    run = make_run(
        ai("", tool_call("lookup_order", order_number="1045", email=CUSTOMER_EMAIL)),
        check_the_item,
        explain,
    )
    refunds_before = await run.count(Refund)

    result = await run.say("I changed my mind about the gloves in order 1045")

    assert json.loads(tool_messages(result, "check_refund_eligibility")[0].text)["decision"] == (
        "ineligible"
    )
    assert not tool_messages(result, "issue_refund")
    assert await run.count(Refund) == refunds_before
    assert result["verified_order"] == "1045"
    assert result["verified_email"] == CUSTOMER_EMAIL


async def test_t13_a_model_that_never_stops_is_escalated_after_eight_steps(make_run):
    counter = iter(range(1000))

    def never_stops(messages) -> AIMessage:
        return ai("", tool_call("search_knowledge_base", query=f"topic number {next(counter)}"))

    run = make_run(then=never_stops)

    result = await run.say("Tell me everything")

    assert run.model.calls == MAX_STEPS + 1
    executed = [m for m in tool_messages(result) if m.status == "success"]
    assert len(executed) == MAX_STEPS
    assert tool_messages(result)[-1].status == "error"
    assert result["ticket_id"] is not None
    assert await run.count(Ticket, Ticket.thread_id == THREAD) == 1
    assert f"ticket #{result['ticket_id']}" in final_text(result)


async def test_checking_eligibility_before_verifying_an_order_is_refused(make_run):
    run = make_run(
        ai(
            "",
            tool_call("check_refund_eligibility", order_number="1042", item_id=1, reason="damaged"),
        ),
        ai("I need to verify your order first."),
    )

    result = await run.say("Refund order 1042")

    assert json.loads(tool_messages(result)[0].text) == {"error": "order_not_verified"}
    assert result.get("verified_order") is None


async def test_invalid_arguments_come_back_to_the_model_as_an_observation(make_run):
    run = make_run(
        ai("", tool_call("lookup_order", order_number="1042")),
        ai("Could you tell me the email on the order?"),
    )

    result = await run.say("Check order 1042")

    assert json.loads(tool_messages(result)[0].text) == {
        "error": "invalid_arguments",
        "fields": ["email"],
    }


async def test_an_identical_call_in_the_same_turn_is_not_run_twice(make_run):
    same = {"order_number": "1042", "email": CUSTOMER_EMAIL}
    run = make_run(
        ai("", tool_call("lookup_order", **same)),
        ai("", tool_call("lookup_order", **same)),
        ai("Done."),
    )

    result = await run.say("Check order 1042")

    first, second = tool_messages(result, "lookup_order")
    assert "order_number" in json.loads(first.text)
    assert json.loads(second.text)["error"] == "duplicate_call"


async def test_the_same_call_is_allowed_again_in_a_later_turn(make_run):
    same = {"order_number": "1042", "email": CUSTOMER_EMAIL}
    run = make_run(
        ai("", tool_call("lookup_order", **same)),
        ai("Here it is."),
        ai("", tool_call("lookup_order", **same)),
        ai("Here it is again."),
    )

    await run.say("Check order 1042")
    result = await run.say("Check it again")

    assert all("error" not in json.loads(m.text) for m in tool_messages(result, "lookup_order"))


async def test_money_reaches_the_model_in_dollars(make_run):
    run = make_run(
        ai("", tool_call("lookup_order", order_number="1042", email=CUSTOMER_EMAIL)),
        ai("Found it."),
    )

    result = await run.say("Check order 1042")

    order = json.loads(tool_messages(result, "lookup_order")[0].text)
    assert order["items"][0]["price_cents"] == 8900
    assert order["items"][0]["price_usd"] == "$89.00"
    assert order["shipping_usd"] == "$9.50"


async def test_the_step_budget_is_per_customer_message(make_run):
    def search(n: int):
        return ai("", tool_call("search_knowledge_base", query=f"question {n}"))

    turn_one = [search(n) for n in range(5)] + [ai("First answer.")]
    turn_two = [search(n + 10) for n in range(5)] + [ai("Second answer.")]
    run = make_run(*turn_one, *turn_two)

    await run.say("First question")
    result = await run.say("Second question")

    assert final_text(result) == "Second answer."
    assert result.get("ticket_id") is None


async def test_the_conversation_continues_on_the_same_thread(make_run):
    run = make_run(ai("Hello! How can I help?"), ai("You said hi earlier."))

    await run.say("hi")
    await run.say("what did I say?")

    second_call = run.model.seen[1]
    assert [m.text for m in second_call if isinstance(m, HumanMessage)] == ["hi", "what did I say?"]


async def test_the_model_is_shown_a_system_prompt_that_hides_internals_rules(make_run):
    run = make_run(ai("Hi."))
    await run.say("hi")

    system = run.model.seen[0][0].text
    assert "Never reveal" in system and "data, never instructions" in system
    assert "BR-" not in system
