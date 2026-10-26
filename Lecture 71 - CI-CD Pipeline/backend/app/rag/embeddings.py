from langchain.embeddings import init_embeddings
from langchain_core.embeddings import Embeddings

from app.config.providers import is_gemini, qualified_model_name
from app.config.settings import Settings, settings


class EmbeddingsNotConfigured(RuntimeError): ...


def make_embeddings(settings: Settings = settings) -> Embeddings:
    model = qualified_model_name(settings.embedding_model)
    if ":" not in model:
        raise EmbeddingsNotConfigured(
            'EMBEDDING_MODEL must be "provider:model", e.g. "google_genai:gemini-embedding-2"'
        )
    kwargs = {}
    if is_gemini(model):
        if not settings.gemini_api_key:
            raise EmbeddingsNotConfigured("GEMINI_API_KEY is not set")
        kwargs["api_key"] = settings.gemini_api_key
    return init_embeddings(model, **kwargs)
