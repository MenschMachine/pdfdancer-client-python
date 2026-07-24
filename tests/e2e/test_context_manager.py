"""E2E coverage for the Python-only context-manager convenience."""

from pdfdancer import PDFDancer
from tests.e2e import _require_env_and_fixture


def test_context_manager_opens_a_usable_session_and_closes_transport():
    base_url, token, fixture = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(fixture, token=token, base_url=base_url) as pdf:
        assert len(pdf.pages()) > 0
        transport = pdf._client

    assert transport.is_closed
