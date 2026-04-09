"""
Domain exception hierarchy for the Post-Processing AI Quality API.

Raise these from business logic; the registered FastAPI exception handlers
translate them to structured ErrorResponse bodies.

Hierarchy:
  QualityAPIError (base, HTTP 400)
  ├── UnknownMetricError        — requested metric is not registered
  ├── EmptyBatchError           — texts list is empty
  ├── BatchTooLargeError        — texts list exceeds MAX_BATCH_SIZE
  ├── TextTooLongError          — a single text exceeds MAX_TEXT_LENGTH
  ├── BlankTextError            — a text is empty or whitespace-only
  ├── InvalidPipelineError      — pipeline step configuration is logically invalid
  │   └── FilterBeforeScoreError
  ├── UnknownProviderError      — requested provider is not registered
  ├── ProviderNotAvailableError — provider API key is not configured (HTTP 503)
  └── ProviderCallError         — provider API call failed (HTTP 502)
"""


class QualityAPIError(Exception):
    """Base class for all domain errors. Maps to HTTP 400 by default."""
    http_status: int = 400
    error_code: str = "quality_api_error"

    def __init__(self, message: str, details: list[dict] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: list[dict] = details or []


# ── Metric / text validation errors ──────────────────────────────────────────

class UnknownMetricError(QualityAPIError):
    error_code = "unknown_metric"

    def __init__(self, unknown: list[str], available: list[str]) -> None:
        super().__init__(
            message=f"Unknown metric(s): {unknown}. Available: {sorted(available)}",
            details=[
                {"field": "metrics", "message": f"{m!r} is not a registered scorer"}
                for m in unknown
            ],
        )
        self.unknown = unknown
        self.available = available


class EmptyBatchError(QualityAPIError):
    error_code = "empty_batch"

    def __init__(self) -> None:
        super().__init__(
            message="texts must contain at least one item.",
            details=[{"field": "texts", "message": "batch must not be empty"}],
        )


class BatchTooLargeError(QualityAPIError):
    error_code = "batch_too_large"

    def __init__(self, received: int, max_size: int) -> None:
        super().__init__(
            message=f"Batch size {received} exceeds maximum of {max_size}.",
            details=[{"field": "texts", "message": f"received {received} items, max is {max_size}"}],
        )


class TextTooLongError(QualityAPIError):
    error_code = "text_too_long"

    def __init__(self, index: int | None, length: int, max_length: int) -> None:
        field = f"texts[{index}]" if index is not None else "text"
        super().__init__(
            message=f"Text at {field} has {length} characters; maximum is {max_length}.",
            details=[{"field": field, "message": f"exceeds max length of {max_length}"}],
        )


class BlankTextError(QualityAPIError):
    error_code = "blank_text"

    def __init__(self, index: int | None = None) -> None:
        field = f"texts[{index}]" if index is not None else "text"
        super().__init__(
            message=f"{field} must not be blank.",
            details=[{"field": field, "message": "text is empty or whitespace-only"}],
        )


# ── Pipeline errors ───────────────────────────────────────────────────────────

class InvalidPipelineError(QualityAPIError):
    error_code = "invalid_pipeline"


class FilterBeforeScoreError(InvalidPipelineError):
    error_code = "filter_before_score"

    def __init__(self) -> None:
        super().__init__(
            message=(
                "A 'filter' step appears before any 'score' step. "
                "All items would have overall=0.0 and be filtered. "
                "Add a 'score' step before 'filter'."
            ),
            details=[{"field": "steps", "message": "filter step has no prior score step"}],
        )


# ── Provider errors ───────────────────────────────────────────────────────────

class UnknownProviderError(QualityAPIError):
    """Requested provider slug is not registered."""
    error_code = "unknown_provider"

    def __init__(self, provider: str, available: list[str]) -> None:
        super().__init__(
            message=f"Unknown provider {provider!r}. Available: {sorted(available)}",
            details=[{"field": "provider", "message": f"{provider!r} is not registered"}],
        )
        self.provider = provider
        self.available = available


class ProviderNotAvailableError(QualityAPIError):
    """Provider is registered but its API key / credentials are not configured."""
    http_status = 503
    error_code = "provider_not_available"

    def __init__(self, provider: str) -> None:
        super().__init__(
            message=(
                f"Provider {provider!r} is not configured. "
                "Set the required API key in your environment variables."
            ),
            details=[{
                "field": "provider",
                "message": f"{provider!r} requires an API key that is not set",
            }],
        )
        self.provider = provider


class ProviderCallError(QualityAPIError):
    """Provider API call failed (network error, rate limit, invalid response, etc.)."""
    http_status = 502
    error_code = "provider_call_failed"

    def __init__(self, provider: str, reason: str) -> None:
        super().__init__(
            message=f"Call to {provider!r} provider failed: {reason}",
            details=[{"field": None, "message": reason}],
        )
        self.provider = provider
        self.reason = reason
