from abc import ABC, abstractmethod
from typing import List


class ModelProviderAdapter(ABC):
    """
    Abstract base class for AI model provider integrations.
    Implement this to support OpenAI, HuggingFace, or any custom endpoint.
    """

    provider_name: str = "base"

    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """Request a text completion from the provider."""
        ...

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Return a vector embedding for the given text."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_name!r})"
