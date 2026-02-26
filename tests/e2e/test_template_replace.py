"""E2E tests for template replacement functionality."""

from pathlib import Path

import pytest

from pdfdancer import Color, Font, ReflowPreset, ValidationException
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
        result = pdf.apply_replacements({"Showcase": "Replaced"})

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
        result = pdf.apply_replacements({
            "PDFDancer": "TestApp",
            "Engine": "System",
        })

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
        result = pdf.page(1).apply_replacements({"Showcase": "PageOneOnly"})

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
            {"Showcase": "ThisIsAMuchLongerReplacementText"},
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
            {"Showcase": "NoReflow"},
            reflow_preset=ReflowPreset.NONE,
        )

        assert result is True

        # Verify replacement without reflow
        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist("Showcase")
            .assert_textline_exists("NoReﬂow")  # TODO where the hell is that ligature coming from?
        )


def test_replace_template_empty_dict_raises():
    """Test that replacing with an empty dict raises ValidationException."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        with pytest.raises(ValidationException):
            pdf.apply_replacements({})


def test_replace_template_page_level_empty_dict_raises():
    """Test that page-level replacement with empty dict raises ValidationException."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        with pytest.raises(ValidationException):
            pdf.page(1).apply_replacements({})


def test_replace_template_with_font():
    """Test template replacement with custom font."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        result = pdf.apply_replacements({
            "Showcase": {
                "text": "FontTest",
                "font": Font("Helvetica-Bold", 14),
            }
        })

        assert result is True

        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist("Showcase")
            .assert_textline_exists("FontTest")
        )


def test_replace_template_with_color():
    """Test template replacement with custom color."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        result = pdf.apply_replacements({
            "Showcase": {
                "text": "ColorTest",
                "color": Color(255, 0, 0),
            }
        })

        assert result is True

        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist("Showcase")
            .assert_textline_exists("ColorTest")
        )


def test_replace_template_with_font_and_color():
    """Test template replacement with both font and color."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        result = pdf.apply_replacements({
            "Showcase": {
                "text": "StyledText",
                "font": Font("Helvetica-Bold", 16),
                "color": Color(0, 100, 0),
            }
        })

        assert result is True

        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist("Showcase")
            .assert_textline_exists("StyledText")
        )


def test_reflow_preset_values():
    """Test ReflowPreset enum values."""
    assert ReflowPreset.BEST_EFFORT.value == "BEST_EFFORT"
    assert ReflowPreset.FIT_OR_FAIL.value == "FIT_OR_FAIL"
    assert ReflowPreset.NONE.value == "NONE"


def test_replace_template_with_image():
    """Test replacing a placeholder with an image file (natural size)."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")
    logo_path = Path(__file__).resolve().parent.parent / "fixtures" / "logo-80.png"
    assert logo_path.exists(), "logo-80.png fixture not found"

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Count images before replacement
        images_before = pdf.select_images()
        count_before = len(images_before)

        # Replace "Showcase" placeholder with an image
        result = pdf.apply_replacements({
            "Showcase": {"image": logo_path},
        })

        assert result is True

        # The placeholder text should be gone
        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist("Showcase")
        )

        # There should be more images now
        images_after = pdf.select_images()
        assert len(images_after) > count_before


def test_replace_template_with_image_explicit_size():
    """Test replacing a placeholder with an image file with explicit width/height."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")
    logo_path = Path(__file__).resolve().parent.parent / "fixtures" / "logo-80.png"
    assert logo_path.exists(), "logo-80.png fixture not found"

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Replace "Showcase" placeholder with a sized image
        result = pdf.apply_replacements({
            "Showcase": {"image": logo_path, "width": 50, "height": 50},
        })

        assert result is True

        # The placeholder text should be gone
        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist("Showcase")
        )
