import os
import uuid

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from app.agent import build_supervisor_graph
from app.main import new_request_input

pytestmark = pytest.mark.live


@pytest.fixture(autouse=True)
def need_a_key():
    if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'):
        return
    if os.getenv('CI'):
        pytest.fail('No Gemini key in the environment. Add the GEMINI_API_KEY secret to the repository.')
    pytest.skip('No Gemini key. Set GEMINI_API_KEY to run the live tests.')


def ask(question: str) -> dict:
    graph = build_supervisor_graph(InMemorySaver())
    config = {'configurable': {'thread_id': str(uuid.uuid4())}, 'recursion_limit': 20}
    return graph.invoke(new_request_input(question), config)


def test_weather_question_goes_to_the_tool_agent():
    result = ask('What is the weather in Tbilisi?')

    assert 'tool_agent' in result['completed_agents']
    assert '25' in result['tool_agent_result']


def test_general_question_needs_no_tools():
    result = ask('What is the capital of France?')

    assert 'general_agent' in result['completed_agents']
    assert 'tool_agent' not in result['completed_agents']
