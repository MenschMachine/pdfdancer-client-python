import requests
import pytest

from pdfdancer import ValidationException
from pdfdancer.pdfdancer_v1 import PDFDancer


def test_open_without_token_reports_actionable_message():
    with pytest.raises(ValidationException) as exc_info:
        PDFDancer.open(pdf_data=b"%PDF", token="")

    message = str(exc_info.value)
    assert "Missing PDFDancer API token" in message
    assert "PDFDANCER_TOKEN" in message


def test_create_session_unauthorized_reports_guidance(monkeypatch):
    class FakeResponse:
        status_code = 401
        text = "Unauthorized"

        def json(self):
            return {"message": "Unauthorized"}

    def fake_post(self, *args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "post", fake_post)

    with pytest.raises(ValidationException) as exc_info:
        PDFDancer(token="bad-token", pdf_data=b"%PDF", base_url="https://api.example.com")

    message = str(exc_info.value)
    assert "Authentication with the PDFDancer API failed" in message
    assert "Server response: Unauthorized" in message
    assert "PDFDANCER_TOKEN" in message
