from fastapi import APIRouter
from app.models.request import FilterRequest
from app.models.response import FilterResponse

router = APIRouter()


@router.post("/filter", response_model=FilterResponse)
def filter_output(request: FilterRequest) -> FilterResponse:
    """
    Return the text only if it meets the quality threshold.
    TODO: wire up pipeline scoring.
    """
    score = 0.0
    passed = score >= request.threshold
    return FilterResponse(
        text=request.text if passed else None,
        passed=passed,
        score=score,
    )
