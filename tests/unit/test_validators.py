"""Unit tests for request model validators."""
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


# ── EvaluateRequest ────────────────────────────────────────────────────────

def test_evaluate_blank_text_rejected():
    with pytest.raises(ValidationError, match="must not be blank"):
        EvaluateRequest(text="   ")


def test_evaluate_text_too_long_rejected():
    with pytest.raises(ValidationError, match="exceeds maximum length"):
        EvaluateRequest(text="x" * (MAX_TEXT_LENGTH + 1))


def test_evaluate_unknown_metric_rejected():
    with pytest.raises(ValidationError, match="Unknown metric"):
        EvaluateRequest(text="hello", metrics=["made_up"])


def test_evaluate_empty_metrics_rejected():
    with pytest.raises(ValidationError, match="must not be empty"):
        EvaluateRequest(text="hello", metrics=[])


def test_evaluate_valid_request_passes():
    req = EvaluateRequest(text="A proper sentence.", metrics=["fluency"])
    assert req.text == "A proper sentence."


# ── FilterRequest ──────────────────────────────────────────────────────────

def test_filter_batch_too_large_rejected():
    with pytest.raises(ValidationError, match="exceeds maximum"):
        FilterRequest(texts=["x"] * (MAX_BATCH_SIZE + 1))


def test_filter_blank_item_rejected():
    with pytest.raises(ValidationError, match="must not be blank"):
        FilterRequest(texts=["good text", "  "])


def test_filter_unknown_metric_rejected():
    with pytest.raises(ValidationError, match="Unknown metric"):
        FilterRequest(texts=["hello"], metrics=["nonexistent"])


# ── PipelineRunRequest ─────────────────────────────────────────────────────

def test_pipeline_filter_before_score_rejected():
    with pytest.raises(ValidationError, match="no preceding .score. step"):
        PipelineRunRequest(
            texts=["hello"],
            steps=[
                PipelineStepConfig(type="filter", threshold=0.5),
            ],
        )


def test_pipeline_filter_after_score_valid():
    req = PipelineRunRequest(
        texts=["Hello world."],
        steps=[
            PipelineStepConfig(type="score", metrics=["fluency"]),
            PipelineStepConfig(type="filter", threshold=0.5),
        ],
    )
    assert len(req.steps) == 2


def test_pipeline_transform_only_no_score_required():
    req = PipelineRunRequest(
        texts=["  hello  "],
        steps=[PipelineStepConfig(type="transform", operation="strip")],
    )
    assert req.steps[0].type == "transform"
