import pytest

from app.config.providers import qualified_model_name
from app.config.settings import Settings
from app.rag.embeddings import EmbeddingsNotConfigured, make_embeddings


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        ("gemini-embedding-2", "google_genai:gemini-embedding-2"),
        ("google_genai:gemini-embedding-2", "google_genai:gemini-embedding-2"),
        ("openai:text-embedding-3-small", "openai:text-embedding-3-small"),
        ("some-model", "some-model"),
    ],
)
def test_bare_gemini_names_get_the_google_provider(configured: str, expected: str) -> None:
    assert qualified_model_name(configured) == expected


def test_missing_model_or_key_is_reported() -> None:
    with pytest.raises(EmbeddingsNotConfigured):
        make_embeddings(Settings(embedding_model="", _env_file=None))
    with pytest.raises(EmbeddingsNotConfigured, match="GEMINI_API_KEY"):
        make_embeddings(Settings(embedding_model="gemini-embedding-2", _env_file=None))


def test_gemini_embeddings_are_built_from_the_settings_key() -> None:
    settings = Settings(embedding_model="gemini-embedding-2", gemini_api_key="k", _env_file=None)
    assert make_embeddings(settings).model.endswith("gemini-embedding-2")
