"""
Coherence scorer: measures how logically connected adjacent sentences are.

Strategy:
  - Split text into sentences.
  - Embed each sentence with a lightweight sentence-transformer model.
  - Compute average cosine similarity between consecutive sentence pairs.
  - Map to [0, 1]; single-sentence inputs score 1.0 (trivially coherent).
"""
import re

import numpy as np

from app.scorers.base import QualityScorer
from app.scorers.utils import embed, norm_sim_to_score


def split_sentences(text: str) -> list[str]:
    """Split text into non-empty sentences on terminal punctuation."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


class CoherenceScorer(QualityScorer):
    """Sentence-embedding coherence scorer."""

    name = "coherence"
    weight = 1.0

    def score(self, text: str, context: str | None = None) -> float:
        sentences = split_sentences(text)
        if len(sentences) <= 1:
            return 1.0

        embeddings = embed(sentences)
        similarities = [
            norm_sim_to_score(float(np.dot(embeddings[i], embeddings[i + 1])))
            for i in range(len(embeddings) - 1)
        ]
        return round(float(np.mean(similarities)), 4)
