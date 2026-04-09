"""
Pydantic models for the /providers endpoints.
"""
from typing import Literal, Optional

from pydantic import BaseModel, field_validator

from app.models.request import MAX_TEXT_LENGTH, _validate_text, _validate_metrics


class ProviderEvaluateRequest(BaseModel):
    """Request body for POST /api/v1/providers/evaluate."""
    text: str
    context: Optional[str] = None
    provider: Literal["openai", "anthropic", "huggingface", "mock"] = "openai"
    model: Optional[str] = None
    criteria: list[str] = ["coherence", "relevance", "fluency"]

    @field_validator("text")
    @classmethod
    def text_valid(cls, v: str) -> str:
        return _validate_text(v, "text")

    @field_validator("criteria")
    @classmethod
    def criteria_known(cls, v: list[str]) -> list[str]:
        return _validate_metrics(v)


class ProviderInfo(BaseModel):
    """Single provider status entry."""
    provider: str
    default_model: str
    available: bool


class ProvidersListResponse(BaseModel):
    """Response for GET /api/v1/providers."""
    providers: list[ProviderInfo]


class ProviderEvaluateResponse(BaseModel):
    """Response for POST /api/v1/providers/evaluate."""
    provider: str
    model: str
    scores: dict[str, float]
    overall: float
    reasoning: str
    latency_ms: float
