"""
Tests for 429 rate limit handling
"""

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import Mock, patch

import httpx
import pytest

from pdfdancer.exceptions import RateLimitException


class TestRateLimitHandling:
    """Test rate limit handling with 429 responses"""

    def test_rate_limit_with_retry_after_header(self):
        """Test that 429 responses with Retry-After header are handled correctly"""
        from pdfdancer.pdfdancer_v2 import _get_retry_after_delay

        # Create mock response with Retry-After header
        mock_response = Mock(spec=httpx.Response)
        mock_response.headers = {"Retry-After": "5"}

        delay = _get_retry_after_delay(mock_response)
        assert delay == 5

    def test_rate_limit_without_retry_after_header(self):
        """Test that 429 responses without Retry-After header return None"""
        from pdfdancer.pdfdancer_v2 import _get_retry_after_delay

        # Create mock response without Retry-After header
        mock_response = Mock(spec=httpx.Response)
        mock_response.headers = {}

        delay = _get_retry_after_delay(mock_response)
        assert delay is None

    def test_rate_limit_with_invalid_retry_after(self):
        """Test that invalid Retry-After values return None"""
        from pdfdancer.pdfdancer_v2 import _get_retry_after_delay

        # Create mock response with invalid Retry-After header
        mock_response = Mock(spec=httpx.Response)
        mock_response.headers = {"Retry-After": "invalid"}

        delay = _get_retry_after_delay(mock_response)
        assert delay is None

    def test_rate_limit_with_negative_retry_after(self):
        """Test that negative Retry-After values are ignored."""
        from pdfdancer.pdfdancer_v2 import _get_retry_after_delay

        mock_response = Mock(spec=httpx.Response)
        mock_response.headers = {"Retry-After": "-1"}

        delay = _get_retry_after_delay(mock_response)
        assert delay is None

    def test_rate_limit_with_http_date_retry_after(self):
        """Test that HTTP-date Retry-After values are converted to seconds."""
        from pdfdancer.pdfdancer_v2 import _get_retry_after_delay

        retry_at = datetime.now(timezone.utc) + timedelta(seconds=30)
        mock_response = Mock(spec=httpx.Response)
        mock_response.headers = {"Retry-After": format_datetime(retry_at)}

        delay = _get_retry_after_delay(mock_response)
        assert delay is not None
        assert 0 <= delay <= 30

    @patch("pdfdancer.pdfdancer_v2.httpx.Client")
    def test_rate_limit_exception_raised_after_retries_exhausted(
        self, mock_client_class
    ):
        """Test that RateLimitException is raised after all attempts return 429."""
        from pdfdancer import PDFDancer

        # Create mock response with 429 status
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "1"}
        mock_response.content = b'{"error": "Rate limit exceeded"}'
        mock_response.text = '{"error": "Rate limit exceeded"}'

        # Create HTTPStatusError
        mock_error = httpx.HTTPStatusError(
            "429 Rate limit exceeded", request=Mock(), response=mock_response
        )

        # Mock the client to always raise 429
        mock_httpx_client = Mock()
        mock_client_class.return_value = mock_httpx_client
        mock_httpx_client.post.side_effect = mock_error

        # PDFDancer should retry and then raise RateLimitException
        with pytest.raises(RateLimitException) as exc_info:
            PDFDancer.open(pdf_data=b"fake pdf data")

        # Verify the exception contains retry_after
        assert exc_info.value.retry_after == 1
        assert exc_info.value.response == mock_response

        # max_attempts includes the initial request.
        assert mock_httpx_client.post.call_count == 3

    @pytest.mark.parametrize("max_attempts", [0, -1, 1.5, True])
    def test_max_attempts_must_be_a_positive_integer(self, max_attempts):
        """The initial request requires a positive integral attempt count."""
        from pdfdancer import PDFDancer, ValidationException

        with pytest.raises(ValidationException, match="max_attempts"):
            PDFDancer.open(pdf_data=b"fake pdf data", max_attempts=max_attempts)
