"""E2E tests for redaction functionality."""

import pytest

from pdfdancer import Color, RedactResponse, StandardFonts
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_redact_single_paragraph():
    """Test redacting a single paragraph using object.redact()"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        # Add a paragraph
        pdf.new_paragraph().text("Confidential Information").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 100).add()

        # Select and redact the paragraph
        paragraphs = pdf.select_paragraphs()
        assert len(paragraphs) == 1

        result = paragraphs[0].redact()
        assert result is True

        # Verify the paragraph content is redacted
        assertions = PDFAssertions(pdf)
        assertions.assert_textline_does_not_exist("Confidential Information")
        assertions.assert_textline_exists("[REDACTED]")


def test_redact_with_custom_replacement():
    """Test redacting with custom replacement text"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("Secret Data").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()

        paragraphs = pdf.select_paragraphs()
        assert len(paragraphs) == 1

        result = paragraphs[0].redact(replacement="[REMOVED]")
        assert result is True

        assertions = PDFAssertions(pdf)
        assertions.assert_textline_does_not_exist("Secret Data")
        assertions.assert_textline_exists("[REMOVED]")


def test_batch_redact_multiple_paragraphs():
    """Test batch redaction of multiple paragraphs using pdf.redact()"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        # Add multiple paragraphs
        pdf.new_paragraph().text("SSN: 123-45-6789").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()
        pdf.new_paragraph().text("Phone: 555-1234").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 200
        ).add()
        pdf.new_paragraph().text("Public Info").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 300
        ).add()

        # Select paragraphs to redact (first two)
        all_paragraphs = pdf.select_paragraphs()
        assert len(all_paragraphs) == 3

        to_redact = all_paragraphs[:2]
        result = pdf.redact(to_redact, replacement="[CONFIDENTIAL]")

        assert isinstance(result, RedactResponse)
        assert result.success is True
        assert result.count == 2

        assertions = PDFAssertions(pdf)
        assertions.assert_textline_does_not_exist("SSN: 123-45-6789")
        assertions.assert_textline_does_not_exist("Phone: 555-1234")
        assertions.assert_paragraph_exists("Public Info")

        # Verify that replacement text exists (may have multiple instances)
        redacted_lines = assertions.pdf.page(1).select_text_lines_starting_with(
            "[CONFIDENTIAL]"
        )
        assert len(redacted_lines) == 2, f"Expected 2 redacted lines, got {len(redacted_lines)}"


def test_redact_with_placeholder_color():
    """Test redaction with custom placeholder color for images"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("Test").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()

        paragraphs = pdf.select_paragraphs()
        gray = Color(128, 128, 128)
        result = pdf.redact(paragraphs, replacement="[X]", placeholder_color=gray)

        assert result.success is True
        assert result.count == 1


def test_redact_response_fields():
    """Test that RedactResponse has all expected fields"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("Data").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()

        paragraphs = pdf.select_paragraphs()
        result = pdf.redact(paragraphs)

        assert hasattr(result, "count")
        assert hasattr(result, "success")
        assert hasattr(result, "warnings")
        assert isinstance(result.count, int)
        assert isinstance(result.success, bool)
        assert isinstance(result.warnings, list)


def test_redact_empty_list_raises():
    """Test that redacting an empty list raises ValidationException"""
    from pdfdancer import ValidationException

    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        with pytest.raises(ValidationException):
            pdf.redact([])
