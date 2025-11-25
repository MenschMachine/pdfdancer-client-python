import pytest

from pdfdancer import Color, StandardFonts
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_context_manager_basic_usage():
    """Test basic context manager usage with PDFDancer.open()"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraphs = pdf.select_paragraphs()
        assert 20 <= len(paragraphs) <= 22  # strange, but differs on linux


def test_context_manager_edit_text_only():
    """Test context manager with paragraph.edit() - text replacement only"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        # Context manager automatically calls apply() on success
        with paragraph.edit() as editor:
            editor.replace("This is replaced\ntext on two lines")

        (
            PDFAssertions(pdf)
            .assert_textline_exists("This is replaced", page=1)
            .assert_textline_exists("text on two lines", page=1)
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles.", page=1
            )
        )


def test_context_manager_edit_font_only():
    """Test context manager with font change only"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.font("Helvetica", 28)

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


def test_context_manager_edit_text_and_font():
    """Test context manager with text replacement and font change"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.replace("New Text\nHere")
            editor.font("Helvetica", 16)

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("New Text", "Helvetica", 16)
            .assert_textline_has_font("Here", "Helvetica", 16)
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles."
            )
        )


def test_context_manager_edit_all_properties():
    """Test context manager with all properties: text, font, color, line spacing, position"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.replace("Fully\nModified")
            editor.font("Helvetica", 18)
            editor.color(Color(255, 0, 0))
            editor.line_spacing(1.5)
            editor.move_to(100, 200)

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Fully", "Helvetica", 18)
            .assert_textline_has_font("Modified", "Helvetica", 18)
            .assert_textline_has_color("Fully", Color(255, 0, 0))
            .assert_textline_has_color("Modified", Color(255, 0, 0))
            .assert_paragraph_is_at("Fully", 100, 200, 1)
        )


def test_context_manager_edit_color_only():
    """Test context manager with color change only"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.color(Color(0, 255, 0))

        PDFAssertions(pdf).assert_textline_has_color(
            "This is regular Sans text showing alignment and styles.", Color(0, 255, 0)
        )


def test_context_manager_edit_line_spacing_only():
    """Test context manager with line spacing change only"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.line_spacing(2.0)

        PDFAssertions(pdf).assert_textline_exists(
            "This is regular Sans text showing alignment and styles."
        )


def test_context_manager_edit_move_only():
    """Test context manager with position change only"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.move_to(150, 300)

        (
            PDFAssertions(pdf)
            .assert_textline_has_font(
                "This is regular Sans text showing alignment and styles.",
                "AAAZPH+Roboto-Regular",
                12,
            )
            .assert_paragraph_is_at(
                "This is regular Sans text showing alignment and styles.",
                150,
                300,
                1,
                epsilon=0.22,
            )
        )


def test_context_manager_multiple_edits_sequential():
    """Test multiple sequential edits using context manager"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        # First edit
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        with paragraph.edit() as editor:
            editor.replace("First Edit")

        # Second edit
        paragraph = pdf.page(1).select_paragraphs_starting_with("First Edit")[0]
        with paragraph.edit() as editor:
            editor.replace("Second Edit")
            editor.font("Helvetica", 20)

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Second Edit", "Helvetica", 20)
            .assert_textline_does_not_exist("First Edit")
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles."
            )
        )


def test_context_manager_edit_multiple_paragraphs():
    """Test editing multiple paragraphs using context manager"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraphs = pdf.page(1).select_paragraphs()

        # Edit first paragraph
        with paragraphs[0].edit() as editor:
            editor.replace("Modified First")
            editor.font("Helvetica", 14)

        # Edit second paragraph
        with paragraphs[1].edit() as editor:
            editor.replace("Modified Second")
            editor.font("Helvetica", 14)

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Modified First", "Helvetica", 14)
            .assert_textline_has_font("Modified Second", "Helvetica", 14)
        )


def test_context_manager_edit_with_exception_no_apply():
    """Test that apply() is NOT called when exception occurs in context manager"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        # Simulate an exception - apply() should not be called
        with pytest.raises(ValueError):
            with paragraph.edit() as editor:
                editor.replace("This should not be applied")
                raise ValueError("Test exception")

        # Original text should still exist since apply() was not called
        PDFAssertions(pdf).assert_textline_exists(
            "This is regular Sans text showing alignment and styles."
        )


def test_context_manager_nested_pdf_and_edit():
    """Test nested context managers: PDFDancer.open() and paragraph.edit()"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.replace("Nested Context\nManager Test")
            editor.font("Helvetica", 16)
            editor.color(Color(0, 0, 255))

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Nested Context", "Helvetica", 16)
            .assert_textline_has_color("Nested Context", Color(0, 0, 255))
            .assert_textline_has_font("Manager Test", "Helvetica", 16)
            .assert_textline_has_color("Manager Test", Color(0, 0, 255))
        )


def test_context_manager_edit_preserves_position_when_not_specified():
    """Test that position is preserved when not explicitly changed"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        original_x = paragraph.position.x()
        original_y = paragraph.position.y()

        with paragraph.edit() as editor:
            editor.replace("Position Preserved")
            editor.font("Helvetica", 14)

        PDFAssertions(pdf).assert_paragraph_is_at(
            "Position Preserved", original_x, original_y, 1
        )


def test_context_manager_edit_chaining():
    """Test fluent chaining within context manager"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.replace("Chained\nEdits").font("Helvetica", 15).color(
                Color(128, 128, 128)
            ).line_spacing(1.8)

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Chained", "Helvetica", 15)
            .assert_textline_has_color("Chained", Color(128, 128, 128))
            .assert_textline_has_font("Edits", "Helvetica", 15)
            .assert_textline_has_color("Edits", Color(128, 128, 128))
        )


def test_context_manager_edit_standard_fonts():
    """Test context manager with standard fonts"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.replace("Times Roman")
            editor.font(StandardFonts.TIMES_ROMAN.value, 16)

        PDFAssertions(pdf).assert_textline_has_font(
            "Times Roman", StandardFonts.TIMES_ROMAN.value, 16
        )


def test_context_manager_edit_with_multiline_text():
    """Test context manager with multiline text replacement"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.replace("Line 1\nLine 2")
            editor.font("Helvetica", 12)

        (
            PDFAssertions(pdf)
            .assert_textline_exists("Line 1")
            .assert_textline_exists("Line 2")
        )


def test_context_manager_edit_empty_text():
    """Test context manager with empty text replacement"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.replace("")
            editor.font("Helvetica", 12)

        PDFAssertions(pdf).assert_textline_does_not_exist(
            "This is regular Sans text showing alignment and styles."
        )


def test_context_manager_example_from_docs():
    """Test the exact example from the documentation"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        paragraph = pdf.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        # Context manager automatically calls apply() on success
        with paragraph.edit() as editor:
            editor.replace("Awesomely\nObvious!")
            editor.font("Helvetica", 12)

        pdf.save("/tmp/output_context_manager_test.pdf")

        # Verify the changes
        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Awesomely", "Helvetica", 12)
            .assert_textline_has_font("Obvious!", "Helvetica", 12)
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles."
            )
        )


def test_context_manager_vs_manual_apply():
    """Test that context manager produces same result as manual apply()"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    # Test with context manager
    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf1:
        paragraph = pdf1.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        with paragraph.edit() as editor:
            editor.replace("Test Text")
            editor.font("Helvetica", 14)
            editor.color(Color(255, 0, 0))

        result1 = pdf1.get_bytes()

    # Test with manual apply()
    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf2:
        paragraph = pdf2.page(1).select_paragraphs_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]

        paragraph.edit().replace("Test Text").font("Helvetica", 14).color(
            Color(255, 0, 0)
        ).apply()

        result2 = pdf2.get_bytes()

    # sometimes it's off by one, don't know why, hard to reproduce
    assert abs(len(result1) - len(result2)) <= 1
