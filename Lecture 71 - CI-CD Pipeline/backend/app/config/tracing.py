import logging
import os

from app.config.settings import Settings

logger = logging.getLogger(__name__)


def configure_tracing(settings: Settings) -> bool:
    if not settings.langsmith_tracing:
        os.environ["LANGSMITH_TRACING"] = "false"
        return False
    if not settings.langsmith_api_key:
        logger.warning("LANGSMITH_TRACING is on but LANGSMITH_API_KEY is not set: tracing is off")
        os.environ["LANGSMITH_TRACING"] = "false"
        return False
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    return True
