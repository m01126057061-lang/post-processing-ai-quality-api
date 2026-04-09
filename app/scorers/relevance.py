"""
Relevance scorer: measures how well the generated text addresses the prompt/context.

Strategy:
  - Embed both the context and the response.
  - Cosine similarity between the two embeddings → relevance proxy.
  - Returns 0.5 (neutral) when no context is provided.
"""
from typing import Optional

from app.scorers.base import QualityScorer
from app.scorers.utils import embed, norm_sim_to_score


class RelevanceScorer(QualityScorer):
    """Embedding-based relevance scorer."""

    name = "relevance"
    weight = 1.0

    def score(self, text: str, context: Optional[str] = None) -> float:
        if not context or not context.strip():
            return 0.5  # neutral — nothing to compare against

        embeddings = embed([context.strip(), text.strip()])
        return round(norm_sim_to_score(float(embeddings[0] @ embeddings[1])), 4)
