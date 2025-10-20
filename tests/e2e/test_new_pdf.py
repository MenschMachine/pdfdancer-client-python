import pytest

from pdfdancer import PDFDancer, PageSize, Orientation, StandardFonts, Color
from tests.e2e import _require_env
from tests.e2e.pdf_assertions import PDFAssertions


def test_create_blank_pdf_defaults():
    """Test creating a blank PDF with default parameters"""
    base_url, token = _require_env()

    with PDFDancer.new(token=token, base_url=base_url) as pdf:
        pages = pdf.pages()
        assert len(pages) == 1, "Default blank PDF should have 1 page"

        pdf_bytes = pdf.get_bytes()
        assert len(pdf_bytes) > 0, "PDF bytes should not be empty"
        assert pdf_bytes[:4] == b'%PDF', "PDF should start with PDF signature"

    (
        PDFAssertions(pdf).assert_total_number_of_elements(0)
    )


def test_create_blank_pdf_with_custom_params():
    """Test creating a blank PDF with custom page size and orientation"""
    base_url, token = _require_env()

    with PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.LANDSCAPE,
            initial_page_count=3
    ) as pdf:
        pages = pdf.pages()
        assert len(pages) == 3, "PDF should have 3 pages"
    (
        PDFAssertions(pdf)
        .assert_total_number_of_elements(0)
        .assert_page_count(3)
        .assert_page_dimension(PageSize.A4.height, PageSize.A4.width)
    )


def test_create_blank_pdf_with_string_params():
    """Test creating a blank PDF with string parameters"""
    base_url, token = _require_env()

    with PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size="LETTER",
            orientation="PORTRAIT",
            initial_page_count=2
    ) as pdf:
        pages = pdf.pages()
        assert len(pages) == 2, "PDF should have 2 pages"

    (
        PDFAssertions(pdf)
        .assert_total_number_of_elements(0)
        .assert_page_count(2)
        .assert_page_dimension(PageSize.LETTER.width, PageSize.LETTER.height, Orientation.PORTRAIT)
    )


def test_create_blank_pdf_add_content():
    """Test creating a blank PDF and adding content"""
    base_url, token = _require_env()

    with PDFDancer.new(token=token, base_url=base_url) as pdf:
        (
            pdf.new_paragraph()
            .text("Hello from blank PDF")
            .font(StandardFonts.COURIER_BOLD_OBLIQUE, 9)
            .color(Color(0, 255, 00))
            .at(0, 100, 201.5)
            .add()
        )

        paragraphs = pdf.select_paragraphs()
        assert len(paragraphs) == 1, "Should have one paragraph"
        assert paragraphs[0].get_text() == "Hello from blank PDF"

    (
        PDFAssertions(pdf)
        .assert_paragraph_is_at("Hello from blank PDF", 100, 201.5)
    )


def test_create_blank_pdf_add_page():
    base_url, token = _require_env()

    with PDFDancer.new(token=token, base_url=base_url) as pdf:
        assert 1 == len(pdf.pages())
        page_ref = pdf.new_page()
        assert 1 == page_ref.position.page_index
        assert Orientation.PORTRAIT == page_ref.orientation
        assert 2 == len(pdf.pages())

    (
        PDFAssertions(pdf)
        .assert_page_count(2)
    )


def test_create_blank_pdf_invalid_page_count():
    """Test that invalid page count raises validation error"""
    base_url, token = _require_env()

    from pdfdancer import ValidationException

    with pytest.raises(ValidationException) as exc_info:
        PDFDancer.new(
            token=token,
            base_url=base_url,
            initial_page_count=0
        )

    assert "Initial page count must be at least 1" in str(exc_info.value)
