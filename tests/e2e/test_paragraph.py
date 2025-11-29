import pytest

from pdfdancer import Color, FontType, StandardFonts
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_find_paragraphs_by_position():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraphs = pdf.select_paragraphs()
        assert 20 <= len(paragraphs) <= 22  # strange, but differs on linux

        paras_page0 = pdf.page(1).select_paragraphs()
        assert len(paras_page0) == 3

        first = paras_page0[0]
        assert first.position is not None
        assert pytest.approx(first.position.x(), rel=0, abs=1) == 180
        assert (
            pytest.approx(first.position.y(), rel=0, abs=1) == 749
        )  # adjusted for baseline/bounding box

        last = paras_page0[-1]
        assert last.position is not None
        assert pytest.approx(last.position.x(), rel=0, abs=1) == 69.3
        assert pytest.approx(last.position.y(), rel=0, abs=2) == 46.7

        assert last.object_ref().status is not None
        # assert last.object_ref().status.is_encodable()
        assert last.object_ref().status.font_type == FontType.EMBEDDED
        assert not last.object_ref().status.is_modified()


def test_find_paragraphs_by_text():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paras = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(paras) == 1
        p = paras[0]
        assert pytest.approx(p.position.x(), rel=0, abs=1) == 64.7
        assert (
            pytest.approx(p.position.y(), rel=0, abs=2) == 642
        )  # adjust for baseline/bounding box


def test_select_paragraphs_matching_document_level():
    """Test document-level regex pattern matching for paragraphs"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # Get all paragraphs to ensure PDF is loaded
        all_paras = pdf.select_paragraphs()
        assert len(all_paras) > 0

        # Test matching any word characters (should match most paragraphs)
        matches = pdf.select_paragraphs_matching(r"\w+")
        assert len(matches) >= 1

        # Test matching any paragraph that contains text
        matches = pdf.select_paragraphs_matching(r".")
        assert len(matches) >= 1


def test_select_paragraphs_matching_with_special_characters():
    """Test regex pattern matching with special characters and numbers"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    # Create a new PDF with test data
    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        # Add paragraphs with various patterns
        pdf.new_paragraph().text("Invoice #12345").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()
        pdf.new_paragraph().text("Date: 2024-01-15").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 200).add()
        pdf.new_paragraph().text("Total: $99.99").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 300
        ).add()
        pdf.new_paragraph().text("Email: test@example.com").font(
            StandardFonts.HELVETICA, 12
        ).at(1, 100, 400).add()

        # Test matching invoice numbers
        invoice_matches = pdf.select_paragraphs_matching(r"Invoice #[0-9]+")
        assert len(invoice_matches) == 1
        assert "Invoice #12345" in invoice_matches[0].text

        # Test matching dates in YYYY-MM-DD format
        date_matches = pdf.select_paragraphs_matching(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
        assert len(date_matches) == 1
        assert "2024-01-15" in date_matches[0].text

        # Test matching dollar amounts
        dollar_matches = pdf.select_paragraphs_matching(r"\$[0-9]+\.[0-9]+")
        assert len(dollar_matches) == 1
        assert "$99.99" in dollar_matches[0].text

        # Test matching email addresses
        email_matches = pdf.select_paragraphs_matching(
            r"[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-zA-Z]+"
        )
        assert len(email_matches) == 1
        assert "test@example.com" in email_matches[0].text


def test_select_paragraphs_matching_multiple_pages():
    """Test regex pattern matching across multiple pages"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(
        token=token, base_url=base_url, timeout=30.0, initial_page_count=3
    ) as pdf:
        # Add paragraphs to different pages
        pdf.new_paragraph().text("Chapter 1: Introduction").font(
            StandardFonts.HELVETICA, 14
        ).at(1, 100, 100).add()

        pdf.new_paragraph().text("Section 1.1").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 200
        ).add()

        pdf.new_paragraph().text("Chapter 2: Methods").font(
            StandardFonts.HELVETICA, 14
        ).at(1, 100, 100).add()
        pdf.new_paragraph().text("Section 2.1").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 200
        ).add()

        pdf.new_paragraph().text("Chapter 3: Results").font(
            StandardFonts.HELVETICA, 14
        ).at(2, 100, 100).add()
        pdf.new_paragraph().text("Section 3.1").font(StandardFonts.HELVETICA, 12).at(
            2, 100, 200
        ).add()

        # Test matching all chapters (document-level)
        chapter_matches = pdf.select_paragraphs_matching(r"^Chapter [0-9]+:")
        assert len(chapter_matches) == 3
        assert all("Chapter" in p.text for p in chapter_matches)

        # Test matching all sections (document-level)
        section_matches = pdf.select_paragraphs_matching(r"^Section [0-9]+\.[0-9]+")
        assert len(section_matches) == 3
        assert all("Section" in p.text for p in section_matches)

        # Compare with page-level matching
        page1_chapters = pdf.page(1).select_paragraphs_matching(r"^Chapter [0-9]+:")
        assert len(page1_chapters) == 2
        assert "Chapter 2" in page1_chapters[1].text


def test_select_paragraphs_matching_empty_results():
    """Test regex pattern matching with no matches"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("Hello World").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()
        pdf.new_paragraph().text("Goodbye Moon").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 200
        ).add()

        # Test pattern that doesn't match anything
        no_matches = pdf.select_paragraphs_matching(r"[0-9]{5}")
        assert len(no_matches) == 0

        # Test pattern that doesn't match
        no_matches = pdf.select_paragraphs_matching(r"^Nonexistent")
        assert len(no_matches) == 0


def test_select_paragraphs_matching_case_sensitivity():
    """Test that regex pattern matching is case-sensitive"""
    base_url, token, _ = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.new(token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph().text("UPPERCASE TEXT").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 100
        ).add()
        pdf.new_paragraph().text("lowercase text").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 200
        ).add()
        pdf.new_paragraph().text("MixedCase Text").font(StandardFonts.HELVETICA, 12).at(
            1, 100, 300
        ).add()

        # Test case-sensitive matching
        uppercase_matches = pdf.select_paragraphs_matching(r"UPPERCASE")
        assert len(uppercase_matches) == 1
        assert "UPPERCASE" in uppercase_matches[0].text

        lowercase_matches = pdf.select_paragraphs_matching(r"lowercase")
        assert len(lowercase_matches) == 1
        assert "lowercase" in lowercase_matches[0].text

        # Test case-insensitive pattern
        case_insensitive_matches = pdf.select_paragraphs_matching(r"(?i)text")
        assert len(case_insensitive_matches) == 3


def test_delete_paragraph():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        paragraph.delete()
        remaining = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert remaining == []


def test_move_paragraph():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        paragraph.move_to(0.1, 300)
        moved = pdf.page(1).select_paragraphs_at(0.1, 300)[0]
        assert moved is not None

        assert moved.object_ref().status is not None
        # assert moved.object_ref().status.is_encodable()
        assert moved.object_ref().status.font_type == FontType.EMBEDDED
        assert not moved.object_ref().status.is_modified()


def test_modify_paragraph():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        (
            paragraph.edit()
            .replace("Awesomely\nObvious!")
            .font("Helvetica", 12)
            .line_spacing(0.7)
            .move_to(300.1, 500)
            .apply()
        )

        moved = pdf.page(1).select_paragraphs_at(300.1, 500)[0]
        assert moved.object_ref().status is not None
        # assert moved.object_ref().status.is_encodable()
        assert moved.object_ref().status.font_type == FontType.STANDARD
        assert moved.object_ref().status.is_modified()

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Awesomely", "Helvetica", 12)
            .assert_textline_has_font("Obvious!", "Helvetica", 12)
            .assert_textline_has_color("Awesomely", Color(0, 0, 0))
            .assert_textline_has_color("Obvious!", Color(0, 0, 0))
            .assert_paragraph_is_at("Awesomely", 300.1, 500)
        )


def test_modify_paragraph_without_position():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        original_x = paragraph.position.x()
        original_y = paragraph.position.y()

        (
            paragraph.edit()
            .replace("Awesomely\nObvious!")
            .font("Helvetica", 12)
            .line_spacing(0.7)
            .apply()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Awesomely", "Helvetica", 12)
            .assert_textline_has_font("Obvious!", "Helvetica", 12)
            .assert_textline_has_color("Awesomely", Color(0, 0, 0))
            .assert_textline_has_color("Obvious!", Color(0, 0, 0))
            .assert_paragraph_is_at("Awesomely", original_x, original_y)
        )


def test_modify_paragraph_without_position_and_spacing():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        original_x = paragraph.position.x()
        original_y = paragraph.position.y()
        (paragraph.edit().replace("Awesomely\nObvious!").font("Helvetica", 12).apply())

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Awesomely", "Helvetica", 12)
            .assert_textline_has_font("Obvious!", "Helvetica", 12)
            .assert_textline_has_color("Awesomely", Color(0, 0, 0))
            .assert_textline_has_color("Obvious!", Color(0, 0, 0))
            .assert_paragraph_is_at("Awesomely", original_x, original_y)
        )


def test_modify_paragraph_noop():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        (paragraph.edit().apply())
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        assert paragraph.object_ref().status is not None
        # assert paragraph.object_ref().status.is_encodable()
        assert paragraph.object_ref().status.font_type == FontType.EMBEDDED
        assert not paragraph.object_ref().status.is_modified()

        (
            PDFAssertions(pdf)
            .assert_textline_has_font(
                "This is regular Sans text showing alignment and styles.",
                "AAAZPH+Roboto-Regular",
                12,
            )
            .assert_textline_has_color(
                "This is regular Sans text showing alignment and styles.",
                Color(0, 0, 0),
            )
        )


def test_modify_paragraph_only_text():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        result = paragraph.edit().replace("lorem\nipsum\nCaesar").apply()

        paragraph = pdf.page(1).select_paragraphs_starting_with("lorem")[0]
        assert paragraph.object_ref().status is not None
        # assert paragraph.object_ref().status.is_encodable()
        assert paragraph.object_ref().status.font_type == FontType.EMBEDDED
        assert paragraph.object_ref().status.is_modified()

        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles."
            )
            .assert_textline_has_color("lorem", Color(0, 0, 0))
            .assert_textline_has_color("ipsum", Color(0, 0, 0))
            .assert_textline_has_color("Caesar", Color(0, 0, 0))
        )


def test_modify_paragraph_only_font():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        (paragraph.edit().font("Helvetica", 28).apply())
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        assert paragraph.object_ref().status is not None
        # assert paragraph.object_ref().status.is_encodable()
        assert paragraph.object_ref().status.font_type == FontType.STANDARD
        assert paragraph.object_ref().status.is_modified()

        # TODO does not preserve color and fucks up line spacings
        (
            PDFAssertions(pdf)
            .assert_textline_has_font(
                "This is regular Sans text showing alignment and styles.",
                "Helvetica",
                28,
            )
            .assert_textline_has_color(
                "This is regular Sans text showing alignment and styles.",
                Color(0, 0, 0),
            )
        )


def test_modify_paragraph_only_move():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        (paragraph.edit().move_to(40, 40).apply())

        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        assert paragraph.object_ref().status is not None
        # assert paragraph.object_ref().status.is_encodable()
        assert paragraph.object_ref().status.font_type == FontType.EMBEDDED
        assert not paragraph.object_ref().status.is_modified()

        (
            PDFAssertions(pdf)
            .assert_textline_has_font(
                "This is regular Sans text showing alignment and styles.",
                "AAAZPH+Roboto-Regular",
                12,
            )
            .assert_paragraph_is_at(
                "This is regular Sans text showing alignment and styles.", 40, 40, 1
            )
            .assert_textline_has_color(
                "This is regular Sans text showing alignment and styles.",
                Color(0, 0, 0),
            )
        )


@pytest.mark.skip(reason="The exception is actually correct")
def test_modify_paragraph_simple():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        paragraph.edit().replace("Awesomely\nObvious!").apply()

        paragraph = pdf.page(1).select_paragraphs_starting_with("Awesomely")[0]
        assert paragraph.object_ref().status is not None
        # assert paragraph.object_ref().status.is_encodable()
        assert paragraph.object_ref().status.font_type == FontType.EMBEDDED
        assert paragraph.object_ref().status.is_modified()

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Awesomely", "AAAZPH+Roboto-Regular", 1)
            .assert_textline_has_font("Obvious!", "AAAZPH+Roboto-Regular", 1)
            .assert_textline_has_color("Awesomely", Color(0, 0, 0))
            .assert_textline_has_color("Obvious!", Color(0, 0, 0))
        )


def test_add_paragraph_with_custom_font1_expect_not_found():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        with pytest.raises(Exception, match="Font not found"):
            response = (
                pdf.new_paragraph()
                .text("Awesomely\nObvious!")
                .font("Roboto", 14)
                .line_spacing(0.7)
                .at(1, 300.1, 500)
                .add()
            )
            print(response)


def test_add_paragraph_with_custom_font1_1():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            pdf.new_paragraph()
            .text("Awesomely\nObvious!")
            .font("Roboto-Regular", 14)
            .line_spacing(0.7)
            .at(1, 300.1, 500)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_font_matching("Awesomely", "Roboto-Regular", 14)
            .assert_textline_has_font_matching("Obvious!", "Roboto-Regular", 14)
            .assert_textline_has_color("Awesomely", Color(0, 0, 0))
            .assert_textline_has_color("Obvious!", Color(0, 0, 0))
            .assert_paragraph_is_at("Awesomely", 300.1, 500, 1)
        )


def test_add_paragraph_on_page_with_custom_font1_1():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            pdf.page(1)
            .new_paragraph()
            .text("Awesomely\nObvious!")
            .font("Roboto-Regular", 14)
            .line_spacing(0.7)
            .at(300.1, 500)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_font_matching("Awesomely", "Roboto-Regular", 14)
            .assert_textline_has_font_matching("Obvious!", "Roboto-Regular", 14)
            .assert_textline_has_color("Awesomely", Color(0, 0, 0))
            .assert_textline_has_color("Obvious!", Color(0, 0, 0))
            .assert_paragraph_is_at("Awesomely", 300.1, 500, 1)
        )


def test_add_paragraph_with_custom_font1_2():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        fonts = pdf.find_fonts("Roboto", 14)
        assert len(fonts) > 0
        assert fonts[0].name.startswith("Roboto")

        roboto = fonts[0]
        (
            pdf.new_paragraph()
            .text("Awesomely\nObvious!")
            .font(roboto.name, roboto.size)
            .line_spacing(0.7)
            .at(1, 300.1, 500)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_font_matching("Awesomely", "Roboto", 14)
            .assert_textline_has_font_matching("Obvious!", "Roboto", 14)
            .assert_textline_has_color("Awesomely", Color(0, 0, 0))
            .assert_textline_has_color("Obvious!", Color(0, 0, 0))
            .assert_paragraph_is_at("Awesomely", 300.1, 500, 1)
        )


def test_add_paragraph_with_custom_font2():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        fonts = pdf.find_fonts("Asimovian", 14)
        assert len(fonts) > 0
        assert fonts[0].name == "Asimovian-Regular"

        asimov = fonts[0]
        (
            pdf.new_paragraph()
            .text("Awesomely\nObvious!")
            .font(asimov.name, asimov.size)
            .line_spacing(0.7)
            .at(1, 300.1, 500)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_font_matching("Awesomely", "Asimovian-Regular", 14)
            .assert_textline_has_font_matching("Obvious!", "Asimovian-Regular", 14)
            .assert_textline_has_color("Awesomely", Color(0, 0, 0))
            .assert_textline_has_color("Obvious!", Color(0, 0, 0))
            .assert_paragraph_is_at("Awesomely", 300.1, 500, 1)
        )


def test_add_paragraph_with_custom_font3():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    ttf_path = repo_root / "tests/fixtures" / "DancingScript-Regular.ttf"

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            pdf.new_paragraph()
            .text("Awesomely\nObvious!")
            .font_file(ttf_path, 24)
            .line_spacing(1.8)
            .color(Color(0, 0, 255))
            .at(1, 300.1, 500)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_font_matching("Awesomely", "DancingScript-Regular", 24)
            .assert_textline_has_font_matching("Obvious!", "DancingScript-Regular", 24)
            .assert_textline_has_color("Awesomely", Color(0, 0, 255))
            .assert_textline_has_color("Obvious!", Color(0, 0, 255))
            .assert_paragraph_is_at("Awesomely", 300.1, 500, 1)
        )


def test_add_paragraph_with_standard_font_times():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            pdf.new_paragraph()
            .text("Times Roman Test")
            .font(StandardFonts.TIMES_ROMAN.value, 14)
            .at(1, 150, 150)
            .add()
        )
        (
            PDFAssertions(pdf)
            .assert_text_has_font(
                "Times Roman Test", StandardFonts.TIMES_ROMAN.value, 14
            )
            .assert_paragraph_is_at("Times Roman Test", 150, 150, 1)
        )


def test_add_paragraph_with_standard_font_courier():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            pdf.new_paragraph()
            .text("Courier MonospacenCode Example")
            .font(StandardFonts.COURIER_BOLD.value, 12)
            .line_spacing(1.5)
            .at(1, 200, 200)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_text_has_font(
                "Courier Monospace", StandardFonts.COURIER_BOLD.value, 12, page=1
            )
            .assert_paragraph_is_at("Courier Monospace", 200, 200, page=1)
        )


def test_paragraph_color_reading():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            pdf.new_paragraph()
            .text("Red Color Test")
            .font(StandardFonts.HELVETICA.value, 14)
            .color(Color(255, 0, 0))
            .at(1, 100, 100)
            .add()
        )

        (
            pdf.new_paragraph()
            .text("Blue Color Test")
            .font(StandardFonts.HELVETICA.value, 14)
            .color(Color(0, 0, 255))
            .at(1, 100, 120)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_color("Blue Color Test", Color(0, 0, 255), page=1)
            .assert_textline_has_color("Red Color Test", Color(255, 0, 0), page=1)
        )


def test_add_paragraph_to_new_page():
    base_url, token, pdf_path = _require_env_and_fixture("Empty.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        (
            pdf.page(1)
            .new_paragraph()
            .text("Awesome")
            .font("Roboto-Regular", 14)
            .at(50, 100)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_font_matching("Awesome", "Roboto-Regular", 14)
            .assert_textline_has_color("Awesome", Color(0, 0, 0))
            .assert_paragraph_is_at("Awesome", 50, 100, 1)
        )
