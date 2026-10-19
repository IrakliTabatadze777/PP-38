import json
import os
import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.postgres


@pytest.fixture(scope='module')
def database_url():
    url = os.environ['DATABASE_URL']
    try:
        psycopg.connect(url, connect_timeout=3).close()
    except psycopg.OperationalError:
        if os.getenv('CI'):
            raise
        pytest.skip('PostgreSQL is not running. Start one and set DATABASE_URL, or let CI run this test.')
    return url


def final_event(response) -> dict:
    blocks = [b for b in response.text.split('\n\n') if b.startswith('data: ')]
    return json.loads(blocks[-1][len('data: ') :])


def chat(client, session_id, message):
    return client.post('/chat/stream', json={'session_id': session_id, 'message': message})


def approve(client, session_id, **fields):
    return client.post('/approve/stream', json={'session_id': session_id, **fields})


def test_app_starts_on_an_empty_database_and_can_start_again(database_url):
    for _ in range(2):
        with TestClient(app):
            pass


def test_a_paused_plan_survives_a_restart(database_url, fake_model):
    fake_model.decisions = ['plan_agent', 'finish']
    session_id = f'test-{uuid.uuid4()}'

    with TestClient(app) as first_server:
        paused = final_event(chat(first_server, session_id, 'Plan 5 days in Rome'))
        assert paused['status'] == 'awaiting_approval'

    with TestClient(app) as second_server:
        finished = final_event(approve(second_server, session_id, action='approve'))

    assert finished['status'] == 'completed'
    assert finished['user_request'] == 'Plan 5 days in Rome'
    assert finished['plan']['destination'] == 'Rome'
    assert finished['final_note'] == 'Plan Finalized'


def test_an_edit_is_saved_in_the_database(database_url, fake_model):
    fake_model.decisions = ['plan_agent', 'finish']
    session_id = f'test-{uuid.uuid4()}'

    with TestClient(app) as first_server:
        chat(first_server, session_id, 'Plan 5 days in Rome')

    with TestClient(app) as second_server:
        finished = final_event(approve(second_server, session_id, action='edit', daily_budget_usd=80))

    assert finished['plan']['daily_budget_usd'] == 80.0
