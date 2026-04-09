from fastapi import APIRouter
from app.models.request import EvaluateRequest
from app.models.response import EvaluateResponse, ScoreResult

router = APIRouter()


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    """
    Score and evaluate an AI-generated output across quality metrics.
    TODO: wire up QualityScorer implementations.
    """
    placeholder_scores = {m: 0.0 for m in request.metrics}
    scores = ScoreResult(overall=0.0, breakdown=placeholder_scores)
    return EvaluateResponse(text=request.text, scores=scores, passed=False)
