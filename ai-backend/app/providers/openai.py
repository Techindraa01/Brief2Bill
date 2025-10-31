"""OpenAI provider implementation"""
import httpx
from typing import Any, Dict, List
from .base import (
    LLMProvider,
    PromptPacket,
    LLMRawResponse,
    ProviderCapabilities,
    ModelDescriptor
)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider with JSON schema support"""

    BASE_URL = "https://api.openai.com/v1/chat/completions"
    MODELS_URL = "https://api.openai.com/v1/models"

    def __init__(self, api_key: str, http_client: httpx.AsyncClient):
        super().__init__(api_key)
        self.http_client = http_client

    async def generate(self, prompt: PromptPacket) -> LLMRawResponse:
        """Generate completion using OpenAI API"""
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
            provider="openai",
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage")
        )

    @staticmethod
    def _coerce_message_content(message_content: Any) -> str:
        """Normalise OpenAI message content to a string payload."""

        if isinstance(message_content, list):
            # OpenAI json_schema responses return content parts with type metadata
            for part in message_content:
                if not isinstance(part, dict):
                    continue

                if part.get("type") == "output_json" and "text" in part:
                    return part["text"]

            # Fallback: concatenate any text fragments
            fragments = [part.get("text", "") for part in message_content if isinstance(part, dict)]
            return "".join(fragments)

        if isinstance(message_content, str):
            return message_content

        return str(message_content)
    
    def capabilities(self) -> ProviderCapabilities:
        """OpenAI supports JSON schema enforcement"""
        return ProviderCapabilities(
            supports_json_schema=True,
            supports_function_call=True,
            supports_plain_json=True
        )
    
    async def list_models(self) -> List[ModelDescriptor]:
        """Fetch available OpenAI models from API"""
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

            # Filter for chat models (gpt-* models)
            for model_data in data.get("data", []):
                model_id = model_data.get("id", "")

                # Only include GPT chat models
                if model_id.startswith("gpt-"):
                    # Determine family from model ID
                    family = "gpt-4" if "gpt-4" in model_id else "gpt-3.5"

                    # Estimate context window based on model name
                    context_window = 128000  # Default for newer models
                    if "gpt-3.5" in model_id:
                        context_window = 16385

                    models.append(ModelDescriptor(
                        id=model_id,
                        family=family,
                        context_window=context_window,
                        supports_json_schema=True,
                        notes=f"OpenAI {model_id}"
                    ))

            # Sort by family and ID for consistent ordering
            models.sort(key=lambda m: (m.family, m.id))

            return models

        except Exception as e:
            # Fallback to hardcoded list if API call fails
            return [
                ModelDescriptor(
                    id="gpt-4o",
                    family="gpt-4",
                    context_window=128000,
                    supports_json_schema=True,
                    notes="Most capable model"
                ),
                ModelDescriptor(
                    id="gpt-4o-mini",
                    family="gpt-4",
                    context_window=128000,
                    supports_json_schema=True,
                    notes="Fast and cost-effective"
                ),
                ModelDescriptor(
                    id="gpt-4-turbo",
                    family="gpt-4",
                    context_window=128000,
                    supports_json_schema=True,
                    notes="Previous generation"
                )
            ]

