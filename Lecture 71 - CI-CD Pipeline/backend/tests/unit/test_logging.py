import json
import logging

import pytest

from app.logging_config import JsonFormatter, mask_email


@pytest.mark.parametrize(
    ("text", "masked"),
    [
        ("maria@example.com", "m***@e***.com"),
        ("contact maria.k+x@mail.example.org now", "contact m***@m***.org now"),
        ("no email here", "no email here"),
    ],
)
def test_emails_are_masked(text: str, masked: str) -> None:
    assert mask_email(text) == masked


def record(message: str, **extra) -> logging.LogRecord:
    return logging.getLogger("app.test").makeRecord(
        "app.test", logging.INFO, __file__, 1, message, (), None, extra=extra
    )


def test_log_lines_are_json_with_the_ids_and_no_raw_emails() -> None:
    line = JsonFormatter().format(
        record(
            "Chat started for maria@example.com",
            event="chat_started",
            thread_id="t-1",
            note="maria@example.com",
        )
    )

    entry = json.loads(line)

    assert entry["event"] == "chat_started" and entry["thread_id"] == "t-1"
    assert entry["level"] == "INFO" and entry["logger"] == "app.test"
    assert "maria@example.com" not in line
