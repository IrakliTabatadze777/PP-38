import asyncio
from types import SimpleNamespace

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from app.agent import build_supervisor_graph
from app.main import new_request_input
from app.schemas import Decision
from app.sessions import apply_decision, describe, is_paused, thread_config

WAITING = SimpleNamespace(next=('finalize_plan',))
IDLE = SimpleNamespace(next=())


def test_thread_config_uses_the_session_id_as_thread_id():
    config = thread_config('session-0001')
    assert config['configurable'] == {'thread_id': 'session-0001'}
    assert config['recursion_limit'] == 20


@pytest.mark.parametrize(('snapshot', 'expected'), [(WAITING, True), (IDLE, False)])
def test_is_paused(snapshot, expected):
    assert is_paused(snapshot) is expected


def test_describe_turns_a_checkpoint_into_a_response():
    snapshot = SimpleNamespace(
        next=('finalize_plan',),
        values={
            'user_request': 'Plan Rome',
            'tool_agent_result': '',
            'plan_agent_result': {'destination': 'Rome'},
            'general_agent_result': '',
            'final_note': '',
        },
    )

    response = describe(snapshot)

    assert response.status == 'awaiting_approval'
    assert response.plan == {'destination': 'Rome'}


def paused_graph(fake_model):
    fake_model.decisions = ['plan_agent', 'finish']
    graph = build_supervisor_graph(InMemorySaver())
    config = thread_config('session-0001')
    graph.invoke(new_request_input('Plan 5 days in Rome'), config)
    return graph, config


def test_approve_leaves_the_plan_alone(fake_model):
    graph, config = paused_graph(fake_model)

    asyncio.run(apply_decision(graph, config, Decision(session_id='session-0001', action='approve')))

    assert graph.get_state(config).values['plan_agent_result']['daily_budget_usd'] == 150.0


def test_edit_writes_the_new_budget_into_the_saved_plan(fake_model):
    graph, config = paused_graph(fake_model)

    decision = Decision(session_id='session-0001', action='edit', daily_budget_usd=80)
    asyncio.run(apply_decision(graph, config, decision))

    assert graph.get_state(config).values['plan_agent_result']['daily_budget_usd'] == 80.0
