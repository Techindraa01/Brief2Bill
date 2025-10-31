"""Application configuration via pydantic settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ai-draft-backend"
    app_version: str = "1.0.0"
    app_env: str = "development"

    default_provider: str = "openrouter"
    default_model: str = "openrouter/auto"

    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    rate_limit_per_minute: int = 5

    api_key: Optional[str] = None
    log_level: str = "INFO"
    log_json: bool = True

    @property
    def gemini_key(self) -> Optional[str]:
        return self.gemini_api_key or self.google_api_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
