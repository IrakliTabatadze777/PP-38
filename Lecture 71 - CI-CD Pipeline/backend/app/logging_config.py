import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

_EMAIL = re.compile(
    r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9-])[A-Za-z0-9.-]*(\.[A-Za-z]+)"
)
_RESERVED = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


def mask_email(text: str) -> str:
    return _EMAIL.sub(r"\1***@\2***\3", text)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_email(record.getMessage()),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED:
                entry[key] = mask_email(value) if isinstance(value, str) else value
        if record.exc_info:
            entry["exception"] = mask_email(self.formatException(record.exc_info))
        return json.dumps(entry, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    app_logger = logging.getLogger("app")
    app_logger.handlers = [handler]
    app_logger.setLevel(level)
    app_logger.propagate = False
