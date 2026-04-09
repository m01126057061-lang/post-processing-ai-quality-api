"""
GET /api/v1/history — paginated audit trail of past evaluations.
"""
from typing import Optional

from fastapi import APIRouter, Query

from app.db.repository import list_evaluations

router = APIRouter()


@router.get(
    "/history",
    summary="List past evaluation records",
    description=(
        "Returns paginated evaluation records from the audit trail. "
        "Requires AUDIT_ENABLED=true (default). "
        "Filter by metric name using the `metric` query parameter."
    ),
    tags=["history"],
)
async def get_history(
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    metric: Optional[str] = Query(None, description="Filter by metric name (e.g. coherence)"),
):
    return await list_evaluations(limit=limit, offset=offset, metric=metric)
