"""
Tests for singular selection methods (select_x instead of select_xs).

These convenience methods return the first match or None instead of a list.
"""

import pytest

from pdfdancer import StandardFonts
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture


def test_select_paragraph_at_page_level():
    """Test selecting a single paragraph at specific coordinates on a page"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # First get all paragraphs to find valid coordinates
        paragraphs = pdf.page(1).select_paragraphs()
        assert len(paragraphs) >= 1

        # Use actual coordinates from first paragraph
        first = paragraphs[0]
        x = first.position.x()
        y = first.position.y()

        # Now test the singular version
        paragraph = pdf.page(1).select_paragraph_at(x, y)
        assert paragraph is not None
        assert paragraph.internal_id == first.internal_id


def test_select_paragraph_at_no_match():
    """Test selecting a paragraph at coordinates with no match returns None"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Test coordinates where no paragraph exists
        paragraph = pdf.page(1).select_paragraph_at(10000, 10000)
        assert paragraph is None


def test_select_paragraph_starting_with():
    """Test selecting a single paragraph starting with specific text"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Test singular version
        paragraph = pdf.page(1).select_paragraph_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert paragraph is not None
        assert pytest.approx(paragraph.position.x(), rel=0, abs=1) == 64.7
        assert (
            pytest.approx(paragraph.position.y(), rel=0, abs=2) == 642
        )  # adjust for baseline/bounding box


def test_select_paragraph_starting_with_no_match():
    """Test selecting a paragraph with no matching text returns None"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(1).select_paragraph_starting_with("Nonexistent text")
        assert paragraph is None


def test_select_paragraph_matching_page_level():
    """Test selecting a single paragraph matching a regex pattern on a page"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        # Add test paragraphs
        pdf.new_paragraph().text("Invoice #12345").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()
        pdf.new_paragraph().text("Date: 2024-01-15").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 200).add()

        # Test singular version
        paragraph = pdf.page(1).select_paragraph_matching(r"Invoice #[0-9]+")
        assert paragraph is not None
        assert "Invoice #12345" in paragraph.text


def test_select_paragraph_matching_document_level():
    """Test selecting a single paragraph matching a regex pattern at document level"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        # Add test paragraphs
        pdf.new_paragraph().text("Invoice #12345").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()
        pdf.new_paragraph().text("Total: $99.99").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 200
        ).add()

        # Test singular version at document level
        paragraph = pdf.select_paragraph_matching(r"\$[0-9]+\.[0-9]+")
        assert paragraph is not None
        assert "$99.99" in paragraph.text


def test_select_paragraph_matching_no_match():
    """Test selecting a paragraph with no matching pattern returns None"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("Hello World").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()

        # Test pattern that doesn't match
        paragraph = pdf.page(1).select_paragraph_matching(r"[0-9]{5}")
        assert paragraph is None


def test_select_text_line_at():
    """Test selecting a single text line at specific coordinates"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        # Add a paragraph with multiple lines
        pdf.new_paragraph().text("Line 1\nLine 2\nLine 3").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 100).add()

        # Get the actual text lines to find their coordinates
        text_lines = pdf.page(1).select_text_lines()
        assert len(text_lines) >= 1

        first_line = text_lines[0]
        x = first_line.position.x()
        y = first_line.position.y()

        # Select first text line at the actual coordinates
        text_line = pdf.page(1).select_text_line_at(x, y)
        assert text_line is not None
        assert text_line.internal_id == first_line.internal_id


def test_select_text_line_starting_with():
    """Test selecting a single text line starting with specific text"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("First Line\nSecond Line").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 100).add()

        text_line = pdf.page(1).select_text_line_starting_with("Second Line")
        assert text_line is not None
        assert "Second Line" in text_line.text


def test_select_text_line_matching():
    """Test selecting a single text line matching a regex pattern"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("Total: $99.99\nItems: 5").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 100).add()

        text_line = pdf.page(1).select_text_line_matching(r"\$[0-9]+\.[0-9]+")
        assert text_line is not None
        assert "$99.99" in text_line.text


def test_select_image_at():
    """Test selecting a single image at specific coordinates"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # First check if there are any images
        images = pdf.page(1).select_images()
        if len(images) > 0:
            first_image = images[0]
            x = first_image.position.x()
            y = first_image.position.y()

            # Test singular version
            image = pdf.page(1).select_image_at(x, y)
            assert image is not None
            assert image.internal_id == first_image.internal_id


def test_select_image_at_no_match():
    """Test selecting an image at coordinates with no match returns None"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        image = pdf.page(1).select_image_at(10000, 10000)
        assert image is None


def test_select_form_field_by_name():
    """Test selecting a single form field by name at document level"""
    base_url, token, pdf_path = _require_env_and_fixture("mixed-form-types.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Test singular version
        field = pdf.select_form_field_by_name("firstName")
        assert field is not None
        assert field.name == "firstName"


def test_select_form_field_by_name_page_level():
    """Test selecting a single form field by name at page level"""
    base_url, token, pdf_path = _require_env_and_fixture("mixed-form-types.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Test singular version at page level
        field = pdf.page(1).select_form_field_by_name("firstName")
        assert field is not None
        assert field.name == "firstName"


def test_select_form_field_by_name_no_match():
    """Test selecting a form field with non-existent name returns None"""
    base_url, token, pdf_path = _require_env_and_fixture("mixed-form-types.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        field = pdf.select_form_field_by_name("nonexistent-field")
        assert field is None


def test_select_form_field_at():
    """Test selecting a single form field at specific coordinates"""
    base_url, token, pdf_path = _require_env_and_fixture("mixed-form-types.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # First get all form fields to find coordinates
        fields = pdf.page(1).select_form_fields()
        if len(fields) > 0:
            first_field = fields[0]
            x = first_field.position.x()
            y = first_field.position.y()

            # Test singular version
            field = pdf.page(1).select_form_field_at(x, y)
            assert field is not None
            assert field.internal_id == first_field.internal_id


def test_select_path_at():
    """Test selecting a single path at specific coordinates"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        # Add a path (line)
        pdf.page(1).new_line().from_point(100, 100).to_point(200, 200).add()

        # Test singular version
        path = pdf.page(1).select_path_at(100, 100)
        assert path is not None


def test_select_path_at_no_match():
    """Test selecting a path at coordinates with no match returns None"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        path = pdf.page(1).select_path_at(10000, 10000)
        assert path is None


def test_select_form_at():
    """Test selecting a single form at specific coordinates"""
    base_url, token, pdf_path = _require_env_and_fixture("form-xobject-example.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # First get all forms to find coordinates
        forms = pdf.page(1).select_forms()
        if len(forms) > 0:
            first_form = forms[0]
            x = first_form.position.x()
            y = first_form.position.y()

            # Test singular version
            form = pdf.page(1).select_form_at(x, y)
            assert form is not None
            assert form.internal_id == first_form.internal_id


def test_singular_methods_return_type():
    """Test that singular methods return proper types (not list)"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("Test").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()

        # Test that singular method returns single object, not list
        paragraph = pdf.page(1).select_paragraph_at(100, 100)
        assert paragraph is not None
        assert not isinstance(paragraph, list)

        # Test that None is returned when no match (not empty list)
        no_match = pdf.page(1).select_paragraph_at(10000, 10000)
        assert no_match is None
        assert not isinstance(no_match, list)


def test_singular_methods_consistency():
    """Test that singular methods return the same first element as plural methods"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("Test 1").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()
        pdf.new_paragraph().text("Test 2").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 120
        ).add()

        # Test consistency between singular and plural methods
        paragraphs = pdf.page(1).select_paragraphs_at(100, 100)
        paragraph = pdf.page(1).select_paragraph_at(100, 100)

        assert len(paragraphs) > 0
        assert paragraph is not None
        assert paragraph.internal_id == paragraphs[0].internal_id
        assert paragraph.text == paragraphs[0].text
