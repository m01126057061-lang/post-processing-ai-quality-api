"""
ScoreStep — evaluates quality metrics for each non-filtered PipelineItem.

Metrics are validated eagerly at construction time (fail fast if unknown).
"""

from app.pipeline.item import PipelineItem
from app.scorers.registry import get_scorer


class ScoreStep:
    name = "score"

    def __init__(self, metrics: list[str]) -> None:
        # Validate at build time — raises KeyError for unknown metrics
        for m in metrics:
            get_scorer(m)
        self.metrics = metrics

    def run(self, items: list[PipelineItem], context: str | None = None) -> list[PipelineItem]:
        for item in items:
            if item.filtered:
                continue
            for metric in self.metrics:
                item.scores[metric] = get_scorer(metric).score(item.text, context)
            if item.scores:
                item.overall = round(sum(item.scores.values()) / len(item.scores), 4)
            item.step_outputs.append({
                "step": "score",
                "metrics": list(self.metrics),
                "scores": dict(item.scores),
                "overall": item.overall,
            })
        return items
