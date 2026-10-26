from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(REPO_ROOT / ".env", ".env"), extra="ignore")

    llm_model: str = ""
    embedding_model: str = ""
    gemini_api_key: str = ""

    database_url: str = ""
    checkpoint_db_url: str = ""

    retrieval_min_score: float = Field(default=0.69, ge=0, le=1)

    jwt_secret: str = ""
    jwt_access_expire_minutes: int = Field(default=15, ge=1)
    jwt_refresh_expire_days: int = Field(default=7, ge=1)
    max_agent_steps: int = Field(default=8, ge=1)
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "customer-support-agent"


settings = Settings()
