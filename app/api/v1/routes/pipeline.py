from fastapi import APIRouter, HTTPException

from app.models.request import PipelineRunRequest
from app.models.response import PipelineRunResponse
from app.pipeline.engine import build_step, run_pipeline

router = APIRouter()


@router.post("/pipeline/run", response_model=PipelineRunResponse, summary="Run a multi-step post-processing pipeline")
def run_pipeline_endpoint(request: PipelineRunRequest) -> PipelineRunResponse:
    """
    Execute an ordered list of pipeline steps over a batch of AI-generated texts.

    **Step types:**
    - `score`     — evaluate quality metrics (coherence, relevance, fluency)
    - `filter`    — remove texts whose overall score is below a threshold
    - `transform` — apply text transformations (strip, lowercase, truncate)

    **Example pipeline:**
    ```json
    {
      "texts": ["Great answer!", "bad"],
      "steps": [
        {"type": "score", "metrics": ["fluency", "coherence"]},
        {"type": "filter", "threshold": 0.5},
        {"type": "transform", "operation": "strip"}
      ]
    }
    ```
    """
    # Validate and build all steps up front — fail fast before processing any text
    try:
        steps = [build_step(s) for s in request.steps]
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return run_pipeline(
        texts=request.texts,
        context=request.context,
        steps=request.steps,
    )
