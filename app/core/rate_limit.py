"""
IP-based sliding-window rate limiting middleware.

Limits are defined per endpoint path. No external dependencies — stdlib only.

Default limits (override via environment variables):
  RATE_LIMIT_EVALUATE   — requests per minute for /api/v1/evaluate        (default 60)
  RATE_LIMIT_FILTER     — requests per minute for /api/v1/filter           (default 30)
  RATE_LIMIT_PIPELINE   — requests per minute for /api/v1/pipeline/run     (default 30)
  RATE_LIMIT_PROVIDERS  — requests per minute for /api/v1/providers/evaluate (default 20)
"""
from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


# (max_requests, window_seconds)
_LIMITS: Dict[str, Tuple[int, int]] = {
    "/api/v1/evaluate":           (_int_env("RATE_LIMIT_EVALUATE", 60),  60),
    "/api/v1/filter":             (_int_env("RATE_LIMIT_FILTER", 30),    60),
    "/api/v1/pipeline/run":       (_int_env("RATE_LIMIT_PIPELINE", 30),  60),
    "/api/v1/providers/evaluate": (_int_env("RATE_LIMIT_PROVIDERS", 20), 60),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter keyed by (client_ip, path)."""

    def __init__(self, app) -> None:
        super().__init__(app)
        # store: key → list of timestamps within the window
        self._store: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        config = _LIMITS.get(path)
        if config is None:
            return await call_next(request)

        max_calls, window = config
        client = request.client.host if request.client else "unknown"
        key = f"{client}:{path}"
        now = time.monotonic()

        # Evict timestamps outside the window
        self._store[key] = [t for t in self._store[key] if now - t < window]

        if len(self._store[key]) >= max_calls:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded — too many requests.",
                    "limit": max_calls,
                    "window_seconds": window,
                },
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(max_calls),
                    "X-RateLimit-Remaining": "0",
                },
            )

        self._store[key].append(now)
        response = await call_next(request)
        remaining = max(0, max_calls - len(self._store[key]))
        response.headers["X-RateLimit-Limit"] = str(max_calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
