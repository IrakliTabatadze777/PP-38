import json

import pytest
from .fake_model import tool_call
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from app import main
from app.agent import build_supervisor_graph
from app.main import app, get_graph

SESSION = 'session-0001'


@pytest.fixture
def client(fake_model):
    graph = build_supervisor_graph(InMemorySaver())
    app.dependency_overrides[get_graph] = lambda: graph
    yield TestClient(app)
    app.dependency_overrides.clear()


def chat(client, message):
    return client.post('/chat/stream', json={'session_id': SESSION, 'message': message})


def approve(client, **fields):
    return client.post('/approve/stream', json={'session_id': SESSION, **fields})


def events(response) -> list[dict]:
    blocks = response.text.split('\n\n')
    return [json.loads(block[len('data: ') :]) for block in blocks if block.startswith('data: ')]


def test_weather_question_streams_steps_then_a_final_answer(client, fake_model):
    fake_model.decisions = ['tool_agent', 'finish']
    fake_model.tool_replies = [tool_call('get_weather', city='Tbilisi'), AIMessage(content='Sunny, 25C in Tbilisi.')]

    response = chat(client, 'What is the weather in Tbilisi?')

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/event-stream')
    sent = events(response)
    assert [e['node'] for e in sent if e['type'] == 'step'] == ['supervisor', 'tool_agent', 'supervisor']
    assert sent[-1]['type'] == 'final'
    assert sent[-1]['status'] == 'completed'
    assert sent[-1]['tool_result'] == 'Sunny, 25C in Tbilisi.'


def test_every_event_ends_with_a_blank_line(client, fake_model):
    fake_model.decisions = ['general_agent', 'finish']

    response = chat(client, 'Hello there')

    assert response.text.endswith('\n\n')
    assert response.text.count('\n\n') == len(events(response))


@pytest.mark.parametrize(
    'body',
    [
        {'session_id': SESSION},
        {'message': 'no session id'},
    ],
)
def test_incomplete_chat_body_is_422(client, body):
    assert client.post('/chat/stream', json=body).status_code == 422


def test_unknown_action_is_422(client):
    assert approve(client, action='delete').status_code == 422


def test_plan_flow_with_approval(client, fake_model):
    fake_model.decisions = ['plan_agent', 'finish']

    first = events(chat(client, 'Plan 5 days in Rome with a budget'))[-1]
    assert first['status'] == 'awaiting_approval'
    assert first['plan']['destination'] == 'Rome'

    last = events(approve(client, action='approve'))[-1]
    assert last['status'] == 'completed'
    assert last['final_note'] == 'Plan Finalized'


def test_edit_replaces_the_budget_with_the_humans_number(client, fake_model):
    fake_model.decisions = ['plan_agent', 'finish']
    chat(client, 'Plan 5 days in Rome with a budget')

    last = events(approve(client, action='edit', daily_budget_usd=80))[-1]

    assert last['status'] == 'completed'
    assert last['plan']['daily_budget_usd'] == 80.0


def test_a_run_that_hits_the_step_limit_ends_with_an_error_event(client, fake_model, monkeypatch):
    fake_model.decisions = ['general_agent', 'finish']
    monkeypatch.setattr(
        main, 'thread_config', lambda session_id: {'configurable': {'thread_id': session_id}, 'recursion_limit': 1}
    )

    sent = events(chat(client, 'Hello there'))

    assert sent[-1] == {'type': 'error', 'detail': 'The agent could not finish within limit'}
