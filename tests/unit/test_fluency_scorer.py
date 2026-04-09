import pytest
from app.scorers.fluency import FluencyScorer

scorer = FluencyScorer()


def test_empty_text_returns_zero():
    assert scorer.score("") == 0.0


def test_whitespace_only_returns_zero():
    assert scorer.score("   ") == 0.0


def test_good_text_scores_above_half():
    text = (
        "The model generated a high-quality response. "
        "It was coherent and relevant to the given prompt."
    )
    assert scorer.score(text) >= 0.5


def test_repetitive_text_penalised():
    repetitive = "the dog the dog the dog the dog the dog the dog"
    normal = "The dog ran across the field and jumped over the fence."
    assert scorer.score(repetitive) < scorer.score(normal)


def test_no_capitalisation_scores_lower():
    lower = "this sentence starts with a lowercase letter."
    upper = "This sentence starts with an uppercase letter."
    assert scorer.score(lower) < scorer.score(upper)


def test_incomplete_sentences_score_lower():
    incomplete = "Running fast through the park and then"
    complete = "She ran fast through the park and then stopped."
    assert scorer.score(incomplete) <= scorer.score(complete)
