"""
FastAPI exception handlers.

Registers four handlers on the FastAPI app instance:
  1. RequestValidationError  → 422 with per-field ErrorDetail list
  2. HTTPException           → echo with ErrorResponse body
  3. QualityAPIError         → 400 (or subclass-defined status) with ErrorResponse
  4. Exception               → 500 Internal Server Error (hides internal details in production)
"""
import logging
import traceback
from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.exceptions import QualityAPIError
from app.models.error import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str | None:
    return request.headers.get("x-request-id") or request.state.__dict__.get("request_id")


def _json(status_code: int, body: ErrorResponse) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=body.model_dump(exclude_none=True))


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI application."""

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", [])[1:])  # strip "body" prefix
            details.append(ErrorDetail(field=loc or None, message=err["msg"]))
        body = ErrorResponse(
            error="validation_error",
            message="Request validation failed. Check the 'details' list for field-level errors.",
            details=details,
            request_id=_request_id(request),
        )
        return _json(status.HTTP_422_UNPROCESSABLE_ENTITY, body)

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        body = ErrorResponse(
            error="http_error",
            message=str(exc.detail),
            request_id=_request_id(request),
        )
        return _json(exc.status_code, body)

    @app.exception_handler(QualityAPIError)
    async def handle_domain_error(request: Request, exc: QualityAPIError) -> JSONResponse:
        details = [ErrorDetail(field=d.get("field"), message=d["message"]) for d in exc.details]
        body = ErrorResponse(
            error=exc.error_code,
            message=exc.message,
            details=details,
            request_id=_request_id(request),
        )
        return _json(exc.http_status, body)

    @app.exception_handler(Exception)
    async def handle_generic_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception: %s
%s", exc, traceback.format_exc())
        body = ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred. Please try again later.",
            request_id=_request_id(request),
        )
        return _json(status.HTTP_500_INTERNAL_SERVER_ERROR, body)
