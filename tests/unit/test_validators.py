"""Unit tests for Pydantic request model validation."""
import pytest
from pydantic import ValidationError

from app.models.request import (
    MAX_BATCH_SIZE,
    MAX_TEXT_LENGTH,
    EvaluateRequest,
    FilterRequest,
    PipelineRunRequest,
    PipelineStepConfig,
)


class TestEvaluateRequest:
    def test_valid_defaults(self):
        req = EvaluateRequest(text="Hello world.")
        assert "coherence" in req.metrics

    def test_valid_custom_metrics(self):
        req = EvaluateRequest(text="Hello.", metrics=["coherence"])
        assert req.metrics == ["coherence"]

    def test_blank_text_raises(self):
        with pytest.raises(ValidationError, match="blank"):
            EvaluateRequest(text="   ")

    def test_text_too_long_raises(self):
        with pytest.raises(ValidationError):
            EvaluateRequest(text="x" * (MAX_TEXT_LENGTH + 1))

    def test_text_exactly_max_length(self):
        req = EvaluateRequest(text="a" * MAX_TEXT_LENGTH, metrics=["fluency"])
        assert len(req.text) == MAX_TEXT_LENGTH

    def test_unknown_metric_raises(self):
        with pytest.raises(ValidationError, match="Unknown metric"):
            EvaluateRequest(text="Valid text.", metrics=["toxicity"])

    def test_empty_metrics_raises(self):
        with pytest.raises(ValidationError, match="empty"):
            EvaluateRequest(text="Valid text.", metrics=[])

    def test_context_defaults_to_none(self):
        assert EvaluateRequest(text="Answer.").context is None

    def test_context_accepted(self):
        req = EvaluateRequest(text="Answer.", context="Question?")
        assert req.context == "Question?"


class TestFilterRequest:
    def test_valid(self):
        req = FilterRequest(texts=["Hello world."], threshold=0.5)
        assert len(req.texts) == 1

    def test_batch_too_large_raises(self):
        with pytest.raises(ValidationError):
            FilterRequest(texts=["text"] * (MAX_BATCH_SIZE + 1))

    def test_batch_exactly_max(self):
        req = FilterRequest(texts=["Valid text."] * MAX_BATCH_SIZE)
        assert len(req.texts) == MAX_BATCH_SIZE

    def test_blank_text_raises(self):
        with pytest.raises(ValidationError, match="blank"):
            FilterRequest(texts=["  "])

    def test_threshold_above_one_raises(self):
        with pytest.raises(ValidationError):
            FilterRequest(texts=["Hello."], threshold=1.5)

    def test_threshold_below_zero_raises(self):
        with pytest.raises(ValidationError):
            FilterRequest(texts=["Hello."], threshold=-0.1)

    def test_threshold_zero_valid(self):
        req = FilterRequest(texts=["Hello."], threshold=0.0)
        assert req.threshold == pytest.approx(0.0)

    def test_threshold_one_valid(self):
        req = FilterRequest(texts=["Hello."], threshold=1.0)
        assert req.threshold == pytest.approx(1.0)

    def test_empty_texts_raises(self):
        with pytest.raises(ValidationError):
            FilterRequest(texts=[])


class TestPipelineRunRequest:
    def _score(self):
        return PipelineStepConfig(type="score", metrics=["coherence"])

    def _filter(self):
        return PipelineStepConfig(type="filter", threshold=0.5)

    def _transform(self):
        return PipelineStepConfig(type="transform", operation="strip")

    def test_valid_score_only(self):
        req = PipelineRunRequest(texts=["Hello."], steps=[self._score()])
        assert len(req.steps) == 1

    def test_valid_score_then_filter(self):
        req = PipelineRunRequest(texts=["Hello."], steps=[self._score(), self._filter()])
        assert len(req.steps) == 2

    def test_valid_all_three_steps(self):
        req = PipelineRunRequest(
            texts=["Hello."],
            steps=[self._score(), self._filter(), self._transform()],
        )
        assert len(req.steps) == 3

    def test_filter_before_score_raises(self):
        with pytest.raises(ValidationError, match="filter"):
            PipelineRunRequest(texts=["Hello."], steps=[self._filter(), self._score()])

    def test_empty_steps_raises(self):
        with pytest.raises(ValidationError):
            PipelineRunRequest(texts=["Hello."], steps=[])

    def test_blank_text_raises(self):
        with pytest.raises(ValidationError):
            PipelineRunRequest(texts=["  "], steps=[self._score()])
