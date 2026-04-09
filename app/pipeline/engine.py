"""
Pipeline engine: build concrete steps from config objects, run them in order,
and package results into a PipelineRunResponse.
"""

from app.models.request import PipelineStepConfig
from app.models.response import (
    PipelineRunResponse,
    PipelineSummary,
    PipelineTextResult,
    ScoreResult,
)
from app.pipeline.item import PipelineItem
from app.pipeline.steps.filter_step import FilterStep
from app.pipeline.steps.score_step import ScoreStep
from app.pipeline.steps.transform_step import TransformStep


def build_step(config: PipelineStepConfig):
    """Instantiate the concrete step class for a given PipelineStepConfig."""
    if config.type == "score":
        return ScoreStep(metrics=config.metrics)
    if config.type == "filter":
        return FilterStep(threshold=config.threshold)
    if config.type == "transform":
        return TransformStep(
            operation=config.operation or "strip",
            max_chars=config.max_chars,
        )
    raise ValueError(f"Unknown pipeline step type: {config.type!r}")


def run_pipeline(
    texts: list[str],
    context: str | None,
    steps: list[PipelineStepConfig],
) -> PipelineRunResponse:
    """Execute a list of pipeline steps over all input texts and return the full result."""
    items: list[PipelineItem] = [PipelineItem(text=t) for t in texts]
    built = [build_step(s) for s in steps]

    for step in built:
        items = step.run(items, context)

    results = [
        PipelineTextResult(
            text=item.text,
            scores=ScoreResult(
                overall=item.overall,
                breakdown={k: round(v, 4) for k, v in item.scores.items()},
            ),
            filtered=item.filtered,
            filter_reason=item.filter_reason or None,
            step_outputs=item.step_outputs,
        )
        for item in items
    ]

    passed = sum(1 for r in results if not r.filtered)
    total = len(results)

    return PipelineRunResponse(
        results=results,
        summary=PipelineSummary(
            total=total,
            passed=passed,
            filtered=total - passed,
            pass_rate=round(passed / total, 4) if total else 0.0,
            steps_run=len(built),
        ),
    )
