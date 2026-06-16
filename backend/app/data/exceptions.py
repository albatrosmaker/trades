"""
Custom exceptions for the data ingestion layer.
"""


class DataFetchError(Exception):
    """Raised when a data fetch operation fails after all retries."""

    def __init__(self, message: str, source: str = "", status_code: int | None = None):
        super().__init__(message)
        self.source = source
        self.status_code = status_code

    def __str__(self) -> str:
        base = super().__str__()
        parts = [base]
        if self.source:
            parts.append(f"source={self.source}")
        if self.status_code is not None:
            parts.append(f"status_code={self.status_code}")
        return " | ".join(parts)


class RateLimitError(DataFetchError):
    """Raised when a data source rate limit is hit and cannot be retried."""

    def __init__(self, message: str, source: str = "", retry_after: float | None = None):
        super().__init__(message, source=source, status_code=429)
        self.retry_after = retry_after

    def __str__(self) -> str:
        base = super().__str__()
        if self.retry_after is not None:
            return f"{base} | retry_after={self.retry_after}s"
        return base


class DataQualityError(Exception):
    """Raised when fetched data fails quality/integrity checks."""

    def __init__(self, message: str, field: str = "", source: str = ""):
        super().__init__(message)
        self.field = field
        self.source = source

    def __str__(self) -> str:
        base = super().__str__()
        parts = [base]
        if self.field:
            parts.append(f"field={self.field}")
        if self.source:
            parts.append(f"source={self.source}")
        return " | ".join(parts)


class InsufficientDataError(Exception):
    """
    Raised when the aggregated data quality score is too low to support
    a meaningful analysis or recommendation.
    """

    def __init__(
        self,
        message: str,
        quality_score: float = 0.0,
        missing_fields: list[str] | None = None,
    ):
        super().__init__(message)
        self.quality_score = quality_score
        self.missing_fields = missing_fields or []

    def __str__(self) -> str:
        base = super().__str__()
        parts = [base, f"quality_score={self.quality_score:.1f}"]
        if self.missing_fields:
            parts.append(f"missing_fields={self.missing_fields}")
        return " | ".join(parts)
