from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str
    debug: bool

    DATABASE_URL: str

    secret: str
    ACCESS_TOKEN_LIFETIME_MINUTES: int
    REFRESH_TOKEN_LIFETIME_DAYS: int
    algorithm: str

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()