"""Provider registry and selection service"""
import httpx
from typing import Dict, Optional, List
from ..core.config import Settings
from ..providers.base import LLMProvider, ModelDescriptor
from ..providers.openai import OpenAIProvider
from ..providers.openrouter import OpenRouterProvider
from ..providers.groq import GroqProvider


class ProviderSelection:
    """Active provider selection"""
    def __init__(self, provider: str, model: str, workspace_id: str = "default"):
        self.provider = provider
        self.model = model
        self.workspace_id = workspace_id


class ProviderService:
    """Manages provider instances and selection"""
    
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient):
        self.settings = settings
        self.http_client = http_client
        self._selections: Dict[str, ProviderSelection] = {}
        self._providers: Dict[str, LLMProvider] = {}
        
        # Initialize providers if keys available
        if settings.openai_api_key:
            self._providers["openai"] = OpenAIProvider(settings.openai_api_key, http_client)
        if settings.openrouter_api_key:
            self._providers["openrouter"] = OpenRouterProvider(settings.openrouter_api_key, http_client)
        if settings.groq_api_key:
            self._providers["groq"] = GroqProvider(settings.groq_api_key, http_client)
    
    def get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """Get provider instance by name"""
        return self._providers.get(provider_name)
    
    def is_provider_enabled(self, provider_name: str) -> bool:
        """Check if provider is enabled (has API key)"""
        return provider_name in self._providers
    
    async def list_providers(self) -> List[Dict]:
        """List all providers with their models"""
        result = []

        for name in ["openai", "openrouter", "groq"]:
            enabled = self.is_provider_enabled(name)
            models = []

            if enabled:
                provider = self._providers[name]
                models = [m.model_dump() for m in await provider.list_models()]

            result.append({
                "name": name,
                "enabled": enabled,
                "models": models
            })

        return result
    
    def set_selection(self, provider: str, model: str, workspace_id: str = "default"):
        """Set active provider/model for workspace"""
        if not self.is_provider_enabled(provider):
            raise ValueError(f"Provider {provider} is not enabled")
        
        self._selections[workspace_id] = ProviderSelection(provider, model, workspace_id)
    
    def get_selection(self, workspace_id: str = "default") -> ProviderSelection:
        """Get active selection for workspace, fallback to defaults"""
        if workspace_id in self._selections:
            return self._selections[workspace_id]
        
        # Return default from settings
        return ProviderSelection(
            provider=self.settings.default_provider,
            model=self.settings.default_model,
            workspace_id=workspace_id
        )
    
    def resolve_provider_and_model(
        self,
        provider_override: Optional[str] = None,
        model_override: Optional[str] = None,
        workspace_id: str = "default"
    ) -> tuple[str, str]:
        """Resolve provider and model with precedence: override > workspace > default"""
        
        if provider_override and model_override:
            return provider_override, model_override
        
        selection = self.get_selection(workspace_id)
        
        provider = provider_override or selection.provider
        model = model_override or selection.model
        
        return provider, model

