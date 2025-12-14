"""
Retry utilities with exponential backoff.

This module provides decorators and utilities for handling transient failures
in API calls with configurable retry logic and exponential backoff.
"""

import logging
import time
from functools import wraps
from typing import Callable, Type, TypeVar

import requests

logger = logging.getLogger(__name__)

# Type variable for generic return type
T = TypeVar("T")

# Default exceptions to retry on
DEFAULT_RETRY_EXCEPTIONS: tuple[Type[Exception], ...] = (
    requests.exceptions.RequestException,
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
)

# HTTP status codes that should trigger a retry
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class RetryError(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, last_exception: Exception | None = None):
        super().__init__(message)
        self.last_exception = last_exception


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = DEFAULT_RETRY_EXCEPTIONS,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that retries a function with exponential backoff.

    Implements exponential backoff strategy where the delay between retries
    increases exponentially: delay = base_delay * (exponential_base ** attempt)

    Args:
        max_retries: Maximum number of retry attempts. Defaults to 3.
        base_delay: Initial delay in seconds before first retry. Defaults to 1.0.
        max_delay: Maximum delay in seconds between retries. Defaults to 60.0.
        exponential_base: Base for exponential backoff calculation. Defaults to 2.0.
        exceptions: Tuple of exception types that should trigger a retry.

    Returns:
        A decorator function that wraps the target function with retry logic.

    Raises:
        RetryError: When all retry attempts have been exhausted.

    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def fetch_data():
            return requests.get("https://api.example.com/data")
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)

                    # Check for retryable HTTP status codes if result is a Response
                    if isinstance(result, requests.Response):
                        if result.status_code in RETRYABLE_STATUS_CODES:
                            raise requests.HTTPError(
                                f"Retryable status code: {result.status_code}",
                                response=result,
                            )

                    return result

                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"All {max_retries} retries exhausted for {func.__name__}. "
                            f"Last error: {e}"
                        )
                        raise RetryError(
                            f"Failed after {max_retries} retries: {e}",
                            last_exception=e,
                        ) from e

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base**attempt),
                        max_delay,
                    )

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} for {func.__name__} "
                        f"failed with {type(e).__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    time.sleep(delay)

            # This should never be reached, but just in case
            raise RetryError(
                f"Unexpected retry loop exit for {func.__name__}",
                last_exception=last_exception,
            )

        return wrapper

    return decorator


def retry_on_rate_limit(
    max_retries: int = 5,
    base_delay: float = 2.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Specialized retry decorator for handling API rate limits (HTTP 429).

    Uses longer delays and more retries suitable for rate-limited APIs.

    Args:
        max_retries: Maximum number of retry attempts. Defaults to 5.
        base_delay: Initial delay in seconds. Defaults to 2.0.

    Returns:
        A decorator function configured for rate limit handling.
    """
    return retry_with_backoff(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=120.0,
        exponential_base=2.0,
        exceptions=(requests.exceptions.RequestException,),
    )
