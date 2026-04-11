from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.db.repository import save_evaluation
from app.models.request import EvaluateRequest
from app.models.response import EvaluateResponse, ScoreResult
from app.scorers.registry import get_scorer

router = APIRouter()


@router.post("/evaluate", response_model=EvaluateResponse, summary="Evaluate AI output quality")
async def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    """
    Score an AI-generated text across one or more quality metrics.

    - **text**: the AI-generated output to evaluate
    - **context**: optional original prompt (required for relevance / hallucination scoring)
    - **metrics**: list of metric names (coherence, relevance, fluency, toxicity, hallucination)

    The response includes:
    - **evaluation_id**: unique ID for this record — use it with POST /feedback
    - **scores**: overall aggregate + per-metric breakdown
    - **passed**: true when overall >= DEFAULT_QUALITY_THRESHOLD (default 0.7)
    - **explanations**: human-readable description of each metric score
    """
    scorers: dict = {}
    scores: dict[str, float] = {}

    for metric in request.metrics:
        try:
            scorer = get_scorer(metric)
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        scorers[metric] = scorer
        scores[metric] = scorer.score(request.text, request.context)

    if not scores:
        raise HTTPException(status_code=400, detail="No metrics were evaluated.")

    overall = round(sum(scores.values()) / len(scores), 4)
    rounded_scores = {k: round(v, 4) for k, v in scores.items()}

    # Persist to audit trail (returns None when AUDIT_ENABLED=false)
    evaluation_id = await save_evaluation(
        text=request.text,
        metrics=list(scores.keys()),
        scores=rounded_scores,
        weighted_score=overall,
        context_provided=request.context is not None,
    )

    # Human-readable per-metric explanations
    explanations = {
        metric: scorers[metric].explain(scores[metric])
        for metric in scores
    }

    return EvaluateResponse(
        evaluation_id=evaluation_id,
        text=request.text,
        scores=ScoreResult(overall=overall, breakdown=rounded_scores),
        passed=overall >= settings.default_quality_threshold,
        explanations=explanations,
    )
