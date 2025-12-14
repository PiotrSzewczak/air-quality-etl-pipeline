"""
Custom exceptions for the air quality ETL pipeline.

This module defines application-specific exceptions for better
error handling and debugging.
"""


class AirQualityError(Exception):
    """Base exception for all air quality pipeline errors."""

    pass


class APIError(AirQualityError):
    """Raised when an API request fails."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class AuthenticationError(APIError):
    """Raised when API authentication fails (401/403)."""

    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded (429)."""

    pass


class NotFoundError(APIError):
    """Raised when a requested resource is not found (404)."""

    pass


class ValidationError(AirQualityError):
    """Raised when data validation fails."""

    pass


class ConfigurationError(AirQualityError):
    """Raised when configuration is invalid or missing."""

    pass
