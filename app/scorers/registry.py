"""
Central scorer registry.

All scorer instances are singletons — they are created once and reused across requests.
ML-backed scorers (coherence, relevance) lazy-load their models on first call.
"""
from typing import Dict, List

from app.scorers.base import QualityScorer
from app.scorers.coherence import CoherenceScorer
from app.scorers.fluency import FluencyScorer
from app.scorers.relevance import RelevanceScorer

_REGISTRY: Dict[str, QualityScorer] = {
    "coherence": CoherenceScorer(),
    "relevance": RelevanceScorer(),
    "fluency": FluencyScorer(),
}


def get_scorer(name: str) -> QualityScorer:
    """Return the scorer for *name*, or raise KeyError if unknown."""
    if name not in _REGISTRY:
        raise KeyError(
            f"Unknown metric: {name!r}. Available metrics: {available_metrics()}"
        )
    return _REGISTRY[name]


def available_metrics() -> List[str]:
    """Return names of all registered metrics."""
    return list(_REGISTRY)
