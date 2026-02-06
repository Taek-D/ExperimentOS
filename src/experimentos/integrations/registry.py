from typing import Dict, Type, Optional
from .base import IntegrationProvider, ProviderNotFoundError

class IntegrationRegistry:
    """Registry to manage and retrieve integration providers."""
    _providers: Dict[str, Type[IntegrationProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[IntegrationProvider]):
        """Register a new provider."""
        cls._providers[name] = provider_cls

    @classmethod
    def get_provider_class(cls, name: str) -> Type[IntegrationProvider]:
        """Get a provider class by name."""
        provider = cls._providers.get(name)
        if not provider:
            raise ProviderNotFoundError(f"Provider '{name}' not found", provider=name)
        return provider

    @classmethod
    def get_provider(cls, name: str, api_key: str) -> IntegrationProvider:
        """Factory method to instantiate a provider."""
        provider_cls = cls.get_provider_class(name)
        # Assuming all providers accept api_key in __init__
        return provider_cls(api_key=api_key)  # type: ignore[call-arg]

# Global registry access
registry = IntegrationRegistry
