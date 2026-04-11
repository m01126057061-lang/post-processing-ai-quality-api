"""
Response models for all API endpoints.
"""

from pydantic import BaseModel

# ── Shared ─────────────────────────────────────────────────────────────────

class ScoreResult(BaseModel):
    overall: float
    breakdown: dict[str, float]


# ── /evaluate ──────────────────────────────────────────────────────────────

class EvaluateResponse(BaseModel):
    evaluation_id: str | None = None
    text: str
    scores: ScoreResult
    passed: bool
    explanations: dict[str, str] | None = None


# ── /filter ────────────────────────────────────────────────────────────────

class FilterItem(BaseModel):
    text: str
    scores: ScoreResult
    filtered: bool
    filter_reason: str | None = None


class FilterSummary(BaseModel):
    total: int
    passed: int
    filtered: int
    pass_rate: float


class FilterResponse(BaseModel):
    results: list[FilterItem]
    summary: FilterSummary


# ── /pipeline/run ──────────────────────────────────────────────────────────

class PipelineTextResult(BaseModel):
    text: str
    scores: ScoreResult
    filtered: bool
    filter_reason: str | None = None
    step_outputs: list[dict]


class PipelineSummary(BaseModel):
    total: int
    passed: int
    filtered: int
    pass_rate: float
    steps_run: int


class PipelineRunResponse(BaseModel):
    results: list[PipelineTextResult]
    summary: PipelineSummary
