"""
Provider evaluation endpoints.

GET  /api/v1/providers               — list all registered providers and their status
POST /api/v1/providers/evaluate      — LLM-based quality evaluation using a chosen provider
"""
import time
from typing import Annotated

from fastapi import APIRouter

from app.adapters.registry import get_adapter, list_providers
from app.models.provider_models import (
    ProviderEvaluateRequest,
    ProviderEvaluateResponse,
    ProviderInfo,
    ProvidersListResponse,
)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get(
    "",
    response_model=ProvidersListResponse,
    summary="List all registered model providers",
    description=(
        "Returns every registered model provider adapter along with its "
        "default model and whether it is currently available (API key configured)."
    ),
)
def get_providers() -> ProvidersListResponse:
    raw = list_providers()
    providers = [ProviderInfo(**p) for p in raw]
    return ProvidersListResponse(providers=providers)


@router.post(
    "/evaluate",
    response_model=ProviderEvaluateResponse,
    summary="LLM-based quality evaluation",
    description=(
        "Use a configured model provider to evaluate the quality of AI-generated text "
        "on one or more criteria. Returns per-criterion scores, an overall aggregate, "
        "and the model's reasoning."
    ),
)
async def provider_evaluate(
    req: ProviderEvaluateRequest,
) -> ProviderEvaluateResponse:
    adapter = get_adapter(req.provider)

    t0 = time.monotonic()
    scores, reasoning = await adapter.score_quality(
        text=req.text,
        context=req.context,
        criteria=req.criteria,
        model=req.model,
    )
    latency_ms = round((time.monotonic() - t0) * 1000, 1)

    overall = round(sum(scores.values()) / len(scores), 4) if scores else 0.0

    return ProviderEvaluateResponse(
        provider=req.provider,
        model=req.model or adapter.default_model,
        scores=scores,
        overall=overall,
        reasoning=reasoning,
        latency_ms=latency_ms,
    )
