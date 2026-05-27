"""E2E tests for template replacement with reflow presets."""

import pytest

from pdfdancer import ReflowPreset
from pdfdancer.exceptions import PdfDancerException
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def _load_three_column_fixture():
    """Load the three-column-paragraphs.pdf fixture."""
    base_url, token, pdf_path = _require_env_and_fixture("examples/text/three-column-paragraphs.pdf")
    return PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0)


def _load_reflow_fixture():
    """Load a generated text fixture suitable for successful reflow."""
    base_url, token, pdf_path = _require_env_and_fixture("examples/text-fragments/multi-line-paragraph.pdf")
    return PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0)


def _get_reflow_placeholder(pdf: PDFDancer) -> str:
    paragraph = pdf.page(1).select_paragraph_starting_with("This is the first line of text.")
    assert paragraph is not None
    return paragraph.get_text()


def test_no_reflow_keeps_line():
    """Test that NONE reflow preset keeps the line as-is."""
    with _load_three_column_fixture() as pdf:
        success = pdf.apply_replacements(
            {"Left aligned text starts each measure with a": "YABBA!"},
            reflow_preset=ReflowPreset.NONE,
        )
        assert success is True

        PDFAssertions(pdf).assert_textline_exists("YABBA", 1)

        text_line = pdf.page(1).select_text_line_starting_with("YABBA!")
        assert text_line is not None
        assert text_line.get_text() == "YABBA!"


def test_reflow_best_effort_reflows():
    """Test that BEST_EFFORT reflow preset reflows text."""
    with _load_reflow_fixture() as pdf:
        placeholder = _get_reflow_placeholder(pdf)

        success = pdf.apply_replacements(
            {placeholder: "BEST_EFFORT_REFLOW_TEXT"},
            reflow_preset=ReflowPreset.BEST_EFFORT,
        )
        assert success is True

        (
            PDFAssertions(pdf)
            .assert_paragraph_does_not_exist("This is the first line of text.", 1)
            .assert_paragraph_exists("BEST_EFFORT_REFLOW_TEXT", 1)
        )


def test_reflow_fit_or_fail_fails_when_too_long():
    """Test that FIT_OR_FAIL raises exception when replacement is too long."""
    with _load_three_column_fixture() as pdf:
        with pytest.raises(PdfDancerException):
            pdf.apply_replacements(
                {"Left aligned text starts each measure with a": "YABBAYABBAYABBAYABBAYABBAYABBAYABBAYABBAYABBAYABBA!"},
                reflow_preset=ReflowPreset.FIT_OR_FAIL,
            )


def test_reflow_fit_or_fit_fits():
    """Test that FIT_OR_FAIL succeeds when replacement fits."""
    with _load_reflow_fixture() as pdf:
        placeholder = _get_reflow_placeholder(pdf)

        success = pdf.apply_replacements(
            {placeholder: "FIT"},
            reflow_preset=ReflowPreset.FIT_OR_FAIL,
        )
        assert success is True

        (
            PDFAssertions(pdf)
            .assert_paragraph_does_not_exist("This is the first line of text.", 1)
            .assert_paragraph_exists("FIT", 1)
        )
