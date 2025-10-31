"""Pydantic settings for environment configuration"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Environment
    env: str = "development"
    app_name: str = "ai-draft-backend"
    app_version: str = "1.0.0"

    # API Keys
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    # Default Provider Settings
    default_provider: str = "openrouter"
    default_model: str = "openrouter/auto"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 5
    rate_limit_per_day: int = 200

    # Security
    api_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    log_json: bool = True


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get cached settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
