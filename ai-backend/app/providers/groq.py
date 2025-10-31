"""Groq provider implementation"""
import httpx
from typing import Any, Dict, List
from .base import (
    LLMProvider,
    PromptPacket,
    LLMRawResponse,
    ProviderCapabilities,
    ModelDescriptor
)


class GroqProvider(LLMProvider):
    """Groq API provider (OpenAI-compatible)"""

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODELS_URL = "https://api.groq.com/openai/v1/models"

    def __init__(self, api_key: str, http_client: httpx.AsyncClient):
        super().__init__(api_key)
        self.http_client = http_client

    async def generate(self, prompt: PromptPacket) -> LLMRawResponse:
        """Generate completion using Groq API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = [
            {"role": "system", "content": prompt.system_prompt},
            {"role": "user", "content": prompt.user_prompt}
        ]

        body: Dict[str, Any] = {
            "model": prompt.model,
            "messages": messages,
            "temperature": prompt.temperature
        }

        if prompt.response_format:
            body["response_format"] = prompt.response_format

        if prompt.tools:
            body["tools"] = prompt.tools

        if prompt.tool_choice:
            body["tool_choice"] = prompt.tool_choice

        response = await self.http_client.post(
            self.BASE_URL,
            headers=headers,
            json=body,
            timeout=60.0
        )
        response.raise_for_status()

        data = response.json()
        choice = data["choices"][0]
        message_content = choice["message"].get("content", "")
        content_text = self._coerce_message_content(message_content)

        return LLMRawResponse(
            content=content_text,
            model=data.get("model", prompt.model),
            provider="groq",
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage")
        )

    @staticmethod
    def _coerce_message_content(message_content: Any) -> str:
        """Groq mirrors OpenAI responses; normalise to text."""

        if isinstance(message_content, list):
            fragments = []
            for part in message_content:
                if isinstance(part, dict) and "text" in part:
                    fragments.append(part["text"])
            if fragments:
                return "".join(fragments)

        if isinstance(message_content, str):
            return message_content

        return str(message_content)

    def capabilities(self) -> ProviderCapabilities:
        """Groq supports plain JSON mode"""
        return ProviderCapabilities(
            supports_json_schema=False,
            supports_function_call=False,
            supports_plain_json=True
        )

    async def list_models(self) -> List[ModelDescriptor]:
        """Fetch available Groq models from API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = await self.http_client.get(
                self.MODELS_URL,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()

            data = response.json()
            models = []

            # Process all models from API
            for model_data in data.get("data", []):
                model_id = model_data.get("id", "")

                # Skip non-active models
                if not model_data.get("active", True):
                    continue

                # Determine family from model ID
                family = "unknown"
                if "llama" in model_id.lower():
                    family = "llama"
                elif "mixtral" in model_id.lower():
                    family = "mixtral"
                elif "gemma" in model_id.lower():
                    family = "gemma"

                # Get context window from API response
                context_window = model_data.get("context_window", 8192)

                models.append(ModelDescriptor(
                    id=model_id,
                    family=family,
                    context_window=context_window,
                    supports_json_schema=False,
                    notes=f"Groq {model_id}"
                ))

            # Sort by family and ID for consistent ordering
            models.sort(key=lambda m: (m.family, m.id))

            return models

        except Exception as e:
            # Fallback to hardcoded list if API call fails
            return [
                ModelDescriptor(
                    id="llama-3.1-70b-versatile",
                    family="llama",
                    context_window=128000,
                    supports_json_schema=False,
                    notes="Fast inference, versatile"
                ),
                ModelDescriptor(
                    id="llama-3.1-8b-instant",
                    family="llama",
                    context_window=128000,
                    supports_json_schema=False,
                    notes="Ultra-fast, smaller model"
                ),
                ModelDescriptor(
                    id="mixtral-8x7b-32768",
                    family="mixtral",
                    context_window=32768,
                    supports_json_schema=False,
                    notes="Mixture of experts"
                )
            ]
