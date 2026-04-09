class QualityAPIError(Exception):
    """Base exception for all quality API errors."""


class ValidationError(QualityAPIError):
    """Raised when input validation fails."""


class PipelineError(QualityAPIError):
    """Raised when a pipeline step fails."""


class ScorerError(QualityAPIError):
    """Raised when a scorer encounters an error."""


class ProviderError(QualityAPIError):
    """Raised when an AI provider call fails."""
