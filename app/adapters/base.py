"""
Abstract base class for model provider adapters.

Each adapter wraps a specific LLM backend (OpenAI, Anthropic, HuggingFace, …)
and exposes two primary operations:

  complete(prompt)          — raw text generation
  score_quality(text, ...)  — structured quality scoring via a scoring prompt

Adapters are instantiated per-request via registry.get_adapter(); they must be
lightweight to construct (no heavy I/O in __init__).
"""
from abc import ABC, abstractmethod


class ModelProviderAdapter(ABC):
    """Abstract model provider adapter."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Machine-readable provider slug (e.g. 'openai')."""

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model identifier used when caller does not specify one."""

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """True when the required credentials/config are present in the environment."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        **kwargs,
    ) -> str:
        """Send a raw prompt and return the model's text completion."""

    @abstractmethod
    async def score_quality(
        self,
        text: str,
        context: str | None,
        criteria: list[str],
        model: str | None = None,
    ) -> tuple[dict[str, float], str]:
        """
        Use the LLM to score the quality of *text* on each criterion.

        Returns:
            (scores, reasoning) where scores maps criterion -> float in [0.0, 1.0].
        """

    def info(self) -> dict:
        """Serialisable summary of this adapter's identity and availability."""
        return {
            "provider": self.provider_name,
            "default_model": self.default_model,
            "available": self.is_available,
        }
