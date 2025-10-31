"""Pydantic settings placeholder"""
from dataclasses import dataclass

@dataclass
class Settings:
    env: str = "development"
    redis_url: str = "redis://localhost:6379/0"

def get_settings() -> Settings:
    return Settings()
