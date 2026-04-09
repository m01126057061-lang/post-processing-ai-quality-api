"""
Relevance scorer: measures how well the generated text addresses the prompt/context.

Strategy:
  - Embed both the context and the response.
  - Cosine similarity between the two embeddings → relevance proxy.

No-context behaviour:
  - When context is absent, scoring is impossible. The scorer returns 0.5 (neutral)
    as a defined no-op sentinel, NOT as a real relevance signal.
  - Callers should check scorer.requires_context and either supply context or
    exclude this metric from the evaluation when none is available.
  - The response schema includes a "context_provided" flag so API consumers can
    distinguish real scores from neutral fallbacks.
"""
from typing import Optional

from app.scorers.base import QualityScorer
from app.scorers.utils import embed_one, norm_sim_to_score

#: This scorer produces meaningful results only when context is provided.
#: Without context, it returns 0.5 (neutral sentinel).
NEUTRAL_NO_CONTEXT = 0.5


class RelevanceScorer(QualityScorer):
    """Embedding-based relevance scorer."""

    name = "relevance"
    weight = 1.0
    requires_context: bool = True  # meaningful score requires a context string

    def score(self, text: str, context: Optional[str] = None) -> float:
        if not context or not context.strip():
            # Documented neutral sentinel — not a real relevance measurement.
            # Check requires_context before interpreting this value.
            return NEUTRAL_NO_CONTEXT

        ctx_emb = embed_one(context.strip())
        txt_emb = embed_one(text.strip())
        return round(norm_sim_to_score(float(ctx_emb @ txt_emb)), 4)
