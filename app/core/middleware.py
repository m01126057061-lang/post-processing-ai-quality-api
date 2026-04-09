"""
Middleware for the Post-Processing AI Quality API.

RequestIDMiddleware
    - Reads X-Request-ID from the incoming request header (if present).
    - Generates a UUID4 if the header is absent.
    - Stores the ID on request.state.request_id (accessible in handlers).
    - Echoes the ID back as X-Request-ID in every response header.
"""
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
