"""
Toxicity scorer: detects harmful, offensive, or toxic content.

Uses the `detoxify` library (BERT-based multilingual model).
Score = 1.0 - max(sub-scores) — high score means safe content.

Sub-categories checked:
  toxicity, severe_toxicity, obscene, threat, insult, identity_attack

Model is lazy-loaded on first call and cached (same pattern as other ML scorers).
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from app.scorers.base import QualityScorer

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model():
    """Lazy-load and cache the detoxify multilingual model."""
    try:
        from detoxify import Detoxify  # type: ignore
        return Detoxify("multilingual")
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "detoxify is required for ToxicityScorer. "
            "Install it with: pip install detoxify"
        ) from exc


class ToxicityScorer(QualityScorer):
    """
    BERT-based toxicity scorer via detoxify.

    Returns a *safety* score in [0, 1]:
      - 1.0 = completely safe
      - 0.0 = maximally toxic

    Score = 1 - max(toxicity, severe_toxicity, obscene, threat, insult, identity_attack)
    """

    name = "toxicity"
    weight = 1.0
    requires_context: bool = False

    _SUB_KEYS = (
        "toxicity",
        "severe_toxicity",
        "obscene",
        "threat",
        "insult",
        "identity_attack",
    )

    def score(self, text: str, context: Optional[str] = None) -> float:
        if not text or not text.strip():
            return 1.0  # empty text is trivially non-toxic

        model = _get_model()
        try:
            predictions: dict = model.predict(text.strip())
            worst = max(float(predictions.get(k, 0.0)) for k in self._SUB_KEYS)
            return round(max(0.0, 1.0 - worst), 4)
        except Exception as exc:  # pragma: no cover
            logger.warning("ToxicityScorer.score() failed: %s", exc)
            return 0.5  # neutral fallback on unexpected error
