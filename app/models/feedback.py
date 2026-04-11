"""
Request and response models for the feedback endpoint.
"""
from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    evaluation_id: str = Field(
        ...,
        description="The evaluation_id returned by a previous POST /api/v1/evaluate call.",
    )
    correct: bool = Field(
        ...,
        description=(
            "Whether the evaluation result agreed with human judgment. "
            "true = the score/verdict was correct; false = it was wrong."
        ),
    )
    note: str | None = Field(
        None,
        max_length=500,
        description="Optional free-text correction or observation (max 500 chars).",
    )


class FeedbackResponse(BaseModel):
    feedback_id: str
    evaluation_id: str
    correct: bool
    note: str | None
    created_at: str
    message: str
