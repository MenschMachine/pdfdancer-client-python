"""
Tests for 429 rate limit handling
"""
import time
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
    def test_rate_limit_exception_raised_after_retries_exhausted(self, mock_client_class):
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

    @patch("pdfdancer.pdfdancer_v1.httpx.Client")
    @patch("pdfdancer.pdfdancer_v1.time.sleep")
    def test_rate_limit_retry_with_exponential_backoff(self, mock_sleep, mock_client_class):
        """Test that 429 responses retry with exponential backoff when no Retry-After"""
        from pdfdancer import PDFDancer

        # Create mock responses: first 2 attempts fail with 429, third succeeds
        mock_429_response = Mock(spec=httpx.Response)
        mock_429_response.status_code = 429
        mock_429_response.headers = {}  # No Retry-After header
        mock_429_response.content = b'{"error": "Rate limit exceeded"}'
        mock_429_response.text = '{"error": "Rate limit exceeded"}'

        mock_success_response = Mock(spec=httpx.Response)
        mock_success_response.status_code = 200
        mock_success_response.text = "test-session-id"
        mock_success_response.headers = {}
        mock_success_response.content = b"test-session-id"

        # Mock token response
        mock_token_response = Mock(spec=httpx.Response)
        mock_token_response.status_code = 200
        mock_token_response.headers = {}
        mock_token_response.json.return_value = {"token": "test-token"}

        mock_error = httpx.HTTPStatusError(
            "429 Rate limit exceeded", request=Mock(), response=mock_429_response
        )

        # Mock the client
        mock_httpx_client = Mock()
        mock_client_class.return_value = mock_httpx_client

        # First call is for token (succeeds), next 2 calls fail with 429, fourth succeeds
        mock_httpx_client.post.side_effect = [
            mock_token_response,
            mock_error,
            mock_error,
            mock_success_response,
        ]

        # This should succeed after retries
        pdf = PDFDancer.open(pdf_data=b"fake pdf data")

        # Verify it retried (1 token call + 3 session calls)
        assert mock_httpx_client.post.call_count == 4

        # Verify exponential backoff was used
        assert mock_sleep.call_count >= 2
        # The actual delays should increase exponentially
        # Note: The exact values depend on the retry_backoff_factor configuration
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        # Verify delays are increasing (exponential backoff)
        if len(calls) >= 2:
            assert calls[1] > calls[0], f"Expected exponential backoff, got {calls}"

    @patch("pdfdancer.pdfdancer_v1.httpx.Client")
    @patch("pdfdancer.pdfdancer_v1.time.sleep")
    def test_rate_limit_retry_uses_retry_after_header(self, mock_sleep, mock_client_class):
        """Test that 429 responses use Retry-After header value for delay"""
        from pdfdancer import PDFDancer

        # Create mock responses: first attempt fails with 429 and Retry-After, second succeeds
        mock_429_response = Mock(spec=httpx.Response)
        mock_429_response.status_code = 429
        mock_429_response.headers = {"Retry-After": "10"}  # Use 10 second delay
        mock_429_response.content = b'{"error": "Rate limit exceeded"}'
        mock_429_response.text = '{"error": "Rate limit exceeded"}'

        mock_success_response = Mock(spec=httpx.Response)
        mock_success_response.status_code = 200
        mock_success_response.text = "test-session-id"
        mock_success_response.headers = {}
        mock_success_response.content = b"test-session-id"

        # Mock token response
        mock_token_response = Mock(spec=httpx.Response)
        mock_token_response.status_code = 200
        mock_token_response.headers = {}
        mock_token_response.json.return_value = {"token": "test-token"}

        mock_error = httpx.HTTPStatusError(
            "429 Rate limit exceeded", request=Mock(), response=mock_429_response
        )

        # Mock the client
        mock_httpx_client = Mock()
        mock_client_class.return_value = mock_httpx_client

        # First call is for token (succeeds), second fails with 429, third succeeds
        mock_httpx_client.post.side_effect = [
            mock_token_response,
            mock_error,
            mock_success_response,
        ]

        # This should succeed after retry
        pdf = PDFDancer.open(pdf_data=b"fake pdf data")

        # Verify it retried (1 token call + 2 session calls)
        assert mock_httpx_client.post.call_count == 3

        # Verify Retry-After value was used (10 seconds)
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(10)
