from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.models.request import EvaluateRequest
from app.models.response import EvaluateResponse, ScoreResult
from app.scorers.registry import get_scorer

router = APIRouter()


@router.post("/evaluate", response_model=EvaluateResponse, summary="Evaluate AI output quality")
def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    """
    Score an AI-generated text across one or more quality metrics.

    - **text**: the AI-generated output to evaluate
    - **context**: optional original prompt (required for relevance scoring)
    - **metrics**: list of metric names (coherence, relevance, fluency)
    """
    scores: dict[str, float] = {}
    for metric in request.metrics:
        try:
            scorer = get_scorer(metric)
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        scores[metric] = scorer.score(request.text, request.context)

    if not scores:
        raise HTTPException(status_code=400, detail="No metrics were evaluated.")

    overall = round(sum(scores.values()) / len(scores), 4)
    return EvaluateResponse(
        text=request.text,
        scores=ScoreResult(
            overall=overall,
            breakdown={k: round(v, 4) for k, v in scores.items()},
        ),
        passed=overall >= settings.default_quality_threshold,
    )
