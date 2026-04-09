"""Focused unit tests for FluencyScorer heuristic signals."""
import pytest

from app.scorers.fluency import FluencyScorer


@pytest.fixture
def scorer():
    return FluencyScorer()


def test_complete_sentence_score(scorer):
    score = scorer.score("The model produces coherent, fluent text.")
    assert 0.0 <= score <= 1.0


def test_empty_text_returns_zero(scorer):
    assert scorer.score("") == pytest.approx(0.0)


def test_whitespace_only_returns_zero(scorer):
    assert scorer.score("   ") == pytest.approx(0.0)


def test_diverse_vocab_scores_higher_than_repetitive(scorer):
    diverse = scorer.score(
        "The neural network processes diverse inputs and generates varied outputs."
    )
    repetitive = scorer.score("cat cat cat cat cat cat cat cat cat cat cat cat")
    assert diverse > repetitive


def test_upper_case_start_boosts_score(scorer):
    upper = scorer.score("This sentence starts correctly.")
    lower = scorer.score("this sentence does not start correctly.")
    assert upper > lower


def test_terminal_punctuation_presence(scorer):
    with_punct = scorer.score("This is a complete sentence.")
    without_punct = scorer.score("This is an incomplete sentence")
    assert with_punct >= without_punct


def test_long_text_in_range(scorer):
    text = " ".join(["This is a sample generated sentence."] * 20)
    assert 0.0 <= scorer.score(text) <= 1.0


def test_weight_attribute(scorer):
    assert scorer.weight == pytest.approx(1.0)
