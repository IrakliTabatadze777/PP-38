import os

os.environ.setdefault('DATABASE_URL', 'postgresql://trip:trip@localhost:5432/trip_test')

import pytest
from .fake_model import FakeModel

from app import agent


@pytest.fixture(autouse=True)
def block_real_model(request, monkeypatch):
    if request.node.get_closest_marker('live'):
        return

    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)

    def refuse():
        raise AssertionError('A test tried to create the real Gemini model. Use the fake_model fixture.')

    monkeypatch.setattr(agent, 'make_model', refuse)


@pytest.fixture
def fake_model(monkeypatch):
    fake = FakeModel()
    monkeypatch.setattr(agent, 'make_model', lambda: fake)
    return fake
