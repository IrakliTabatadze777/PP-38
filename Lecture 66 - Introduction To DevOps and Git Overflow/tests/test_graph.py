import uuid

import pytest
from .fake_model import tool_call
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.agent import build_supervisor_graph
from app.main import new_request_input


def new_config() -> dict:
    return {'configurable': {'thread_id': str(uuid.uuid4())}, 'recursion_limit': 20}


@pytest.fixture
def graph(fake_model):
    return build_supervisor_graph(InMemorySaver())


def ask(graph, question, config):
    return graph.invoke(new_request_input(question), config)


def test_general_question(graph, fake_model):
    fake_model.decisions = ['general_agent', 'finish']
    fake_model.text = 'I am a trip assistant.'

    result = ask(graph, 'What is your name?', new_config())

    assert result['completed_agents'] == ['general_agent']
    assert result['general_agent_result'] == 'I am a trip assistant.'


def test_weather_question_runs_the_real_tool(graph, fake_model):
    fake_model.decisions = ['tool_agent', 'finish']
    fake_model.tool_replies = [tool_call('get_weather', city='Tbilisi'), AIMessage(content='Sunny, 25C in Tbilisi.')]

    result = ask(graph, 'What is the weather in Tbilisi?', new_config())

    assert result['completed_agents'] == ['tool_agent']
    assert result['tool_agent_result'] == 'Sunny, 25C in Tbilisi.'
    messages_sent_back = fake_model.tool_inputs[-1]
    assert [m.content for m in messages_sent_back if m.type == 'tool'] == ['Sunny, 25C']


def test_plan_pauses_for_approval_then_finishes(graph, fake_model):
    fake_model.decisions = ['plan_agent', 'finish']
    config = new_config()

    ask(graph, 'Plan 5 days in Rome with a budget', config)

    paused = graph.get_state(config)
    assert paused.next == ('finalize_plan',)
    assert paused.values['plan_agent_result']['destination'] == 'Rome'
    assert paused.values['final_note'] == ''

    graph.invoke(None, config)

    done = graph.get_state(config)
    assert done.next == ()
    assert done.values['final_note'] == 'Plan Finalized'


def test_the_plan_agent_gets_the_users_request(graph, fake_model):
    fake_model.decisions = ['plan_agent', 'finish']

    ask(graph, 'Plan 5 days in Rome with a budget', new_config())

    plan_prompts = [p for p in fake_model.prompts if 'Produce a trip plan' in p]
    assert 'Plan 5 days in Rome with a budget' in plan_prompts[0]


def test_supervisor_does_not_call_the_same_agent_twice(graph, fake_model):
    fake_model.decisions = ['general_agent', 'general_agent']

    result = ask(graph, 'Hello', new_config())

    assert result['completed_agents'] == ['general_agent']
    assert fake_model.prompts.count('Hello') == 1


def test_without_the_fake_the_graph_cannot_reach_gemini():
    graph = build_supervisor_graph(InMemorySaver())
    with pytest.raises(AssertionError, match='real Gemini model'):
        ask(graph, 'Hello', new_config())
