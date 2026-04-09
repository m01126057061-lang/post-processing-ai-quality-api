"""
Post-Processing AI Quality API — application entry point.

Registers:
  - CORS middleware (permissive by default; restrict origins in production)
  - RequestIDMiddleware (X-Request-ID injection)
  - Structured exception handlers (validation, HTTP, domain, generic)
  - API routers: /health, /api/v1/evaluate, /api/v1/filter, /api/v1/pipeline/run
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import evaluate, filter_route, pipeline, health
from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.core.middleware import RequestIDMiddleware

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=(
        "Post-process AI-generated outputs: evaluate quality via configurable scorers "
        "(coherence, relevance, fluency), filter below-threshold outputs, "
        "and run chainable multi-step pipelines."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Liveness and readiness probes."},
        {"name": "evaluate", "description": "Single-text quality evaluation."},
        {"name": "filter", "description": "Batch quality filtering."},
        {"name": "pipeline", "description": "Multi-step post-processing pipelines."},
    ],
)

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Restrict to specific origins in production
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ── Exception handlers ──────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(health.router)                                  # /health, /health/ready
app.include_router(evaluate.router, prefix="/api/v1", tags=["evaluate"])
app.include_router(filter_route.router, prefix="/api/v1", tags=["filter"])
app.include_router(pipeline.router, prefix="/api/v1", tags=["pipeline"])
