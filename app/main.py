from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.v1.routes import evaluate, filter_route, pipeline
from app.core.config import settings
from app.core.exceptions import QualityAPIError

app = FastAPI(
    title="Post-Processing AI Quality API",
    description="Evaluate and improve AI-generated output quality through configurable post-processing pipelines.",
    version="0.1.0",
)

app.include_router(evaluate.router, prefix="/api/v1", tags=["evaluate"])
app.include_router(filter_route.router, prefix="/api/v1", tags=["filter"])
app.include_router(pipeline.router, prefix="/api/v1", tags=["pipeline"])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.exception_handler(QualityAPIError)
async def quality_api_error_handler(request: Request, exc: QualityAPIError):
    return JSONResponse(
        status_code=422,
        content={"error": type(exc).__name__, "message": str(exc)},
    )
