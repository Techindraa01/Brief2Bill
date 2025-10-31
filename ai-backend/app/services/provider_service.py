"""Provider registry and selection management."""

from __future__ import annotations

from typing import Dict, List, Optional

import httpx

from ..core.config import Settings
from ..providers.base import LLMProvider, ModelDescriptor
from ..providers.groq import GroqProvider
from ..providers.openai import OpenAIProvider
from ..providers.openrouter import OpenRouterProvider
from ..providers.gemini import GeminiProvider


class ProviderSelection:
    def __init__(self, provider: str, model: str, workspace_id: str = "default") -> None:
        self.provider = provider
        self.model = model
        self.workspace_id = workspace_id


class ProviderService:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient) -> None:
        self.settings = settings
        self.http_client = http_client
        self._providers: Dict[str, LLMProvider] = {}
        self._selections: Dict[str, ProviderSelection] = {}

        if settings.openrouter_api_key:
            self._providers["openrouter"] = OpenRouterProvider(settings.openrouter_api_key, http_client)
        if settings.groq_api_key:
            self._providers["groq"] = GroqProvider(settings.groq_api_key, http_client)
        if settings.openai_api_key:
            self._providers["openai"] = OpenAIProvider(settings.openai_api_key, http_client)
        gemini_key = settings.gemini_key
        if gemini_key:
            self._providers["gemini"] = GeminiProvider(gemini_key, http_client)

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        return self._providers.get(name)

    def is_provider_enabled(self, name: str) -> bool:
        return name in self._providers

    async def describe_providers(self) -> List[Dict[str, object]]:
        providers: List[Dict[str, object]] = []
        for name in ["openrouter", "groq", "openai", "gemini"]:
            provider = self._providers.get(name)
            enabled = provider is not None
            models: List[ModelDescriptor] = []
            if provider:
                try:
                    models = await provider.list_models()
                except Exception:
                    models = []
            providers.append(
                {
                    "name": name,
                    "enabled": enabled,
                    "models": [model.model_dump() for model in models],
                }
            )
        return providers

    def set_selection(self, provider: str, model: str, workspace_id: str = "default") -> None:
        if provider not in self._providers:
            raise ValueError(f"Provider {provider} is not enabled")
        self._selections[workspace_id] = ProviderSelection(provider, model, workspace_id)

    def get_selection(self, workspace_id: str = "default") -> ProviderSelection:
        if workspace_id in self._selections:
            return self._selections[workspace_id]
        return ProviderSelection(self.settings.default_provider, self.settings.default_model, workspace_id)

    def resolve(self, workspace_id: str, provider_override: Optional[str], model_override: Optional[str]) -> ProviderSelection:
        if provider_override and model_override:
            return ProviderSelection(provider_override, model_override, workspace_id)
        selection = self.get_selection(workspace_id)
        provider = provider_override or selection.provider
        model = model_override or selection.model
        return ProviderSelection(provider, model, workspace_id)
