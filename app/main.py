"""
Post-Processing AI Quality API — application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import evaluate, filter_route, pipeline, health, providers
from app.api.v1.routes.history import router as history_router
from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.core.middleware import RequestIDMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialise audit DB (no-op if AUDIT_ENABLED=false)
    init_db()
    yield
    # Shutdown: nothing to clean up for SQLite


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=(
        "Post-process AI-generated outputs: evaluate quality via configurable scorers "
        "(coherence, relevance, fluency, toxicity, hallucination), filter below-threshold "
        "outputs, run chainable multi-step pipelines, and compare results across LLM providers."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health",    "description": "Liveness and readiness probes."},
        {"name": "evaluate",  "description": "Single-text quality evaluation."},
        {"name": "filter",    "description": "Batch quality filtering."},
        {"name": "pipeline",  "description": "Multi-step post-processing pipelines."},
        {"name": "providers", "description": "LLM provider adapters (OpenAI, Anthropic, HuggingFace)."},
        {"name": "history",   "description": "Audit trail of past evaluations."},
    ],
)

# ── Middleware (order matters: outermost applied last) ──────────────────────
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# ── Exception handlers ──────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(evaluate.router,    prefix="/api/v1", tags=["evaluate"])
app.include_router(filter_route.router, prefix="/api/v1", tags=["filter"])
app.include_router(pipeline.router,    prefix="/api/v1", tags=["pipeline"])
app.include_router(providers.router,   prefix="/api/v1", tags=["providers"])
app.include_router(history_router,     prefix="/api/v1", tags=["history"])
