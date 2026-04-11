"""
POST /api/v1/feedback — submit human feedback on a past evaluation.

Feedback links back to an evaluation_id returned by /evaluate and records
whether the automated score agreed with human judgment.  Stored records form
the basis for future per-metric threshold recalibration.
"""
from fastapi import APIRouter, HTTPException

from app.db.repository import save_feedback
from app.models.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter()


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit feedback on a past evaluation",
    description=(
        "Mark a previous /evaluate result as correct or incorrect. "
        "Requires the evaluation_id from the /evaluate response. "
        "Stored feedback will be used for future scorer recalibration."
    ),
    tags=["feedback"],
)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    result = await save_feedback(
        evaluation_id=request.evaluation_id,
        correct=request.correct,
        note=request.note,
    )
    if result is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Audit trail is disabled (AUDIT_ENABLED=false). "
                "Feedback requires the audit trail to be enabled."
            ),
        )
    return FeedbackResponse(
        feedback_id=result["feedback_id"],
        evaluation_id=request.evaluation_id,
        correct=request.correct,
        note=request.note,
        created_at=result["created_at"],
        message="Feedback recorded — thank you. This will help improve scorer calibration.",
    )
