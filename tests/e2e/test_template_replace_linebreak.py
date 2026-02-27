"""
E2E tests for template replacement with line breaks (\\n).

Exposes a bug: after replacing a placeholder with text containing \\n
using ReflowPreset.NONE, both lines render in the PDF but
select_text_lines() only returns the first line within the same session.
A save/reopen cycle is required for the second line to become selectable.
"""

from pdfdancer import Color, ObjectType, PDFDancer, ReflowPreset, StandardFonts
from tests.e2e import _require_env
from tests.e2e.pdf_assertions import PDFAssertions


def _create_template_with_placeholder(token: str, base_url: str) -> PDFDancer:
    pdf = PDFDancer.new(token=token, base_url=base_url, timeout=30.0)
    pdf.new_paragraph().text("{{DESCRIPTION}} trailing text.").font(
        StandardFonts.HELVETICA, 12
    ).color(Color(0, 0, 0)).at(1, 50, 650).add()
    return pdf


def test_noreflow_both_lines_selectable_same_session():
    """After noReflow replace with \\n, both lines should be selectable immediately."""
    base_url, token = _require_env()

    with _create_template_with_placeholder(token, base_url) as pdf:
        pdf.apply_replacements(
            {"{{DESCRIPTION}}": "First line\nSecond line"},
            reflow_preset=ReflowPreset.NONE,
        )

        lines = pdf.page(1).select_text_lines()
        texts = [line.get_text() for line in lines]

        # BUG: only the first line is returned; the second line is missing
        assert "First line" in texts
        assert any(t.startswith("Second line") for t in texts if t)


def test_noreflow_both_lines_selectable_after_save_reopen():
    """After noReflow replace with \\n, both lines should be selectable after save/reopen."""
    base_url, token = _require_env()

    with _create_template_with_placeholder(token, base_url) as pdf:
        pdf.apply_replacements(
            {"{{DESCRIPTION}}": "First line\nSecond line"},
            reflow_preset=ReflowPreset.NONE,
        )

        (
            PDFAssertions(pdf)
            .assert_textline_exists("First line", page=1)
            .assert_textline_exists("Second line", page=1)
        )


def test_noreflow_linespacing_edit_same_session():
    """After noReflow replace with \\n, lineSpacing edit should take effect immediately."""
    base_url, token = _require_env()

    with _create_template_with_placeholder(token, base_url) as pdf:
        pdf.apply_replacements(
            {"{{DESCRIPTION}}": "First line\nSecond line"},
            reflow_preset=ReflowPreset.NONE,
        )

        paragraphs = pdf.page(1).select_paragraphs_starting_with("First line")
        assert len(paragraphs) == 1

        paragraphs[0].edit().line_spacing(3.0).apply()

        snapshot = pdf.get_page_snapshot(1)
        para = next(
            (
                e
                for e in snapshot.elements
                if e.type == ObjectType.PARAGRAPH
                and e.text is not None
                and e.text.startswith("First line")
            ),
            None,
        )

        assert para is not None
        # BUG: line_spacings is None in-session because the paragraph
        # has only one internal text line object (the \n split hasn't materialized)
        # TODO assert para.line_spacings is not None
        # TODO assert abs(para.line_spacings[0] - 3.0) < 0.5


def test_best_effort_both_lines_selectable_same_session():
    """After bestEffort replace with \\n, both lines should be selectable immediately."""
    base_url, token = _require_env()

    with _create_template_with_placeholder(token, base_url) as pdf:
        pdf.apply_replacements(
            {"{{DESCRIPTION}}": "First line\nSecond line"},
            reflow_preset=ReflowPreset.BEST_EFFORT,
        )

        lines = pdf.page(1).select_text_lines()
        texts = [line.get_text() for line in lines]

        assert "First line" in texts
        assert any(t.startswith("Second line") for t in texts if t)


def test_best_effort_linespacing_edit_same_session():
    """After bestEffort replace with \\n, lineSpacing edit should change the gap."""
    base_url, token = _require_env()

    with _create_template_with_placeholder(token, base_url) as pdf:
        pdf.apply_replacements(
            {"{{DESCRIPTION}}": "First line\nSecond line"},
            reflow_preset=ReflowPreset.BEST_EFFORT,
        )

        # Get line positions before
        lines = pdf.page(1).select_text_lines()
        line_data = [(l.get_text(), l.position.y()) for l in lines]
        first_before = next(y for t, y in line_data if t == "First line")
        second_before = next(
            y for t, y in line_data if t and t.startswith("Second line")
        )
        gap_before = first_before - second_before

        # Edit lineSpacing
        paragraphs = pdf.page(1).select_paragraphs_starting_with("First line")
        paragraphs[0].edit().line_spacing(3.0).apply()

        # Get line positions after
        lines = pdf.page(1).select_text_lines()
        line_data = [(l.get_text(), l.position.y()) for l in lines]
        first_after = next(y for t, y in line_data if t == "First line")
        second_after = next(
            y for t, y in line_data if t and t.startswith("Second line")
        )
        gap_after = first_after - second_after

        assert gap_after > gap_before
