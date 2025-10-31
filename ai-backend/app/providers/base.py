"""LLMProvider base classes and models"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class PromptPacket(BaseModel):
    """Input to LLM provider"""
    system_prompt: str
    user_prompt: str
    temperature: float = 0.2
    json_schema: Optional[Dict[str, Any]] = None


class LLMRawResponse(BaseModel):
    """Raw response from LLM provider"""
    content: str
    model: str
    provider: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None  # Can contain nested dicts in newer APIs


class ModelDescriptor(BaseModel):
    """Model metadata"""
    id: str
    family: str
    context_window: Optional[int] = None
    supports_json_schema: bool = False
    notes: Optional[str] = None


class ProviderCapabilities(BaseModel):
    """Provider capability flags"""
    supports_json_schema: bool = False
    supports_function_call: bool = False
    supports_plain_json: bool = True


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def generate(self, prompt: PromptPacket) -> LLMRawResponse:
        """Generate completion from prompt"""
        raise NotImplementedError()

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities"""
        raise NotImplementedError()

    @abstractmethod
    async def list_models(self) -> List[ModelDescriptor]:
        """List available models"""
        raise NotImplementedError()
