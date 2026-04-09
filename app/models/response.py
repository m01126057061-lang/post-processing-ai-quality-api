from pydantic import BaseModel
from typing import Dict, Optional, Any


class ScoreResult(BaseModel):
    overall: float
    breakdown: Dict[str, float]


class EvaluateResponse(BaseModel):
    text: str
    scores: ScoreResult
    passed: bool


class FilterResponse(BaseModel):
    text: Optional[str]
    passed: bool
    score: float


class PipelineRunResponse(BaseModel):
    output: Any
    steps_completed: int
    passed: bool
