"""
Tests for anonymous token fallback functionality.

These tests verify that the PDFDancer client can automatically obtain
anonymous tokens when no PDFDANCER_TOKEN is provided, matching the
behavior of the Java client.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from pdfdancer import PDFDancer
from pdfdancer.exceptions import HttpClientException


class TestAnonymousTokenFallback:
    """Test anonymous token fallback when PDFDANCER_TOKEN is not set."""

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx.Client for testing."""
        with patch("pdfdancer.pdfdancer_v1.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def clear_env_token(self):
        """Temporarily clear PDFDANCER_TOKEN from environment."""
        original_token = os.environ.get("PDFDANCER_TOKEN")
        if "PDFDANCER_TOKEN" in os.environ:
            del os.environ["PDFDANCER_TOKEN"]
        yield
        if original_token is not None:
            os.environ["PDFDANCER_TOKEN"] = original_token

    def test_resolve_token_returns_none_when_no_token(self, clear_env_token):
        """Test that _resolve_token returns None when no token is available."""
        result = PDFDancer._resolve_token(None)
        assert result is None

    def test_resolve_token_uses_explicit_token(self):
        """Test that _resolve_token uses explicitly provided token."""
        token = "test-token-123"
        result = PDFDancer._resolve_token(token)
        assert result == token

    def test_resolve_token_uses_env_token(self):
        """Test that _resolve_token uses PDFDANCER_TOKEN from environment."""
        with patch.dict(os.environ, {"PDFDANCER_TOKEN": "env-token-456"}):
            result = PDFDancer._resolve_token(None)
            assert result == "env-token-456"

    def test_resolve_token_prefers_explicit_over_env(self):
        """Test that explicit token takes precedence over environment variable."""
        with patch.dict(os.environ, {"PDFDANCER_TOKEN": "env-token"}):
            result = PDFDancer._resolve_token("explicit-token")
            assert result == "explicit-token"

    def test_obtain_anonymous_token_success(self, mock_httpx_client):
        """Test successful anonymous token retrieval."""
        # Mock the response from /keys/anon endpoint
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "token": "anon-token-789",
            "metadata": {
                "id": "test-id",
                "name": "Anonymous Token",
                "prefix": "anon",
                "createdAt": "2025-01-01T00:00:00Z",
                "expiresAt": "2025-12-31T23:59:59Z",
            },
        }
        mock_httpx_client.post.return_value = mock_response

        token = PDFDancer._obtain_anonymous_token("http://localhost:8080")

        assert token == "anon-token-789"
        mock_httpx_client.post.assert_called_once()
        call_args = mock_httpx_client.post.call_args
        assert "/keys/anon" in call_args[0][0]
        assert "X-Fingerprint" in call_args[1]["headers"]

    def test_obtain_anonymous_token_http_error(self, mock_httpx_client):
        """Test that HTTP errors are properly handled when obtaining anonymous token."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        with pytest.raises(HttpClientException) as exc_info:
            PDFDancer._obtain_anonymous_token("http://localhost:8080")

        assert "Failed to obtain anonymous token" in str(exc_info.value)
        assert "HTTP 404" in str(exc_info.value)

    def test_obtain_anonymous_token_network_error(self, mock_httpx_client):
        """Test that network errors are properly handled when obtaining anonymous token."""
        import httpx

        mock_httpx_client.post.side_effect = httpx.RequestError("Connection failed")

        with pytest.raises(HttpClientException) as exc_info:
            PDFDancer._obtain_anonymous_token("http://localhost:8080")

        assert "Failed to obtain anonymous token" in str(exc_info.value)
        assert "Connection failed" in str(exc_info.value)

    def test_obtain_anonymous_token_invalid_response(self, mock_httpx_client):
        """Test that invalid response format is properly handled."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"invalid": "response"}
        mock_httpx_client.post.return_value = mock_response

        with pytest.raises(HttpClientException) as exc_info:
            PDFDancer._obtain_anonymous_token("http://localhost:8080")

        assert "Invalid anonymous token response format" in str(exc_info.value)

    @patch("pdfdancer.pdfdancer_v1.PDFDancer._obtain_anonymous_token")
    @patch("pdfdancer.pdfdancer_v1.PDFDancer.__init__")
    def test_open_uses_anonymous_token_when_no_token(
        self, mock_init, mock_obtain_token, clear_env_token
    ):
        """Test that PDFDancer.open() obtains anonymous token when none provided."""
        mock_init.return_value = None
        mock_obtain_token.return_value = "anon-token-123"

        PDFDancer.open(b"%PDF-1.4")

        mock_obtain_token.assert_called_once()
        mock_init.assert_called_once()
        # Verify anonymous token was passed to __init__
        assert mock_init.call_args[0][0] == "anon-token-123"

    @patch("pdfdancer.pdfdancer_v1.PDFDancer._obtain_anonymous_token")
    @patch("pdfdancer.pdfdancer_v1.PDFDancer.__init__")
    def test_open_uses_explicit_token(self, mock_init, mock_obtain_token):
        """Test that PDFDancer.open() uses explicit token when provided."""
        mock_init.return_value = None

        PDFDancer.open(b"%PDF-1.4", token="explicit-token")

        mock_obtain_token.assert_not_called()
        mock_init.assert_called_once()
        # Verify explicit token was passed to __init__
        assert mock_init.call_args[0][0] == "explicit-token"

    @patch("pdfdancer.pdfdancer_v1.PDFDancer._obtain_anonymous_token")
    def test_new_uses_anonymous_token_when_no_token(
        self, mock_obtain_token, clear_env_token, mock_httpx_client
    ):
        """Test that PDFDancer.new() obtains anonymous token when none provided."""
        mock_obtain_token.return_value = "anon-token-456"

        # Mock the session creation response
        mock_response = MagicMock()
        mock_response.text = "test-session-id"
        mock_httpx_client.post.return_value = mock_response

        pdf = PDFDancer.new()

        mock_obtain_token.assert_called_once()
        assert pdf._token == "anon-token-456"

    @patch("pdfdancer.pdfdancer_v1.PDFDancer._obtain_anonymous_token")
    def test_new_uses_explicit_token(self, mock_obtain_token, mock_httpx_client):
        """Test that PDFDancer.new() uses explicit token when provided."""
        # Mock the session creation response
        mock_response = MagicMock()
        mock_response.text = "test-session-id"
        mock_httpx_client.post.return_value = mock_response

        pdf = PDFDancer.new(token="explicit-token")

        mock_obtain_token.assert_not_called()
        assert pdf._token == "explicit-token"

    def test_cleanup_url_path(self):
        """Test URL path cleanup helper method."""
        # Test various combinations of base URL and path
        assert (
            PDFDancer._cleanup_url_path("http://localhost:8080", "/keys/anon")
            == "http://localhost:8080/keys/anon"
        )
        assert (
            PDFDancer._cleanup_url_path("http://localhost:8080/", "/keys/anon")
            == "http://localhost:8080/keys/anon"
        )
        assert (
            PDFDancer._cleanup_url_path("http://localhost:8080", "keys/anon")
            == "http://localhost:8080/keys/anon"
        )
        assert (
            PDFDancer._cleanup_url_path("http://localhost:8080/", "keys/anon")
            == "http://localhost:8080/keys/anon"
        )
