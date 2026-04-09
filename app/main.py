"""
Post-Processing AI Quality API — application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import evaluate, filter_route, pipeline, health, providers
from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.core.middleware import RequestIDMiddleware

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=(
        "Post-process AI-generated outputs: evaluate quality via configurable scorers "
        "(coherence, relevance, fluency), filter below-threshold outputs, "
        "run chainable multi-step pipelines, and compare results across LLM providers."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Liveness and readiness probes."},
        {"name": "evaluate", "description": "Single-text quality evaluation (embedding-based)."},
        {"name": "filter", "description": "Batch quality filtering."},
        {"name": "pipeline", "description": "Multi-step post-processing pipelines."},
        {"name": "providers", "description": "LLM provider adapters (OpenAI, Anthropic, HuggingFace)."},
    ],
)

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ── Exception handlers ──────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(evaluate.router, prefix="/api/v1", tags=["evaluate"])
app.include_router(filter_route.router, prefix="/api/v1", tags=["filter"])
app.include_router(pipeline.router, prefix="/api/v1", tags=["pipeline"])
app.include_router(providers.router, prefix="/api/v1", tags=["providers"])
