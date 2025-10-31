"""OpenRouter provider implementation (placeholder)"""
from .base import LLMProvider

class OpenRouterProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        return f"[openrouter simulated] {prompt}"
