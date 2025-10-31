"""OpenRouter provider implementation"""
import json
import httpx
from typing import Any, Dict, List
from .base import (
    LLMProvider,
    PromptPacket,
    LLMRawResponse,
    ProviderCapabilities,
    ModelDescriptor
)


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider"""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODELS_URL = "https://openrouter.ai/api/v1/models"

    def __init__(self, api_key: str, http_client: httpx.AsyncClient):
        super().__init__(api_key)
        self.http_client = http_client

    async def generate(self, prompt: PromptPacket) -> LLMRawResponse:
        """Generate completion using OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://brief2bill.app",
            "X-Title": "Brief2Bill"
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
            provider="openrouter",
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage")
        )

    @staticmethod
    def _coerce_message_content(message_content: Any) -> str:
        """OpenRouter mirrors OpenAI responses; normalise to text."""

        if isinstance(message_content, list):
            json_payload: Any = None
            fragments: list[str] = []

            for part in message_content:
                if not isinstance(part, dict):
                    continue

                part_type = part.get("type")

                if part_type == "output_json":
                    if "json" in part:
                        json_payload = part["json"]
                        break
                    if "text" in part:
                        return part["text"]

                text_value = part.get("text")
                if text_value:
                    fragments.append(text_value)

            if json_payload is not None:
                if isinstance(json_payload, (dict, list)):
                    try:
                        return json.dumps(json_payload)
                    except TypeError:
                        return str(json_payload)
                return str(json_payload)

            return "".join(fragments)

        if isinstance(message_content, str):
            return message_content

        return str(message_content)

    def capabilities(self) -> ProviderCapabilities:
        """OpenRouter supports plain JSON mode"""
        return ProviderCapabilities(
            supports_json_schema=False,
            supports_function_call=False,
            supports_plain_json=True
        )

    async def list_models(self) -> List[ModelDescriptor]:
        """Fetch available OpenRouter models from API"""
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

            # Process models from API
            for model_data in data.get("data", []):
                model_id = model_data.get("id", "")

                # Determine family from model ID
                family = "unknown"
                if "/" in model_id:
                    family = model_id.split("/")[0]

                # Get context window from API response
                context_window = model_data.get("context_length", 8192)

                # Get model name for notes
                model_name = model_data.get("name", model_id)

                models.append(ModelDescriptor(
                    id=model_id,
                    family=family,
                    context_window=context_window,
                    supports_json_schema=False,
                    notes=model_name
                ))

            # Sort by family and ID for consistent ordering
            models.sort(key=lambda m: (m.family, m.id))

            return models

        except Exception as e:
            # Fallback to hardcoded list if API call fails
            return [
                ModelDescriptor(
                    id="openrouter/auto",
                    family="auto",
                    supports_json_schema=False,
                    notes="Automatic model selection"
                ),
                ModelDescriptor(
                    id="anthropic/claude-3.5-sonnet",
                    family="claude",
                    context_window=200000,
                    supports_json_schema=False,
                    notes="Most capable Claude model"
                ),
                ModelDescriptor(
                    id="google/gemini-pro-1.5",
                    family="gemini",
                    context_window=1000000,
                    supports_json_schema=False,
                    notes="Large context window"
                ),
                ModelDescriptor(
                    id="meta-llama/llama-3.1-70b-instruct",
                    family="llama",
                    context_window=128000,
                    supports_json_schema=False,
                    notes="Open source model"
                )
            ]
