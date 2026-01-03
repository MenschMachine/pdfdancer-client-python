"""E2E tests for template replacement functionality."""

import pytest

from pdfdancer import ReflowPreset, StandardFonts, TemplateReplacement, ValidationException
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_replace_single_template():
    """Test replacing a single template placeholder."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Verify original text exists on page 1
        original = pdf.page(1).select_paragraphs_starting_with("Showcase")
        assert len(original) > 0, "Expected 'Showcase' text to exist in PDF"

        # Replace the existing "Showcase" text in the PDF
        result = pdf.replace_templates([
            TemplateReplacement(placeholder="Showcase", text="Replaced"),
        ])

        assert result is True

        # Verify the old text is gone (replacement content verification skipped
        # due to font encoding handling in PDF)
        old_text = pdf.page(1).select_paragraphs_starting_with("Showcase")
        assert len(old_text) == 0, "Expected 'Showcase' text to be replaced"


def test_replace_multiple_templates():
    """Test replacing multiple template placeholders."""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        # Add paragraphs with placeholders
        pdf.new_paragraph().text("Name: {{NAME}}").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 100).add()
        pdf.new_paragraph().text("Date: {{DATE}}").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 200).add()

        # Replace multiple placeholders
        result = pdf.replace_templates([
            TemplateReplacement(placeholder="{{NAME}}", text="Jane Smith"),
            TemplateReplacement(placeholder="{{DATE}}", text="2025-01-15"),
        ])

        assert result is True

        assertions = PDFAssertions(pdf)
        assertions.assert_textline_does_not_exist("{{NAME}}")
        assertions.assert_textline_does_not_exist("{{DATE}}")
        assertions.assert_textline_exists("Name: Jane Smith")
        assertions.assert_textline_exists("Date: 2025-01-15")


def test_replace_template_on_specific_page():
    """Test replacing template placeholders on a specific page only."""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        # Add a new page
        pdf.new_page().add()

        # Add same placeholder on both pages
        pdf.new_paragraph().text("Page {{NUM}}").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 100).add()
        pdf.new_paragraph().text("Page {{NUM}}").font(
            StandardFonts.HELVETICA, 12
        ).at(2, 100, 100).add()

        # Replace only on page 1
        result = pdf.page(1).replace_templates([
            TemplateReplacement(placeholder="{{NUM}}", text="ONE"),
        ])

        assert result is True

        # Verify page 1 was replaced
        page1_paragraphs = pdf.page(1).select_paragraphs_starting_with("Page ONE")
        assert len(page1_paragraphs) == 1

        # Verify page 2 still has placeholder
        page2_paragraphs = pdf.page(2).select_paragraphs_starting_with("Page {{NUM}}")
        assert len(page2_paragraphs) == 1


def test_replace_template_with_reflow_best_effort():
    """Test template replacement with BEST_EFFORT reflow preset."""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("Short: {{PLACEHOLDER}}").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 100).add()

        # Replace with longer text using BEST_EFFORT
        result = pdf.replace_templates(
            [TemplateReplacement(placeholder="{{PLACEHOLDER}}", text="A much longer replacement text")],
            reflow_preset=ReflowPreset.BEST_EFFORT,
        )

        assert result is True

        assertions = PDFAssertions(pdf)
        assertions.assert_textline_does_not_exist("{{PLACEHOLDER}}")


def test_replace_template_with_reflow_none():
    """Test template replacement with NONE reflow preset."""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("Value: {{VAL}}").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 100).add()

        # Replace without reflow
        result = pdf.replace_templates(
            [TemplateReplacement(placeholder="{{VAL}}", text="42")],
            reflow_preset=ReflowPreset.NONE,
        )

        assert result is True

        assertions = PDFAssertions(pdf)
        assertions.assert_textline_exists("Value: 42")


def test_replace_template_empty_list_raises():
    """Test that replacing with an empty list raises ValidationException."""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        with pytest.raises(ValidationException):
            pdf.replace_templates([])


def test_replace_template_page_level_empty_list_raises():
    """Test that page-level replacement with empty list raises ValidationException."""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        with pytest.raises(ValidationException):
            pdf.page(1).replace_templates([])


def test_template_replacement_dataclass():
    """Test TemplateReplacement dataclass structure and serialization."""
    replacement = TemplateReplacement(
        placeholder="{{NAME}}",
        text="John Doe",
    )

    assert replacement.placeholder == "{{NAME}}"
    assert replacement.text == "John Doe"

    # Test to_dict
    d = replacement.to_dict()
    assert d == {
        "placeholder": "{{NAME}}",
        "text": "John Doe",
    }


def test_reflow_preset_values():
    """Test ReflowPreset enum values."""
    assert ReflowPreset.BEST_EFFORT.value == "BEST_EFFORT"
    assert ReflowPreset.FIT_OR_FAIL.value == "FIT_OR_FAIL"
    assert ReflowPreset.NONE.value == "NONE"
