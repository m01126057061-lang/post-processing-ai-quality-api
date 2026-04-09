"""
TransformStep — basic text transformations applied to non-filtered items.

Supported operations:
  - strip     : trim leading/trailing whitespace (default)
  - lowercase : convert to lowercase
  - truncate  : trim to max_chars characters
"""

from app.pipeline.item import PipelineItem


class TransformStep:
    name = "transform"

    def __init__(self, operation: str = "strip", max_chars: int | None = None) -> None:
        self.operation = operation
        self.max_chars = max_chars

    def run(self, items: list[PipelineItem], context: str | None = None) -> list[PipelineItem]:
        for item in items:
            if item.filtered:
                continue
            original = item.text
            if self.operation == "strip":
                item.text = item.text.strip()
            elif self.operation == "lowercase":
                item.text = item.text.lower()
            elif self.operation == "truncate" and self.max_chars:
                item.text = item.text[: self.max_chars]
            item.step_outputs.append({
                "step": "transform",
                "operation": self.operation,
                "changed": item.text != original,
            })
        return items
