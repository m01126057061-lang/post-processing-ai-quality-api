"""
Unit tests for the pipeline engine and its individual steps.
Only FluencyScorer is used here — no network/model calls required.
"""
import pytest

from app.pipeline.item import PipelineItem
from app.pipeline.steps.filter_step import FilterStep
from app.pipeline.steps.score_step import ScoreStep
from app.pipeline.steps.transform_step import TransformStep
from app.pipeline.engine import run_pipeline
from app.models.request import PipelineStepConfig


# ── TransformStep ──────────────────────────────────────────────────────────

def test_transform_strip():
    items = [PipelineItem(text="  hello world  ")]
    result = TransformStep(operation="strip").run(items)
    assert result[0].text == "hello world"


def test_transform_lowercase():
    items = [PipelineItem(text="Hello World")]
    result = TransformStep(operation="lowercase").run(items)
    assert result[0].text == "hello world"


def test_transform_truncate():
    items = [PipelineItem(text="Hello World")]
    result = TransformStep(operation="truncate", max_chars=5).run(items)
    assert result[0].text == "Hello"


def test_transform_skips_filtered_items():
    item = PipelineItem(text="  some text  ", filtered=True, filter_reason="below threshold")
    result = TransformStep(operation="strip").run([item])
    assert result[0].text == "  some text  "  # unchanged


# ── FilterStep ─────────────────────────────────────────────────────────────

def test_filter_marks_item_below_threshold():
    item = PipelineItem(text="bad", overall=0.3)
    result = FilterStep(threshold=0.5).run([item])
    assert result[0].filtered is True
    assert "0.3" in result[0].filter_reason


def test_filter_passes_item_above_threshold():
    item = PipelineItem(text="good", overall=0.8)
    result = FilterStep(threshold=0.5).run([item])
    assert result[0].filtered is False


def test_filter_skips_already_filtered():
    item = PipelineItem(text="already gone", overall=0.9, filtered=True, filter_reason="prior step")
    result = FilterStep(threshold=0.5).run([item])
    assert result[0].filtered is True
    assert result[0].filter_reason == "prior step"  # reason unchanged


# ── ScoreStep ──────────────────────────────────────────────────────────────

def test_score_step_fluency_only():
    """Fluency scorer is heuristic — safe to run in unit tests without ML models."""
    items = [PipelineItem(text="The model produced a clear and complete response.")]
    result = ScoreStep(metrics=["fluency"]).run(items)
    assert "fluency" in result[0].scores
    assert 0.0 <= result[0].overall <= 1.0


def test_score_step_unknown_metric_raises():
    with pytest.raises(KeyError):
        ScoreStep(metrics=["nonexistent"])


# ── Engine integration ─────────────────────────────────────────────────────

def test_pipeline_score_then_filter():
    config = [
        PipelineStepConfig(type="score", metrics=["fluency"]),
        PipelineStepConfig(type="filter", threshold=0.9),
    ]
    # Short, lower-quality text should typically score below 0.9 and be filtered
    resp = run_pipeline(["ok"], context=None, steps=config)
    assert resp.summary.total == 1
    assert resp.summary.steps_run == 2
    assert isinstance(resp.results[0].filtered, bool)


def test_pipeline_transform_only():
    config = [PipelineStepConfig(type="transform", operation="uppercase")]
    # "uppercase" is not a valid operation — transform step ignores unknowns
    resp = run_pipeline(["  hello  "], context=None, steps=config)
    # No crash; text may be unchanged since "uppercase" is not handled
    assert resp.summary.total == 1
