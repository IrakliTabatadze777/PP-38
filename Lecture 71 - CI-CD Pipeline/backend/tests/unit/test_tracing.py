import os

import pytest

from app.config.settings import Settings
from app.config.tracing import configure_tracing


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("LANGSMITH_TRACING", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT"):
        monkeypatch.setenv(name, "placeholder")
        monkeypatch.delenv(name)


def settings(**values) -> Settings:
    return Settings(_env_file=None, **values)


def test_tracing_is_off_by_default() -> None:
    assert configure_tracing(settings()) is False
    assert os.environ["LANGSMITH_TRACING"] == "false"


def test_tracing_needs_its_own_key() -> None:
    assert configure_tracing(settings(langsmith_tracing=True)) is False
    assert os.environ["LANGSMITH_TRACING"] == "false"
    assert "LANGSMITH_API_KEY" not in os.environ


def test_tracing_is_exported_to_the_environment_langchain_reads() -> None:
    on = settings(langsmith_tracing=True, langsmith_api_key="key", langsmith_project="demo")

    assert configure_tracing(on) is True

    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_API_KEY"] == "key"
    assert os.environ["LANGSMITH_PROJECT"] == "demo"


def test_the_tests_leave_the_environment_as_they_found_it() -> None:
    assert os.environ.get("LANGSMITH_API_KEY") != "key"
    assert os.environ.get("LANGSMITH_PROJECT") != "demo"
