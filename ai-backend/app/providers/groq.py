"""Groq provider implementation (placeholder)"""
from .base import LLMProvider

class GroqProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        return f"[groq simulated] {prompt}"
