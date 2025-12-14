"""
Tests for retry mechanism.

These tests verify exponential backoff retry for API calls.
"""

import pytest

from utils.retry import retry_with_backoff, RetryError


class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator."""

    def test_returns_result_on_success(self):
        """Successful function should return result without retry."""
        @retry_with_backoff(max_retries=3, exceptions=(Exception,))
        def successful():
            return "ok"

        assert successful() == "ok"

    def test_retries_on_failure_then_succeeds(self):
        """Function should retry on exception and succeed eventually."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01, exceptions=(Exception,))
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            return "ok"

        result = eventually_succeeds()

        assert result == "ok"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        """Should raise RetryError after all retries exhausted."""
        @retry_with_backoff(max_retries=2, base_delay=0.01, exceptions=(Exception,))
        def always_fails():
            raise Exception("Permanent error")

        with pytest.raises(RetryError):
            always_fails()

    def test_does_not_retry_unexpected_exception(self):
        """Should not retry on exceptions not in the tuple."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01, exceptions=(ValueError,))
        def raises_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Not retryable")

        with pytest.raises(TypeError):
            raises_type_error()

        # Should only be called once (no retries)
        assert call_count == 1
