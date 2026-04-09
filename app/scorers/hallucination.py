"""
Hallucination detection scorer via Natural Language Inference (NLI).

Uses `cross-encoder/nli-deberta-v3-small` from sentence-transformers.

Strategy:
  - Frame the task as NLI: premise = context, hypothesis = generated text.
  - Run inference → get [contradiction, entailment, neutral] probabilities (softmax).
  - Score = P(entailment) — high value means the output is grounded in context.

No-context behaviour:
  - Hallucination detection is meaningless without a reference context.
  - Returns 0.5 (neutral) with a logged warning when context is absent.
  - Set `requires_context = True` so callers can detect this case.

Model: cross-encoder/nli-deberta-v3-small (~80 MB, fast CPU inference)
No new pip dependencies — uses the existing `sentence-transformers` package.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import numpy as np

from app.scorers.base import QualityScorer

logger = logging.getLogger(__name__)

# Label order for cross-encoder/nli-deberta-v3-small
# 0 = contradiction, 1 = entailment, 2 = neutral
_ENTAILMENT_IDX = 1


@lru_cache(maxsize=1)
def _get_model():
    """Lazy-load and cache the NLI cross-encoder model."""
    from sentence_transformers.cross_encoder import CrossEncoder  # type: ignore
    return CrossEncoder("cross-encoder/nli-deberta-v3-small")


def _softmax(logits: np.ndarray) -> np.ndarray:
    e = np.exp(logits - np.max(logits))
    return e / e.sum()


class HallucinationScorer(QualityScorer):
    """
    NLI-based hallucination detection scorer.

    Returns a *groundedness* score in [0, 1]:
      - 1.0 = fully entailed by context (no hallucination detected)
      - 0.0 = contradicts context (likely hallucinated)
      - ~0.5 = neutral / unverifiable

    Requires context to produce a meaningful score.
    """

    name = "hallucination"
    weight = 1.0
    requires_context: bool = True

    def score(self, text: str, context: Optional[str] = None) -> float:
        if not context or not context.strip():
            logger.warning(
                "HallucinationScorer.score() called without context — "
                "returning neutral 0.5. Supply context for meaningful scores."
            )
            return 0.5

        if not text or not text.strip():
            return 1.0  # empty output cannot hallucinate

        model = _get_model()
        try:
            logits = model.predict([(context.strip(), text.strip())],
                                   apply_softmax=False)[0]
            probs = _softmax(np.array(logits, dtype=float))
            return round(float(probs[_ENTAILMENT_IDX]), 4)
        except Exception as exc:  # pragma: no cover
            logger.warning("HallucinationScorer.score() failed: %s", exc)
            return 0.5
