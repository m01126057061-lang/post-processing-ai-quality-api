"""
Central scorer registry.

All scorer instances are singletons — created once and reused across requests.
ML-backed scorers lazy-load their models on first call.

Available metrics:
  coherence    — adjacent-sentence embedding similarity
  relevance    — output vs. context embedding similarity (requires context)
  fluency      — heuristic + readability signals (language-aware)
  toxicity     — BERT-based safety score via detoxify
  hallucination— NLI-based groundedness score (requires context)
"""
from typing import Dict, List

from app.scorers.base import QualityScorer
from app.scorers.coherence import CoherenceScorer
from app.scorers.fluency import FluencyScorer
from app.scorers.hallucination import HallucinationScorer
from app.scorers.relevance import RelevanceScorer
from app.scorers.toxicity import ToxicityScorer

_REGISTRY: Dict[str, QualityScorer] = {
    "coherence":     CoherenceScorer(),
    "relevance":     RelevanceScorer(),
    "fluency":       FluencyScorer(),
    "toxicity":      ToxicityScorer(),
    "hallucination": HallucinationScorer(),
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


def get_context_required_metrics() -> List[str]:
    """Return names of metrics that require a context string for meaningful scores."""
    return [name for name, scorer in _REGISTRY.items()
            if getattr(scorer, "requires_context", False)]
