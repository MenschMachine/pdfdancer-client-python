"""
Tests for 429 rate limit handling
"""

from unittest.mock import Mock, patch

import httpx
import pytest

from pdfdancer.exceptions import RateLimitException


class TestRateLimitHandling:
    """Test rate limit handling with 429 responses"""

    def test_rate_limit_with_retry_after_header(self):
        """Test that 429 responses with Retry-After header are handled correctly"""
        from pdfdancer.pdfdancer_v1 import _get_retry_after_delay

        # Create mock response with Retry-After header
        mock_response = Mock(spec=httpx.Response)
        mock_response.headers = {"Retry-After": "5"}

        delay = _get_retry_after_delay(mock_response)
        assert delay == 5

    def test_rate_limit_without_retry_after_header(self):
        """Test that 429 responses without Retry-After header return None"""
        from pdfdancer.pdfdancer_v1 import _get_retry_after_delay

        # Create mock response without Retry-After header
        mock_response = Mock(spec=httpx.Response)
        mock_response.headers = {}

        delay = _get_retry_after_delay(mock_response)
        assert delay is None

    def test_rate_limit_with_invalid_retry_after(self):
        """Test that invalid Retry-After values return None"""
        from pdfdancer.pdfdancer_v1 import _get_retry_after_delay

        # Create mock response with invalid Retry-After header
        mock_response = Mock(spec=httpx.Response)
        mock_response.headers = {"Retry-After": "invalid"}

        delay = _get_retry_after_delay(mock_response)
        assert delay is None

    @patch("pdfdancer.pdfdancer_v1.httpx.Client")
    def test_rate_limit_exception_raised_after_retries_exhausted(
        self, mock_client_class
    ):
        """Test that RateLimitException is raised after max retries for 429"""
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

        # Verify it retried (max_retries=3, so 4 attempts total)
        assert mock_httpx_client.post.call_count == 4
