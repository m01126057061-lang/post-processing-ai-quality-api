"""
Request models with field-level validation for all API endpoints.

Validation rules applied via @field_validator:
  - text / texts items: non-blank, max MAX_TEXT_LENGTH chars
  - texts batch: max MAX_BATCH_SIZE items
  - metrics: non-empty, all values must be registered scorer names
  - pipeline steps: filter must be preceded by at least one score step
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

MAX_TEXT_LENGTH = 10_000   # characters per text item
MAX_BATCH_SIZE = 100       # items per batch request


def _validate_text(value: str, field_label: str = "text") -> str:
    """Shared single-text validation logic."""
    if not value.strip():
        raise ValueError(f"{field_label} must not be blank")
    if len(value) > MAX_TEXT_LENGTH:
        raise ValueError(
            f"{field_label} exceeds maximum length of {MAX_TEXT_LENGTH} characters "
            f"(got {len(value)})"
        )
    return value


def _validate_metrics(values: list[str]) -> list[str]:
    """Shared metrics validation logic — checks against the scorer registry."""
    from app.scorers.registry import available_metrics  # lazy import avoids circular deps
    if not values:
        raise ValueError("metrics list must not be empty")
    known = set(available_metrics())
    unknown = [m for m in values if m not in known]
    if unknown:
        raise ValueError(
            f"Unknown metric(s): {unknown}. Available: {sorted(known)}"
        )
    return values


# ── /evaluate ──────────────────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The AI-generated text to evaluate.")
    context: Optional[str] = Field(None, description="Original prompt/context (used by relevance scorer).")
    metrics: list[str] = Field(
        default=["coherence", "relevance", "fluency"],
        description="Quality metrics to compute.",
    )

    @field_validator("text")
    @classmethod
    def text_valid(cls, v: str) -> str:
        return _validate_text(v, "text")

    @field_validator("metrics")
    @classmethod
    def metrics_known(cls, v: list[str]) -> list[str]:
        return _validate_metrics(v)


# ── /filter ────────────────────────────────────────────────────────────────

class FilterRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, description="Batch of AI-generated texts to filter.")
    context: Optional[str] = Field(None, description="Shared prompt/context for all texts.")
    metrics: list[str] = Field(
        default=["coherence", "relevance", "fluency"],
        description="Metrics used to compute the aggregate quality score.",
    )
    threshold: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Texts with overall score below this value are filtered out.",
    )

    @field_validator("texts")
    @classmethod
    def texts_valid(cls, v: list[str]) -> list[str]:
        if len(v) > MAX_BATCH_SIZE:
            raise ValueError(
                f"Batch size {len(v)} exceeds maximum of {MAX_BATCH_SIZE}"
            )
        for i, text in enumerate(v):
            _validate_text(text, f"texts[{i}]")
        return v

    @field_validator("metrics")
    @classmethod
    def metrics_known(cls, v: list[str]) -> list[str]:
        return _validate_metrics(v)


# ── /pipeline/run ──────────────────────────────────────────────────────────

class PipelineStepConfig(BaseModel):
    """Configuration for a single step in a pipeline."""
    type: Literal["score", "filter", "transform"] = Field(
        ..., description="Step type: score | filter | transform"
    )
    metrics: list[str] = Field(
        default=["coherence", "relevance", "fluency"],
        description="Metrics to evaluate (used by score step).",
    )
    threshold: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Quality threshold (used by filter step).",
    )
    operation: Optional[Literal["strip", "lowercase", "truncate"]] = Field(
        None, description="Text operation (used by transform step)."
    )
    max_chars: Optional[int] = Field(
        None, gt=0, description="Max character length for truncate operation."
    )

    @field_validator("metrics")
    @classmethod
    def metrics_known(cls, v: list[str]) -> list[str]:
        return _validate_metrics(v)


class PipelineRunRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, description="Input texts to process.")
    context: Optional[str] = Field(None, description="Shared prompt/context for all texts.")
    steps: list[PipelineStepConfig] = Field(
        ..., min_length=1, description="Ordered list of pipeline steps to execute."
    )

    @field_validator("texts")
    @classmethod
    def texts_valid(cls, v: list[str]) -> list[str]:
        if len(v) > MAX_BATCH_SIZE:
            raise ValueError(f"Batch size {len(v)} exceeds maximum of {MAX_BATCH_SIZE}")
        for i, text in enumerate(v):
            _validate_text(text, f"texts[{i}]")
        return v

    @model_validator(mode="after")
    def filter_requires_prior_score(self) -> "PipelineRunRequest":
        """A filter step must be preceded by at least one score step (otherwise overall=0.0)."""
        seen_score = False
        for i, step in enumerate(self.steps):
            if step.type == "score":
                seen_score = True
            elif step.type == "filter" and not seen_score:
                raise ValueError(
                    f"steps[{i}]: 'filter' step has no preceding 'score' step — "
                    "all items would have overall=0.0 and be filtered. "
                    "Add a 'score' step before 'filter'."
                )
        return self
