"""
Request models for all API endpoints.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── /evaluate ──────────────────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The AI-generated text to evaluate.")
    context: Optional[str] = Field(None, description="Original prompt or source context (used by relevance scorer).")
    metrics: list[str] = Field(
        default=["coherence", "relevance", "fluency"],
        description="Quality metrics to compute.",
    )


# ── /filter ────────────────────────────────────────────────────────────────

class FilterRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, description="Batch of AI-generated texts to filter.")
    context: Optional[str] = Field(None, description="Shared prompt/context for all texts.")
    metrics: list[str] = Field(
        default=["coherence", "relevance", "fluency"],
        description="Metrics used to compute the aggregate quality score.",
    )
    threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Texts with overall score below this value are filtered out.",
    )


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
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Quality threshold (used by filter step).",
    )
    operation: Optional[Literal["strip", "lowercase", "truncate"]] = Field(
        None, description="Text operation (used by transform step)."
    )
    max_chars: Optional[int] = Field(
        None, gt=0, description="Max character length (used by transform/truncate)."
    )


class PipelineRunRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, description="Input texts to process.")
    context: Optional[str] = Field(None, description="Shared prompt/context for all texts.")
    steps: list[PipelineStepConfig] = Field(
        ..., min_length=1, description="Ordered list of pipeline steps to execute."
    )
