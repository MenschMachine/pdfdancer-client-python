import os

import pytest

from pdfdancer import HttpClientException, PDFDancer, ValidationException
from tests.e2e import _require_env_and_fixture


def test_env_vars():
    base_url, _, pdf_path = _require_env_and_fixture("Showcase.pdf")
    original_base_url_env = os.environ.get("PDFDANCER_BASE_URL")
    original_token_env = os.environ.get("PDFDANCER_TOKEN")
    try:
        os.environ.pop("PDFDANCER_TOKEN", None)

        # With the anonymous token fallback, opening without a token should now succeed
        # (it will automatically obtain an anonymous token)
        # This test now verifies that the client works without PDFDANCER_TOKEN set
        with PDFDancer.open(pdf_path, base_url=base_url) as pdf:
            # Verify we got a valid session
            assert pdf._session_id is not None
            assert pdf._token is not None  # Should have obtained an anonymous token

        os.environ["PDFDANCER_TOKEN"] = "42"
        with PDFDancer.open(pdf_path, base_url=base_url) as pdf:
            pass

        os.environ["PDFDANCER_BASE_URL"] = "https://www.google.com"
        with pytest.raises(HttpClientException) as exc_info:
            with PDFDancer.open(pdf_path) as pdf:
                pass

        os.environ["PDFDANCER_BASE_URL"] = "https://api.pdfdancer.com"
        with pytest.raises(ValidationException) as exc_info:
            with PDFDancer.open(pdf_path) as pdf:
                pass
        assert (
            "Authentication with the PDFDancer API failed. Confirm that your API token is valid, has not expired"
            in str(exc_info.value)
        )
    finally:
        if original_base_url_env is not None:
            os.environ["PDFDANCER_BASE_URL"] = original_base_url_env
        elif "PDFDANCER_BASE_URL" in os.environ:
            del os.environ["PDFDANCER_BASE_URL"]
        if original_token_env is not None:
            os.environ["PDFDANCER_TOKEN"] = original_token_env
        elif "PDFDANCER_TOKEN" in os.environ:
            del os.environ["PDFDANCER_TOKEN"]
