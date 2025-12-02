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


def test_redact_image():
    """Test redacting an image replaces it with a placeholder rectangle"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        images = pdf.page(1).select_images()
        assert len(images) == 2

        # Get image position before redaction
        image = images[0]
        original_x = image.position.x()
        original_y = image.position.y()

        result = image.redact()
        assert result is True

        # Image should be gone from original position
        assertions = PDFAssertions(pdf)
        assertions.assert_no_image_at(original_x, original_y, 1)

        # Should now have only 1 image on page 1
        assertions.assert_number_of_images(1, 1)


def test_redact_image_with_placeholder_color():
    """Test redacting image with custom placeholder color"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        images = pdf.page(1).select_images()
        assert len(images) == 2

        # Batch redact with custom color
        red = Color(255, 0, 0)
        result = pdf.redact(images, placeholder_color=red)

        assert result.success is True
        assert result.count == 2

        # Both images should be gone
        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_images(0, 1)


def test_redact_path():
    """Test redacting a path"""
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths_at(80, 720)
        assert len(paths) == 1
        path = paths[0]

        result = path.redact()
        assert result is True

        # Path should be gone
        assertions = PDFAssertions(pdf)
        assertions.assert_no_path_at(80, 720)
        assertions.assert_number_of_paths(8)


def test_redact_multiple_paths():
    """Test batch redacting multiple paths"""
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        all_paths = pdf.select_paths()
        assert len(all_paths) == 9

        # Redact first 3 paths
        to_redact = all_paths[:3]
        result = pdf.redact(to_redact)

        assert result.success is True
        assert result.count == 3

        # Should have 6 paths remaining
        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(6)


def test_redact_form_field():
    """Test redacting a form field replaces its content"""
    base_url, token, pdf_path = _require_env_and_fixture("mixed-form-types.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        form_fields = pdf.select_form_fields()
        assert len(form_fields) == 10

        # Redact a text field form field
        text_fields = [f for f in form_fields if f.object_type.value == "TEXT_FIELD"]
        assert len(text_fields) > 0

        form_field = text_fields[0]
        result = form_field.redact()

        # Redaction should succeed
        assert result is True


def test_redact_multiple_form_fields():
    """Test batch redacting multiple form fields"""
    base_url, token, pdf_path = _require_env_and_fixture("mixed-form-types.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        form_fields = pdf.select_form_fields()
        assert len(form_fields) == 10

        # Redact first 5 form fields
        to_redact = form_fields[:5]
        result = pdf.redact(to_redact)

        # Operation should succeed (some may fail with warnings)
        assert result.success is True
        assert result.count >= 1

        # Check for any warnings about failed redactions
        if result.warnings:
            # Some form field types may not support redaction
            assert all("Failed to redact" in w for w in result.warnings)


def test_redact_mixed_object_types():
    """Test batch redacting a mix of paragraphs and images"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraphs = pdf.page(1).select_paragraphs()
        images = pdf.page(1).select_images()

        initial_para_count = len(paragraphs)
        initial_image_count = len(images)

        assert initial_para_count > 0
        assert initial_image_count > 0

        # Redact one paragraph and one image
        to_redact = [paragraphs[0], images[0]]
        result = pdf.redact(to_redact, replacement="[MIXED_REDACT]")

        assert result.success is True
        assert result.count == 2

        # Verify counts decreased
        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_images(initial_image_count - 1, 1)
