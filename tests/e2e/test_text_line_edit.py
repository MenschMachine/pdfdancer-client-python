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
        text_lines = pdf.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

        text_line = text_lines[0]

        # Context manager automatically calls apply() on success
        with text_line.edit() as editor:
            editor.replace("This text has been replaced")

        (
            PDFAssertions(pdf)
            .assert_textline_exists("This text has been replaced", page=0)
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles.", page=0
            )
        )


def test_text_line_edit_font_only():
    """Test text line edit with font change only"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

        text_line = text_lines[0]

        with text_line.edit() as editor:
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


def test_text_line_edit_color_only():
    """Test text line edit with color change only"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

        text_line = text_lines[0]

        with text_line.edit() as editor:
            editor.color(Color(0, 255, 0))

        PDFAssertions(pdf).assert_textline_has_color(
            "This is regular Sans text showing alignment and styles.", Color(0, 255, 0)
        )


def test_text_line_edit_move_only():
    """Test text line edit with position change only"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

        text_line = text_lines[0]

        with text_line.edit() as editor:
            editor.move_to(150, 300)

        # Verify the text line was moved by searching at the new position
        text_lines_after = pdf.page(0).select_text_lines_at(150, 300, tolerance=5.0)

        # Check if we found a text line at the new position with the same text
        found = any(
            "This is regular Sans text showing alignment and styles." in tl.text
            for tl in text_lines_after
            if tl.text
        )
        assert found, "Text line was not found at the new position"


def test_text_line_edit_text_and_font():
    """Test text line edit with text replacement and font change"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

        text_line = text_lines[0]

        with text_line.edit() as editor:
            editor.replace("New Text Here")
            editor.font("Helvetica", 16)

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("New Text Here", "Helvetica", 16)
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles."
            )
        )


def test_text_line_edit_all_properties():
    """Test text line edit with all properties: text, font, color, position"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

        text_line = text_lines[0]

        with text_line.edit() as editor:
            editor.replace("Fully Modified")
            editor.font("Helvetica", 18)
            editor.color(Color(255, 0, 0))
            editor.move_to(100, 200)

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Fully Modified", "Helvetica", 18)
            .assert_textline_has_color("Fully Modified", Color(255, 0, 0))
        )


def test_text_line_edit_line_spacing_ignored():
    """Test that line spacing is ignored for text lines with a warning"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

        text_line = text_lines[0]

        # Line spacing should be ignored with a warning
        with text_line.edit() as editor:
            editor.line_spacing(2.0)  # This should be ignored
            editor.replace("Text with ignored spacing")

        # Verify the text was changed
        PDFAssertions(pdf).assert_textline_exists("Text with ignored spacing")


def test_text_line_edit_chaining():
    """Test fluent chaining within context manager"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

        text_line = text_lines[0]

        with text_line.edit() as editor:
            editor.replace("Chained Edits").font("Helvetica", 15).color(
                Color(128, 128, 128)
            )

        (
            PDFAssertions(pdf)
            .assert_textline_has_font("Chained Edits", "Helvetica", 15)
            .assert_textline_has_color("Chained Edits", Color(128, 128, 128))
        )


def test_text_line_edit_with_exception_no_apply():
    """Test that apply() is NOT called when exception occurs in context manager"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        text_lines = pdf.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

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
    """Test multiple sequential edits using context manager"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        # First edit
        text_lines = pdf.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

        text_line = text_lines[0]
        with text_line.edit() as editor:
            editor.replace("First Edit")

        # Second edit
        text_lines = pdf.page(0).select_text_lines_starting_with("First Edit")
        text_line = text_lines[0]
        with text_line.edit() as editor:
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


def test_text_line_edit_vs_manual_apply():
    """Test that context manager produces same result as manual apply()"""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    # Test with context manager
    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf1:
        text_lines = pdf1.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

        text_line = text_lines[0]

        with text_line.edit() as editor:
            editor.replace("Test Text")
            editor.font("Helvetica", 14)
            editor.color(Color(255, 0, 0))

        result1 = pdf1.get_bytes()

    # Test with manual apply()
    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf2:
        text_lines = pdf2.page(0).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        if not text_lines:
            pytest.skip("Required text line not found in test PDF")

        text_line = text_lines[0]

        text_line.edit().replace("Test Text").font("Helvetica", 14).color(
            Color(255, 0, 0)
        ).apply()

        result2 = pdf2.get_bytes()

    # Results should be similar in size
    assert abs(len(result1) - len(result2)) <= 1
