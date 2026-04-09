"""
FilterStep — marks items as filtered when their overall score falls below a threshold.

Items already filtered by a prior step are skipped.
"""
from typing import Optional

from app.pipeline.item import PipelineItem


class FilterStep:
    name = "filter"

    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    def run(self, items: list[PipelineItem], context: Optional[str] = None) -> list[PipelineItem]:
        for item in items:
            if item.filtered:
                continue
            passed = item.overall >= self.threshold
            if not passed:
                item.filtered = True
                item.filter_reason = (
                    f"overall score {item.overall:.4f} below threshold {self.threshold:.2f}"
                )
            item.step_outputs.append({
                "step": "filter",
                "threshold": self.threshold,
                "passed": passed,
            })
        return items
