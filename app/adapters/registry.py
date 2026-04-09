"""
Adapter registry — maps provider slugs to adapter classes and exposes a
factory function for per-request adapter instantiation.
"""
from typing import TYPE_CHECKING

from app.adapters.anthropic_adapter import AnthropicAdapter
from app.adapters.huggingface_adapter import HuggingFaceAdapter
from app.adapters.mock_adapter import MockAdapter
from app.adapters.openai_adapter import OpenAIAdapter
from app.core.exceptions import ProviderNotAvailableError, UnknownProviderError

if TYPE_CHECKING:
    from app.adapters.base import ModelProviderAdapter

_REGISTRY: dict[str, type] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "huggingface": HuggingFaceAdapter,
    "mock": MockAdapter,
}


def list_providers() -> list[dict]:
    """Return info dicts for every registered provider."""
    return [cls().info() for cls in _REGISTRY.values()]


def get_adapter(provider: str) -> "ModelProviderAdapter":
    """
    Instantiate and return the adapter for *provider*.

    Raises:
        UnknownProviderError      — if *provider* is not registered.
        ProviderNotAvailableError — if the provider's credentials are missing.
    """
    if provider not in _REGISTRY:
        raise UnknownProviderError(provider, list(_REGISTRY.keys()))
    adapter = _REGISTRY[provider]()
    if not adapter.is_available:
        raise ProviderNotAvailableError(provider)
    return adapter
