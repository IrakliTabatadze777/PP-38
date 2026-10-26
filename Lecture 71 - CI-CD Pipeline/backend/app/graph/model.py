from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from app.config.providers import is_gemini, qualified_model_name
from app.config.settings import Settings, settings

MODEL_RETRIES = 2


class ModelNotConfigured(RuntimeError): ...


def make_chat_model(settings: Settings = settings) -> BaseChatModel:
    if not settings.llm_model:
        raise ModelNotConfigured("LLM_MODEL is not set")
    model = qualified_model_name(settings.llm_model)
    kwargs: dict[str, object] = {"max_retries": MODEL_RETRIES}
    if is_gemini(model):
        if not settings.gemini_api_key:
            raise ModelNotConfigured("GEMINI_API_KEY is not set")
        kwargs["api_key"] = settings.gemini_api_key
    return init_chat_model(model, **kwargs)
