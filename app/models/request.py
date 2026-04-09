from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class EvaluateRequest(BaseModel):
    text: str = Field(..., description="AI-generated text to evaluate")
    context: Optional[str] = Field(None, description="Original prompt or context for relevance scoring")
    metrics: List[str] = Field(
        default=["coherence", "relevance", "fluency"],
        description="Quality metrics to compute",
    )


class FilterRequest(BaseModel):
    text: str = Field(..., description="AI-generated text to evaluate and filter")
    threshold: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description="Minimum overall quality score required to pass",
    )
    context: Optional[str] = Field(None, description="Original prompt or context")


class PipelineRunRequest(BaseModel):
    text: str = Field(..., description="Input text to process through the pipeline")
    pipeline_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional pipeline configuration override (steps, thresholds, etc.)",
    )
