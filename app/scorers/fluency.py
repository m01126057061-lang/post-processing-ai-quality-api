"""
Fluency scorer: heuristic + readability signals, language-aware.

Five signals (equal weight):
  1. Lexical diversity  — type-token ratio, adjusted for agglutinative languages.
  2. Sentence completeness — fraction of sentences ending with terminal punctuation.
  3. Capitalisation       — first character should be uppercase (Latin-script only).
  4. Bigram repetition   — penalises repeated two-word phrases (>2 occurrences).
  5. Readability          — Flesch Reading Ease normalised to [0, 1] via textstat
                            (graceful fallback to heuristics if textstat unavailable).

Language detection (langdetect) adapts rules to the detected language.
Graceful degradation: if langdetect / textstat are unavailable, falls back to
the original heuristic-only mode without raising errors.
"""
from __future__ import annotations

import re
from collections import Counter

from app.scorers.base import QualityScorer

try:
    import textstat  # type: ignore
    _TEXTSTAT_AVAILABLE = True
except ImportError:
    _TEXTSTAT_AVAILABLE = False

try:
    from app.scorers.language import detect_language, is_agglutinative, is_latin_script
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False


def _flesch_score(text: str) -> float:
    """Normalise Flesch Reading Ease (0–100) to [0, 1].

    Flesch RE:  100 = very easy, 0 = very hard.
    We clip to [0, 100] first to guard against negative values on technical text.
    """
    if not _TEXTSTAT_AVAILABLE:
        return 0.7  # neutral fallback when textstat unavailable

    raw = textstat.flesch_reading_ease(text)
    clipped = max(0.0, min(100.0, raw))
    return round(clipped / 100.0, 4)


class FluencyScorer(QualityScorer):
    """Heuristic + readability fluency scorer with language awareness."""

    name = "fluency"
    weight = 1.0

    def score(self, text: str, context: str | None = None) -> float:
        if not text or not text.strip():
            return 0.0

        text = text.strip()
        signals: list[float] = []

        # ── Language detection ────────────────────────────────────────────────
        if _LANGDETECT_AVAILABLE:
            lang = detect_language(text)
            latin = is_latin_script(lang)
            agglut = is_agglutinative(lang)
        else:
            lang, latin, agglut = "en", True, False

        words = re.findall(r"\w+", text.lower())

        # 1. Lexical diversity (TTR) — adjusted for agglutinative languages
        if words:
            raw_ttr = len(set(words)) / len(words)
            # Agglutinative langs naturally have lower repetition; scale factor up
            scale = 1.2 if agglut else 1.5
            ttr = min(raw_ttr * scale, 1.0)
            signals.append(ttr)

        # 2. Sentence completeness
        sentences = re.split(r"(?<=[.!?])\s+", text)
        complete = sum(1 for s in sentences if s.strip() and s.strip()[-1] in ".!?")
        signals.append(complete / len(sentences) if sentences else 0.0)

        # 3. Capitalisation — only for Latin-script languages
        if latin:
            signals.append(1.0 if text[0].isupper() else 0.3)

        # 4. Bigram repetition penalty
        if len(words) > 1:
            bigrams = [f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1)]
            max_freq = max(Counter(bigrams).values())
            rep_penalty = max(0.0, 1.0 - (max_freq - 2) * 0.15) if max_freq > 2 else 1.0
            signals.append(rep_penalty)

        # 5. Readability (Flesch Reading Ease → [0,1])
        signals.append(_flesch_score(text))

        return round(sum(signals) / len(signals), 4) if signals else 0.5
