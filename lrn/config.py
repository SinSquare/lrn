"""Application and gunicorn configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """App config model."""

    model_config = SettingsConfigDict(
        env_prefix="LRN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str | None = None
    db_url: str = "postgresql://postgres:postgres@localhost:5433/lrn_db"
    review_rescore_limit: int = 25
    review_rescore_concurrency: int = 5
