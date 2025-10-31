"""Google Gemini provider integration."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .base import LLMProvider, LLMRawResponse, ModelDescriptor, PromptPacket, ProviderCapabilities


class GeminiProvider(LLMProvider):
    MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, http_client: httpx.AsyncClient) -> None:
        super().__init__(api_key)
        self.http_client = http_client

    async def generate(self, prompt: PromptPacket) -> LLMRawResponse:
        raise NotImplementedError("Gemini generation not yet implemented")

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(supports_json_schema=False, supports_plain_json=True)

    async def list_models(self) -> List[ModelDescriptor]:
        params = {"key": self.api_key}
        try:
            response = await self.http_client.get(self.MODELS_URL, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            models: List[ModelDescriptor] = []
            for item in data.get("models", []):
                if "generateContent" not in item.get("supportedGenerationMethods", []):
                    continue
                models.append(
                    ModelDescriptor(
                        id=item.get("name", ""),
                        family=item.get("displayName", "gemini"),
                        context_window=item.get("inputTokenLimit"),
                        supports_json_schema=False,
                        notes=item.get("description"),
                    )
                )
            return models
        except Exception:
            return []
