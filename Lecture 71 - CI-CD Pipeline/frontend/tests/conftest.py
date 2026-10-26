import sys
from pathlib import Path

import httpx
import pytest

FRONTEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FRONTEND_DIR))


@pytest.fixture(autouse=True)
def no_real_network(monkeypatch: pytest.MonkeyPatch) -> None:

    def refuse(*args: object, **kwargs: object) -> None:
        raise httpx.ConnectError("tests must not use the network")

    for name in ("request", "stream", "get"):
        monkeypatch.setattr(httpx, name, refuse)
