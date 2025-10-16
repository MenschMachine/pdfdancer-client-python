import os

import pytest

from tests.e2e import _require_env_and_fixture
from pdfdancer import PDFDancer, ValidationException, HttpClientException


def test_env_vars():
    base_url, _, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")
    os.environ.pop("PDFDANCER_TOKEN", None)

    with pytest.raises(ValidationException) as exc_info:
        with PDFDancer.open(pdf_path, base_url=base_url) as pdf:
            pass
    assert "Missing PDFDancer API token. Pass a token via the `token` argument or set the PDFDANCER_TOKEN environment variable." == str(
        exc_info.value)

    os.environ["PDFDANCER_TOKEN"] = "42"
    with PDFDancer.open(pdf_path, base_url=base_url) as pdf:
        pass

    os.environ["PDFDANCER_BASE_URL"] = "http://www.google.com"
    with pytest.raises(HttpClientException) as exc_info:
        with PDFDancer.open(pdf_path) as pdf:
            pass

    os.environ["PDFDANCER_BASE_URL"] = "https://api.pdfdancer.com"
    with pytest.raises(ValidationException) as exc_info:
        with PDFDancer.open(pdf_path) as pdf:
            pass
    assert "Authentication with the PDFDancer API failed. Confirm that your API token is valid, has not expired" in str(
        exc_info.value)
