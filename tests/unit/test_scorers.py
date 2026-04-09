"""Unit tests for scorer implementations and the scorer registry."""
import pytest

from app.scorers.coherence import CoherenceScorer, split_sentences
from app.scorers.fluency import FluencyScorer
from app.scorers.registry import available_metrics, get_scorer
from app.scorers.relevance import RelevanceScorer

# ── split_sentences ────────────────────────────────────────────────────────────

def test_split_sentences_single():
    assert split_sentences("Hello world.") == ["Hello world."]


def test_split_sentences_multiple():
    result = split_sentences("Hello world. How are you? Fine!")
    assert len(result) == 3


def test_split_sentences_filters_empty():
    result = split_sentences("  Hello.   World.  ")
    assert all(s.strip() for s in result)


# ── CoherenceScorer ───────────────────────────────────────────────────────────

class TestCoherenceScorer:
    def test_single_sentence_returns_one(self):
        assert CoherenceScorer().score("Only one sentence.") == pytest.approx(1.0)

    def test_multi_sentence_score_in_range(self):
        score = CoherenceScorer().score("First. Second. Third.")
        assert 0.0 <= score <= 1.0

    def test_returns_float(self):
        assert isinstance(CoherenceScorer().score("Hello. World."), float)

    def test_name(self):
        assert CoherenceScorer.name == "coherence"

    def test_weight_positive(self):
        assert CoherenceScorer.weight > 0

    def test_deterministic(self):
        scorer = CoherenceScorer()
        t = "Sentence one. Sentence two. Sentence three."
        assert scorer.score(t) == scorer.score(t)

    def test_repr_contains_name(self):
        assert "coherence" in repr(CoherenceScorer())


# ── RelevanceScorer ────────────────────────────────────────────────────────────

class TestRelevanceScorer:
    def test_with_context_in_range(self):
        score = RelevanceScorer().score("Paris.", context="Capital of France?")
        assert 0.0 <= score <= 1.0

    def test_no_context_returns_neutral(self):
        assert RelevanceScorer().score("Hello.", context=None) == pytest.approx(0.5)

    def test_blank_context_returns_neutral(self):
        assert RelevanceScorer().score("Hello.", context="  ") == pytest.approx(0.5)

    def test_returns_float(self):
        assert isinstance(RelevanceScorer().score("Test.", context="Prompt."), float)

    def test_name(self):
        assert RelevanceScorer.name == "relevance"


# ── FluencyScorer ──────────────────────────────────────────────────────────────

class TestFluencyScorer:
    def test_score_in_range(self):
        score = FluencyScorer().score("The quick brown fox jumps over the lazy dog.")
        assert 0.0 <= score <= 1.0

    def test_returns_float(self):
        assert isinstance(FluencyScorer().score("Hello world."), float)

    def test_capitalised_text_scores_higher_than_lowercase(self):
        high = FluencyScorer().score("This is a properly written sentence.")
        low = FluencyScorer().score("this is not capitalised properly.")
        assert high >= low

    def test_repetitive_text_penalised(self):
        normal = FluencyScorer().score("The cat sat on the mat today.")
        repetitive = FluencyScorer().score(
            "the the the the the the the the the the the"
        )
        assert normal >= repetitive

    def test_name(self):
        assert FluencyScorer.name == "fluency"

    def test_very_short_text(self):
        score = FluencyScorer().score("Hi.")
        assert 0.0 <= score <= 1.0

    def test_context_ignored(self):
        """FluencyScorer should not raise when context is passed."""
        score = FluencyScorer().score("Hello world.", context="some context")
        assert 0.0 <= score <= 1.0

    def test_deterministic(self):
        scorer = FluencyScorer()
        t = "Consistent text for testing."
        assert scorer.score(t) == scorer.score(t)


# ── Registry ──────────────────────────────────────────────────────────────────

class TestRegistry:
    def test_available_metrics(self):
        assert set(available_metrics()) == {"coherence", "relevance", "fluency"}

    def test_get_coherence(self):
        assert get_scorer("coherence").name == "coherence"

    def test_get_relevance(self):
        assert get_scorer("relevance").name == "relevance"

    def test_get_fluency(self):
        assert get_scorer("fluency").name == "fluency"

    def test_unknown_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown metric"):
            get_scorer("toxicity")

    def test_singleton(self):
        assert get_scorer("coherence") is get_scorer("coherence")
