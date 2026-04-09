"""
Fluency scorer: lightweight heuristic — no ML dependency, fast.

Four signals (equal weight):
  1. Lexical diversity  — type-token ratio (penalises repetitive vocabulary).
  2. Sentence completeness — fraction of sentences ending with terminal punctuation.
  3. Capitalisation       — first character should be uppercase.
  4. Bigram repetition   — penalises repeated two-word phrases (>2 occurrences).
"""
import re
from collections import Counter
from typing import Optional

from app.scorers.base import QualityScorer


class FluencyScorer(QualityScorer):
    """Heuristic fluency scorer (no ML required)."""

    name = "fluency"
    weight = 1.0

    def score(self, text: str, context: Optional[str] = None) -> float:
        if not text or not text.strip():
            return 0.0

        text = text.strip()
        signals: list[float] = []

        words = re.findall(r"\w+", text.lower())

        # 1. Lexical diversity (type-token ratio, capped at 1.0)
        if words:
            ttr = min(len(set(words)) / len(words) * 1.5, 1.0)
            signals.append(ttr)

        # 2. Sentence completeness
        sentences = re.split(r"(?<=[.!?])\s+", text)
        complete = sum(1 for s in sentences if s.strip() and s.strip()[-1] in ".!?")
        signals.append(complete / len(sentences) if sentences else 0.0)

        # 3. Capitalisation
        signals.append(1.0 if text[0].isupper() else 0.3)

        # 4. Bigram repetition penalty
        if len(words) > 1:
            bigrams = [f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1)]
            max_freq = max(Counter(bigrams).values())
            rep_penalty = max(0.0, 1.0 - (max_freq - 2) * 0.15) if max_freq > 2 else 1.0
            signals.append(rep_penalty)

        return round(sum(signals) / len(signals), 4) if signals else 0.5
