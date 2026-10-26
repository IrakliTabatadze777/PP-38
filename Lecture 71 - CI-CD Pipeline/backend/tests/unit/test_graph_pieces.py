import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.graph.approvals import approval_flags, approval_id_for, policy_sources_in
from app.graph.nodes import call_key, calls_made_this_turn, summarize_for_ticket
from app.graph.routing import route_after_agent
from app.graph.tools import SENSITIVE_TOOL_NAMES, bindable_tools, observation, with_usd
from tests.fakes import ai, tool_call


def state(*messages, steps: int = 1) -> dict:
    return {"messages": list(messages), "steps": steps}


class TestRouting:
    def test_a_reply_without_tool_calls_ends_the_run(self) -> None:
        assert route_after_agent(state(HumanMessage("hi"), ai("hello")), max_steps=8) == "end"

    def test_tool_calls_go_to_the_tools(self) -> None:
        reply = ai("", tool_call("lookup_order", order_number="1", email="a@b.c"))
        assert route_after_agent(state(HumanMessage("hi"), reply), max_steps=8) == "tools"

    def test_the_eighth_round_trip_still_runs_the_ninth_call_escalates(self) -> None:
        reply = ai("", tool_call("search_knowledge_base", query="x"))
        messages = (HumanMessage("hi"), reply)
        assert route_after_agent(state(*messages, steps=8), max_steps=8) == "tools"
        assert route_after_agent(state(*messages, steps=9), max_steps=8) == "limit_escalation"

    def test_a_final_answer_past_the_limit_still_ends_normally(self) -> None:
        assert (
            route_after_agent(state(HumanMessage("hi"), ai("done"), steps=9), max_steps=8) == "end"
        )


class TestMoneyForTheModel:
    def test_usd_text_is_added_next_to_every_cents_field(self) -> None:
        result = with_usd({"items": [{"price_cents": 8900}], "total_cents": 9850, "n": 3})
        assert result == {
            "items": [{"price_cents": 8900, "price_usd": "$89.00"}],
            "total_cents": 9850,
            "total_usd": "$98.50",
            "n": 3,
        }

    def test_observation_is_json_with_dollars(self) -> None:
        assert json.loads(observation({"max_refund_cents": 12345}))["max_refund_usd"] == "$123.45"

    def test_other_values_pass_through(self) -> None:
        assert with_usd([{"source": "a.md", "score": 0.8}]) == [{"source": "a.md", "score": 0.8}]


class TestDuplicateCalls:
    def test_calls_since_the_last_customer_message_count(self) -> None:
        call = tool_call("lookup_order", order_number="1", email="a@b.c")
        messages = [
            HumanMessage("first"),
            ai("", call),
            ToolMessage("{}", tool_call_id=call["id"]),
        ]
        assert calls_made_this_turn(messages) == {call_key("lookup_order", call["args"])}

    def test_a_new_customer_message_starts_a_new_turn(self) -> None:
        call = tool_call("lookup_order", order_number="1", email="a@b.c")
        messages = [HumanMessage("first"), ai("", call), HumanMessage("second")]
        assert calls_made_this_turn(messages) == set()

    def test_argument_order_does_not_matter(self) -> None:
        assert call_key("t", {"a": 1, "b": 2}) == call_key("t", {"b": 2, "a": 1})


def test_ticket_summary_uses_recent_customer_messages_only() -> None:
    messages = [HumanMessage(f"message {i}") for i in range(5)]
    messages.insert(2, AIMessage("assistant text"))
    summary = summarize_for_ticket(messages)
    assert "message 4" in summary and "message 2" in summary
    assert "message 1" not in summary and "assistant text" not in summary


def test_the_model_sees_all_six_tools() -> None:
    names = {tool.name for tool in bindable_tools()}
    assert names == {
        "search_knowledge_base",
        "lookup_order",
        "check_refund_eligibility",
        "issue_refund",
        "issue_replacement",
        "escalate_to_human",
    }
    assert SENSITIVE_TOOL_NAMES == {"issue_refund", "issue_replacement"}


@pytest.mark.parametrize("tool", bindable_tools(), ids=lambda t: t.name)
def test_tool_schemas_do_not_expose_graph_controlled_arguments(tool) -> None:
    properties = set(tool.args_schema.model_json_schema()["properties"])
    assert properties.isdisjoint({"verified_order", "thread_id", "tool_call_id"})


class TestPolicySources:
    def search_result(self, *sources: str) -> ToolMessage:
        passages = [{"source": s, "section": "x", "text": "t", "score": 0.9} for s in sources]
        return ToolMessage(json.dumps(passages), tool_call_id="c", name="search_knowledge_base")

    def test_sources_are_collected_across_the_conversation_without_repeats(self) -> None:
        messages = [
            HumanMessage("first"),
            self.search_result("refund_policy.md", "returns_policy.md"),
            HumanMessage("second"),
            self.search_result("refund_policy.md", "warranty.md"),
        ]
        assert policy_sources_in(messages) == [
            "refund_policy.md",
            "returns_policy.md",
            "warranty.md",
        ]

    def test_other_tool_results_and_empty_searches_are_ignored(self) -> None:
        messages = [
            ToolMessage("[]", tool_call_id="a", name="search_knowledge_base"),
            ToolMessage('{"source": "x.md"}', tool_call_id="b", name="lookup_order"),
            ToolMessage("not json", tool_call_id="c", name="search_knowledge_base"),
        ]
        assert policy_sources_in(messages) == []


class TestApprovalFlags:
    def test_a_refund_over_200_dollars_is_high_value(self) -> None:
        assert approval_flags(tool="issue_refund", amount_cents=20_001, decision="eligible") == [
            "high_value"
        ]

    def test_exactly_200_dollars_is_not_high_value(self) -> None:
        assert approval_flags(tool="issue_refund", amount_cents=20_000, decision="eligible") == []

    def test_a_grace_period_refund_is_an_exception(self) -> None:
        flags = approval_flags(
            tool="issue_refund", amount_cents=14_000, decision="needs_human_judgment"
        )
        assert flags == ["exception"]

    def test_both_flags_can_apply(self) -> None:
        flags = approval_flags(
            tool="issue_refund", amount_cents=28_900, decision="needs_human_judgment"
        )
        assert flags == ["high_value", "exception"]

    def test_the_approval_id_is_stable_for_the_same_call(self) -> None:
        assert approval_id_for("t-1", "call_a") == approval_id_for("t-1", "call_a")
        assert approval_id_for("t-1", "call_a") != approval_id_for("t-1", "call_b")
        assert approval_id_for("t-1", "call_a") != approval_id_for("t-2", "call_a")
