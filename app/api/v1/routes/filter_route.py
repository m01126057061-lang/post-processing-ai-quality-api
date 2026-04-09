from fastapi import APIRouter, HTTPException

from app.models.request import FilterRequest
from app.models.response import FilterItem, FilterResponse, FilterSummary, ScoreResult
from app.scorers.registry import get_scorer

router = APIRouter()


@router.post("/filter", response_model=FilterResponse, summary="Filter AI outputs by quality threshold")
def filter_texts(request: FilterRequest) -> FilterResponse:
    """
    Score each text across the requested metrics and return a pass/fail split.

    - **texts**: batch of AI-generated outputs
    - **context**: optional shared prompt (improves relevance scoring)
    - **metrics**: quality metrics to compute
    - **threshold**: texts scoring below this are marked `filtered: true`
    """
    threshold = request.threshold

    # Validate all metrics up front before processing any text
    scorers = {}
    for metric in request.metrics:
        try:
            scorers[metric] = get_scorer(metric)
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    results: list[FilterItem] = []
    for text in request.texts:
        raw_scores = {m: s.score(text, request.context) for m, s in scorers.items()}
        overall = round(sum(raw_scores.values()) / len(raw_scores), 4) if raw_scores else 0.0
        filtered = overall < threshold
        results.append(
            FilterItem(
                text=text,
                scores=ScoreResult(
                    overall=overall,
                    breakdown={k: round(v, 4) for k, v in raw_scores.items()},
                ),
                filtered=filtered,
                filter_reason=(
                    f"overall score {overall:.4f} below threshold {threshold:.2f}"
                    if filtered
                    else None
                ),
            )
        )

    passed = sum(1 for r in results if not r.filtered)
    total = len(results)
    return FilterResponse(
        results=results,
        summary=FilterSummary(
            total=total,
            passed=passed,
            filtered=total - passed,
            pass_rate=round(passed / total, 4) if total else 0.0,
        ),
    )
