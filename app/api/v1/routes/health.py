"""
Health-check endpoints.

GET /health
    Returns a minimal liveness probe — used by Docker HEALTHCHECK and load balancers.
    Always returns 200 if the process is running.

GET /health/ready
    Readiness probe — verifies the scorer registry is available and the embedding model
    can be imported (lazy, no actual inference). Returns 503 if not ready.
"""
import importlib

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
def liveness() -> dict:
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness probe")
def readiness() -> JSONResponse:
    checks: dict[str, str] = {}

    # Check scorer registry is importable
    try:
        from app.scorers.registry import available_metrics
        metrics = available_metrics()
        checks["scorer_registry"] = f"ok ({len(metrics)} metrics registered)"
    except Exception as exc:
        checks["scorer_registry"] = f"error: {exc}"

    # Check sentence-transformers is importable (model loaded lazily)
    try:
        importlib.import_module("sentence_transformers")
        checks["sentence_transformers"] = "ok"
    except ImportError as exc:
        checks["sentence_transformers"] = f"missing: {exc}"

    all_ok = all(v.startswith("ok") for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )
