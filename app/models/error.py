"""
Unified error response models used by all exception handlers.
Every non-2xx response from the API returns an ErrorResponse JSON body.
"""
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """A single validation or domain error detail."""
    field: str | None = None   # dotted path to the offending field, if applicable
    message: str                  # human-readable error message


class ErrorResponse(BaseModel):
    """Standard error envelope returned for all non-2xx responses."""
    error: str                          # machine-readable error code (e.g. "validation_error")
    message: str                        # short human-readable summary
    details: list[ErrorDetail] = []     # per-field breakdown (populated for 422)
    request_id: str | None = None    # echoed from X-Request-ID header when present
