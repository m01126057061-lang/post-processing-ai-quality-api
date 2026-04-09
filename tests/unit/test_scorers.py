import pytest
from app.scorers.base import QualityScorer


def test_quality_scorer_is_abstract():
    """QualityScorer cannot be instantiated directly."""
    with pytest.raises(TypeError):
        QualityScorer()  # type: ignore


def test_custom_scorer_requires_score_method():
    """Subclass without score() should still raise TypeError."""

    class IncompleteScorer(QualityScorer):
        name = "incomplete"

    with pytest.raises(TypeError):
        IncompleteScorer()  # type: ignore


def test_custom_scorer_basic():
    """A properly implemented scorer should return a float in [0, 1]."""

    class AlwaysPassScorer(QualityScorer):
        name = "always_pass"

        def score(self, text, context=None):
            return 1.0

    scorer = AlwaysPassScorer()
    assert scorer.score("hello") == 1.0
    assert scorer.name == "always_pass"
