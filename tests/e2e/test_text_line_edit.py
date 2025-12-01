import pytest

from pdfdancer import Color
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_text_line_edit_text_only():
    """Test text line edit with text replacement only"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        # Select a text line
        text_lines = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )

        assert len(text_lines) >= 1

        text_line = text_lines[0]

        # Context manager automatically calls apply() on success
        with text_line.edit() as editor:
            editor.replace("This text has been replaced")

        (
            PDFAssertions(pdf)
            .assert_textline_exists("This text has been replaced", page=1)
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles.", page=1
            )
        )


def test_text_line_edit_font_only():
    """Test text line font-only changes"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(text_lines) >= 1

        text_line = text_lines[0]
        original_text = text_line.text

        # Font changes on text lines should work
        with text_line.edit() as editor:
            editor.font("Helvetica", 28)

        # Verify the text still exists (font changed but text preserved)
        PDFAssertions(pdf).assert_textline_exists(original_text)


def test_text_line_edit_color_only():
    """Test text line color-only changes"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(text_lines) >= 1

        text_line = text_lines[0]
        original_text = text_line.text

        # Color changes on text lines should work
        with text_line.edit() as editor:
            editor.color(Color(0, 255, 0))

        # Verify the text still exists (color changed but text preserved)
        PDFAssertions(pdf).assert_textline_exists(original_text)


def test_text_line_edit_move_only():
    """Test text line edit with position change only"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(text_lines) >= 1

        text_line = text_lines[0]

        with text_line.edit() as editor:
            editor.move_to(150, 300)

        # Verify the text line was moved by searching at the new position
        text_lines_after = pdf.page(1).select_text_lines_at(150, 300, tolerance=5.0)

        # Check if we found a text line at the new position with the same text
        found = any(
            "This is regular Sans text showing alignment and styles." in tl.text
            for tl in text_lines_after
            if tl.text
        )
        assert found, "Text line was not found at the new position"


def test_text_line_edit_text_and_font():
    """Test text+font changes work together"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(text_lines) >= 1

        text_line = text_lines[0]

        # Text + Font changes should work
        with text_line.edit() as editor:
            editor.replace("New Text Here")
            editor.font("Helvetica", 16)

        # Verify the new text exists
        (
            PDFAssertions(pdf)
            .assert_textline_exists("New Text Here")
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles."
            )
        )


def test_text_line_edit_all_properties():
    """Test that combined property changes work (except line spacing)"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(text_lines) >= 1

        text_line = text_lines[0]

        # Combined changes including font/color/position should work
        with text_line.edit() as editor:
            editor.replace("Fully Modified")
            editor.font("Helvetica", 18)
            editor.color(Color(255, 0, 0))
            editor.move_to(100, 200)

        # Verify the modified text exists
        PDFAssertions(pdf).assert_textline_exists("Fully Modified")


def test_text_line_edit_chaining():
    """Test that chained font/color changes work"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(text_lines) >= 1

        text_line = text_lines[0]

        # Chained font/color changes should work
        with text_line.edit() as editor:
            editor.replace("Chained Edits").font("Helvetica", 15).color(
                Color(128, 128, 128)
            )

        # Verify the new text exists
        (
            PDFAssertions(pdf)
            .assert_textline_exists("Chained Edits")
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles."
            )
        )


def test_text_line_edit_with_exception_no_apply():
    """Test that apply() is NOT called when exception occurs in context manager"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(text_lines) >= 1

        text_line = text_lines[0]

        # Simulate an exception - apply() should not be called
        with pytest.raises(ValueError):
            with text_line.edit() as editor:
                editor.replace("This should not be applied")
                raise ValueError("Test exception")

        # Original text should still exist since apply() was not called
        PDFAssertions(pdf).assert_textline_exists(
            "This is regular Sans text showing alignment and styles."
        )


def test_text_line_edit_multiple_sequential():
    """Test multiple sequential text-only edits using context manager"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        # First edit
        text_lines = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(text_lines) >= 1

        text_line = text_lines[0]
        with text_line.edit() as editor:
            editor.replace("First Edit")

        # Second edit - text only (no font change since it's not supported)
        text_lines = pdf.page(1).select_text_lines_starting_with("First Edit")
        text_line = text_lines[0]
        with text_line.edit() as editor:
            editor.replace("Second Edit")

        (
            PDFAssertions(pdf)
            .assert_textline_exists("Second Edit")
            .assert_textline_does_not_exist("First Edit")
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles."
            )
        )


def test_text_line_edit_vs_manual_apply():
    """Test that context manager produces same result as manual apply() for text-only changes"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    # Test with context manager
    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf1:
        text_lines = pdf1.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(text_lines) >= 1

        text_line = text_lines[0]

        with text_line.edit() as editor:
            editor.replace("Test Text")

        result1 = pdf1.get_bytes()

    # Test with manual apply()
    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf2:
        text_lines = pdf2.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(text_lines) >= 1

        text_line = text_lines[0]

        text_line.edit().replace("Test Text").apply()

        result2 = pdf2.get_bytes()

    # Results should be similar in size
    assert abs(len(result1) - len(result2)) <= 10
