"""Unit tests for the pipeline engine: build_step factory and run_pipeline."""
import pytest

from app.models.request import PipelineStepConfig
from app.pipeline.engine import build_step, run_pipeline
from app.pipeline.item import PipelineItem
from app.pipeline.steps.filter_step import FilterStep
from app.pipeline.steps.score_step import ScoreStep
from app.pipeline.steps.transform_step import TransformStep

# ── build_step ────────────────────────────────────────────────────────────────

def test_build_score_step():
    assert isinstance(build_step(PipelineStepConfig(type="score", metrics=["coherence"])), ScoreStep)


def test_build_filter_step():
    assert isinstance(build_step(PipelineStepConfig(type="filter", threshold=0.5)), FilterStep)


def test_build_transform_step():
    assert isinstance(build_step(PipelineStepConfig(type="transform", operation="strip")), TransformStep)


def test_build_unknown_raises():
    with pytest.raises(ValueError, match="Unknown pipeline step type"):
        build_step(PipelineStepConfig(type="unknown"))


# ── ScoreStep ──────────────────────────────────────────────────────────────────

def test_score_step_adds_scores():
    step = ScoreStep(metrics=["coherence"])
    items = [PipelineItem(text="Hello world.")]
    result = step.run(items, context=None)
    assert "coherence" in result[0].scores


def test_score_step_multiple_metrics():
    step = ScoreStep(metrics=["coherence", "fluency"])
    items = [PipelineItem(text="Test.")]
    result = step.run(items, context=None)
    assert set(result[0].scores.keys()) >= {"coherence", "fluency"}


def test_score_step_scores_in_range():
    step = ScoreStep(metrics=["fluency"])
    items = [PipelineItem(text="Hello."), PipelineItem(text="World.")]
    result = step.run(items, context=None)
    for item in result:
        assert 0.0 <= item.scores["fluency"] <= 1.0


def test_score_step_sets_overall():
    step = ScoreStep(metrics=["fluency"])
    items = [PipelineItem(text="Hello world.")]
    result = step.run(items, context=None)
    assert result[0].overall >= 0.0


# ── FilterStep ────────────────────────────────────────────────────────────────

def test_filter_marks_low_score():
    step = FilterStep(threshold=0.99)
    items = [PipelineItem(text="Low.", scores={"coherence": 0.1}, overall=0.1)]
    result = step.run(items)
    assert result[0].filtered is True


def test_filter_keeps_high_score():
    step = FilterStep(threshold=0.0)
    items = [PipelineItem(text="High.", scores={"coherence": 0.9}, overall=0.9)]
    result = step.run(items)
    assert result[0].filtered is False


def test_filter_preserves_all_items():
    """FilterStep must keep all items — both passed and filtered."""
    step = FilterStep(threshold=0.8)
    items = [
        PipelineItem(text="Pass.", overall=0.9),
        PipelineItem(text="Fail.", overall=0.1),
    ]
    assert len(step.run(items)) == 2


def test_filter_already_filtered_item_not_re_evaluated():
    """Items already filtered by a prior step should remain filtered."""
    step = FilterStep(threshold=0.0)  # threshold so low everything should pass
    items = [PipelineItem(text="Hi.", overall=0.9, filtered=True)]
    result = step.run(items)
    assert result[0].filtered is True  # stays True


def test_filter_sets_reason():
    step = FilterStep(threshold=0.9)
    items = [PipelineItem(text="Low.", overall=0.1)]
    result = step.run(items)
    assert result[0].filter_reason != ""


# ── TransformStep ──────────────────────────────────────────────────────────────

def test_transform_strip():
    step = TransformStep(operation="strip")
    items = [PipelineItem(text="  hello  ")]
    assert step.run(items)[0].text == "hello"


def test_transform_lowercase():
    step = TransformStep(operation="lowercase")
    items = [PipelineItem(text="HELLO WORLD")]
    assert step.run(items)[0].text == "hello world"


def test_transform_truncate():
    step = TransformStep(operation="truncate", max_chars=5)
    items = [PipelineItem(text="Hello World")]
    assert len(step.run(items)[0].text) <= 5


# ── run_pipeline ───────────────────────────────────────────────────────────────

def test_run_pipeline_score_only():
    steps = [PipelineStepConfig(type="score", metrics=["coherence"])]
    resp = run_pipeline(["Hello world."], context=None, steps=steps)
    assert resp.summary.total == 1
    assert resp.summary.passed == 1


def test_run_pipeline_score_filter_all_pass():
    steps = [
        PipelineStepConfig(type="score", metrics=["coherence"]),
        PipelineStepConfig(type="filter", threshold=0.0),
    ]
    resp = run_pipeline(["Hello world."], context=None, steps=steps)
    assert resp.summary.passed == 1
    assert resp.summary.filtered == 0


def test_run_pipeline_multiple_inputs():
    steps = [PipelineStepConfig(type="score", metrics=["fluency"])]
    resp = run_pipeline(["A.", "B.", "C."], context=None, steps=steps)
    assert resp.summary.total == 3


def test_run_pipeline_transform():
    steps = [PipelineStepConfig(type="transform", operation="strip")]
    resp = run_pipeline(["  hello  "], context=None, steps=steps)
    assert resp.results[0].text == "hello"


def test_run_pipeline_steps_run_count():
    steps = [
        PipelineStepConfig(type="score", metrics=["coherence"]),
        PipelineStepConfig(type="filter", threshold=0.0),
    ]
    resp = run_pipeline(["Hello."], context=None, steps=steps)
    assert resp.summary.steps_run == 2


def test_run_pipeline_pass_rate_all_pass():
    steps = [
        PipelineStepConfig(type="score", metrics=["coherence"]),
        PipelineStepConfig(type="filter", threshold=0.0),
    ]
    resp = run_pipeline(["A.", "B.", "C.", "D."], context=None, steps=steps)
    assert resp.summary.pass_rate == pytest.approx(1.0)


def test_run_pipeline_results_have_step_outputs():
    steps = [PipelineStepConfig(type="score", metrics=["coherence"])]
    resp = run_pipeline(["Hello."], context=None, steps=steps)
    assert isinstance(resp.results[0].step_outputs, list)
