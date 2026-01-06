"""E2E tests for template replacement functionality."""

import pytest

from pdfdancer import ReflowPreset, TemplateReplacement, ValidationException
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_replace_single_template():
    """Test replacing a single template placeholder."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Verify original text exists
        (
            PDFAssertions(pdf)
            .assert_paragraph_exists("Showcase")
            .assert_textline_exists("PDFDancer Showcase")
        )

        # Replace the existing "Showcase" text
        result = pdf.apply_replacements([
            TemplateReplacement(placeholder="Showcase", text="Replaced"),
        ])

        assert result is True

        # Verify replacement worked
        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist("Showcase")
            .assert_textline_exists("PDFDancer Replaced")
            .assert_textline_exists("Replaced.pdf")
        )


def test_replace_multiple_templates():
    """Test replacing multiple template placeholders."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Replace multiple placeholders
        result = pdf.apply_replacements([
            TemplateReplacement(placeholder="PDFDancer", text="TestApp"),
            TemplateReplacement(placeholder="Engine", text="System"),
        ])

        assert result is True

        # Verify all replacements worked
        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist("PDFDancer")
            .assert_textline_does_not_exist("Engine")
            .assert_textline_exists("TestApp")
            .assert_textline_exists("System")
        )


def test_replace_template_on_specific_page():
    """Test replacing template placeholders on a specific page only."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Verify original text exists on page 1
        (
            PDFAssertions(pdf)
            .assert_paragraph_exists("Showcase")
        )

        # Replace only on page 1
        result = pdf.page(1).apply_replacements([
            TemplateReplacement(placeholder="Showcase", text="PageOneOnly"),
        ])

        assert result is True

        # Verify page 1 replacement
        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist("Showcase")
            .assert_textline_exists("PageOneOnly")
        )


def test_replace_template_with_reflow_best_effort():
    """Test template replacement with BEST_EFFORT reflow preset."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Verify original text exists
        (
            PDFAssertions(pdf)
            .assert_paragraph_exists("Showcase")
        )

        # Replace with longer text using BEST_EFFORT reflow
        result = pdf.apply_replacements(
            [TemplateReplacement(placeholder="Showcase", text="ThisIsAMuchLongerReplacementText")],
            reflow_preset=ReflowPreset.BEST_EFFORT,
        )

        assert result is True

        # Verify replacement with reflow
        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist("Showcase")
            .assert_textline_exists("ThisIsAMuchLongerReplacementText")
        )


def test_replace_template_with_reflow_none():
    """Test template replacement with NONE reflow preset."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Verify original text exists
        (
            PDFAssertions(pdf)
            .assert_paragraph_exists("Showcase")
        )

        # Replace without reflow
        result = pdf.apply_replacements(
            [TemplateReplacement(placeholder="Showcase", text="NoReflow")],
            reflow_preset=ReflowPreset.NONE,
        )

        assert result is True

        # Verify replacement without reflow
        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist("Showcase")
            .assert_textline_exists("NoReﬂow")  # TODO where the hell is that ligature coming from?
        )


def test_replace_template_empty_list_raises():
    """Test that replacing with an empty list raises ValidationException."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        with pytest.raises(ValidationException):
            pdf.apply_replacements([])


def test_replace_template_page_level_empty_list_raises():
    """Test that page-level replacement with empty list raises ValidationException."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        with pytest.raises(ValidationException):
            pdf.page(1).apply_replacements([])


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
