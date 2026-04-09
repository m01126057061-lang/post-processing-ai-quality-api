from fastapi import APIRouter
from app.models.request import PipelineRunRequest
from app.models.response import PipelineRunResponse

router = APIRouter()


@router.post("/pipeline/run", response_model=PipelineRunResponse)
def run_pipeline(request: PipelineRunRequest) -> PipelineRunResponse:
    """
    Run a full post-processing pipeline on the input text.
    TODO: load and execute pipeline steps from config.
    """
    return PipelineRunResponse(output=request.text, steps_completed=0, passed=False)
