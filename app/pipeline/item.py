"""
PipelineItem — internal mutable state carrier for a single text as it moves through pipeline steps.
Not exposed in API responses directly; converted to PipelineTextResult at the end.
"""
from dataclasses import dataclass, field


@dataclass
class PipelineItem:
    text: str
    scores: dict[str, float] = field(default_factory=dict)
    overall: float = 0.0
    filtered: bool = False
    filter_reason: str = ""
    step_outputs: list[dict] = field(default_factory=list)
