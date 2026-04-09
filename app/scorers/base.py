from abc import ABC, abstractmethod
from typing import Optional


class QualityScorer(ABC):
    """
    Abstract base class for all quality scorers.

    Subclasses must implement score() and set a unique name.
    Scores must be in the range [0.0, 1.0].
    """

    name: str = "base"
    weight: float = 1.0

    @abstractmethod
    def score(self, text: str, context: Optional[str] = None) -> float:
        """Compute a quality score between 0.0 (lowest) and 1.0 (highest)."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, weight={self.weight})"
