from abc import ABC, abstractmethod

# ── Score label helpers ──────────────────────────────────────────────────────

_SCORE_BANDS: list[tuple[float, str]] = [
    (0.85, "high"),
    (0.70, "good"),
    (0.50, "moderate"),
    (0.30, "low"),
    (0.00, "very low"),
]

_METRIC_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "coherence": {
        "high":     "sentences flow logically throughout",
        "good":     "mostly coherent with minor topic shifts",
        "moderate": "some logical gaps between sentences",
        "low":      "noticeable topic jumps or contradictions",
        "very low": "text lacks logical structure",
    },
    "fluency": {
        "high":     "natural, well-formed grammar",
        "good":     "generally readable with minor issues",
        "moderate": "some grammar or readability concerns",
        "low":      "awkward phrasing or grammatical errors",
        "very low": "difficult to read",
    },
    "relevance": {
        "high":     "directly addresses the given context",
        "good":     "mostly on-topic",
        "moderate": "partially relevant to the context",
        "low":      "mostly off-topic",
        "very low": "does not address the context",
    },
    "toxicity": {
        "high":     "no toxic or harmful content detected",
        "good":     "minimal potentially sensitive content",
        "moderate": "some potentially sensitive language",
        "low":      "contains harmful or offensive content",
        "very low": "highly toxic content detected",
    },
    "hallucination": {
        "high":     "well-grounded in the provided context",
        "good":     "mostly supported by context",
        "moderate": "some claims not directly supported by context",
        "low":      "likely contains fabricated information",
        "very low": "contradicts or significantly deviates from context",
    },
}


def _score_band(score: float) -> str:
    for threshold, label in _SCORE_BANDS:
        if score >= threshold:
            return label
    return "very low"


# ── Abstract base ────────────────────────────────────────────────────────────

class QualityScorer(ABC):
    """
    Abstract base class for all quality scorers.

    Subclasses must implement score() and set a unique name.
    Scores must be in the range [0.0, 1.0].

    The default explain() method returns a human-readable label based on the
    numeric score.  Override it in a subclass for richer explanations.
    """

    name: str = "base"
    weight: float = 1.0
    requires_context: bool = False

    @abstractmethod
    def score(self, text: str, context: str | None = None) -> float:
        """Compute a quality score between 0.0 (lowest) and 1.0 (highest)."""
        ...

    def explain(self, score: float) -> str:
        """Return a one-line human-readable explanation for a computed score."""
        band = _score_band(score)
        descriptions = _METRIC_DESCRIPTIONS.get(self.name, {})
        detail = descriptions.get(band, band)
        return f"{score:.2f} ({band}) — {detail}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, weight={self.weight})"
