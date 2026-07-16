"""Deep persistence tests for the selector-based v2 text-editing API."""

from pathlib import Path

import pytest
from dotenv import load_dotenv

from pdfdancer import (
    PdfAffineTransform,
    PdfColorRequest,
    PDFDancer,
    TextDeleteRequest,
    TextInsertRequest,
    TextLayoutProfile,
    TextReplaceRequest,
    TextStyleRequest,
)
from tests.e2e import _get_base_url, _server_up
from tests.e2e.pdf_assertions import PDFAssertions

IOWA_1040 = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "examples"
    / "corpus-pdfs-failed"
    / "pdfs_all"
    / "ia_scr_1040.pdf"
)
SHOWCASE = Path(__file__).resolve().parents[1] / "fixtures" / "Showcase.pdf"
ROBOTO = Path(__file__).resolve().parents[1] / "fixtures" / "Roboto-Regular.ttf"
LOGO = Path(__file__).resolve().parents[1] / "fixtures" / "logo-80.png"


def _open_local_fixture(path: Path) -> PDFDancer:
    load_dotenv()
    base_url = _get_base_url()
    up, message = _server_up(base_url)
    if not up:
        pytest.fail(f"PDFDancer server not reachable at {base_url}: {message}")
    if not path.exists():
        pytest.fail(f"PDF fixture not found at {path}")
    token = PDFDancer._obtain_anonymous_token(base_url)
    return PDFDancer.open(path, token=token, base_url=base_url)


@pytest.fixture
def iowa_pdf() -> PDFDancer:
    """Open the shared Java/Python real-world fixture with a fresh local token."""
    # A fresh anonymous token prevents a stale developer .env token from making
    # the persistence tests nondeterministic.
    pdf = _open_local_fixture(IOWA_1040)
    try:
        yield pdf
    finally:
        pdf.close()


@pytest.fixture
def showcase_pdf() -> PDFDancer:
    pdf = _open_local_fixture(SHOWCASE)
    try:
        yield pdf
    finally:
        pdf.close()


def test_custom_font_replace_persists_in_saved_pdf(showcase_pdf: PDFDancer):
    font_name = showcase_pdf.register_font(ROBOTO)
    response = (
        showcase_pdf.page(1)
        .text()
        .replace(
            TextReplaceRequest.literal(
                "This line will be replaced.", "Replacement succeeded."
            )
            .font(font_name)
            .build()
        )
    )

    assert font_name == "Roboto-Regular"
    assert response.matched == 1
    assert response.changed == 1
    assert response.pages_changed == (1,)
    assert not response.warnings
    assert not response.errors
    (
        PDFAssertions(showcase_pdf)
        .assert_pdf_text_occurrence_count("This line will be replaced.", 0, page=1)
        .assert_pdf_text_occurrence_count("Replacement succeeded.", 1, page=1)
        .assert_pdf_text_contains("PDFDancer Showcase", page=1)
    )


def test_image_replace_persists_generated_image(showcase_pdf: PDFDancer):
    response = (
        showcase_pdf.page(1)
        .text()
        .replace(
            TextReplaceRequest.builder()
            .literal("This line will be replaced.")
            .max_matches(1)
            .replace_with_image(
                LOGO,
                PdfAffineTransform.builder().scale(20, 10).translate(3, -2).build(),
            )
            .build()
        )
    )

    assert response.matched == 1
    assert response.changed == 1
    assert len(response.change) == 1
    change = response.change[0]
    assert change.operation == "replaceWithImage"
    assert change.source_text == "This line will be replaced."
    assert change.result_text == ""
    assert len(change.generated_element_ids) == 1
    image_id = change.generated_element_ids[0]

    persisted = PDFAssertions(showcase_pdf)
    persisted.assert_pdf_text_occurrence_count("This line will be replaced.", 0, page=1)
    assert image_id in {
        image.internal_id for image in persisted.get_pdf().page(1).select_images()
    }


def test_page_scoped_replace_reports_unencodable_font_and_preserves_pdf(
    iowa_pdf: PDFDancer,
):
    response = (
        iowa_pdf.page(1)
        .text()
        .replace(
            # Use only glyphs already encoded by the source font. The live server
            # reports a per-match font-roundtrip error for this replacement.
            TextReplaceRequest.literal("Iowa", "Iwoa").build()
        )
    )

    assert response.matched == 3
    assert response.changed == 0
    assert response.pages_changed == ()
    assert len(response.errors) == 3
    assert all(error.page == 1 for error in response.errors)
    assert all(
        error.message
        and error.message.startswith(
            "No decoded replacement font can roundtrip text: Iwoa"
        )
        for error in response.errors
    )
    (
        PDFAssertions(iowa_pdf)
        .assert_pdf_text_occurrence_count("Iowa", 3, page=1)
        .assert_pdf_text_occurrence_count("Iwoa", 0, page=1)
        .assert_pdf_text_occurrence_count("Iowa", 11, page=2)
        .assert_pdf_text_occurrence_count("Iwoa", 0, page=2)
        .assert_pdf_text_contains("2012 IA 1040, page 2", page=2)
    )


def test_page_scoped_insert_persists_only_on_selected_page(iowa_pdf: PDFDancer):
    response = (
        iowa_pdf.page(1)
        .text()
        .insert(TextInsertRequest.after("Iowa", "_STATE").build())
    )

    assert response.matched == 3
    assert response.changed == 3
    assert response.pages_changed == (1,)
    assert not response.errors
    assert len(response.change) == 3
    (
        PDFAssertions(iowa_pdf)
        .assert_pdf_text_occurrence_count("_STATE", 3, page=1)
        .assert_pdf_text_occurrence_count("_STATE", 0, page=2)
        .assert_pdf_text_occurrence_count("Iowa", 11, page=2)
        .assert_pdf_text_contains("2012 IA 1040, page 2", page=2)
    )


def test_page_scoped_delete_persists_only_on_selected_page(iowa_pdf: PDFDancer):
    response = iowa_pdf.page(1).text().delete(TextDeleteRequest.literal("Iowa").build())

    assert response.matched == 3
    assert response.changed == 3
    assert response.pages_changed == (1,)
    assert not response.errors
    (
        PDFAssertions(iowa_pdf)
        .assert_pdf_text_occurrence_count("Iowa", 0, page=1)
        .assert_pdf_text_occurrence_count("Iowa", 11, page=2)
        .assert_pdf_text_contains("2012 IA 1040, page 2", page=2)
    )


def test_case_insensitive_delete_honors_max_matches(iowa_pdf: PDFDancer):
    response = (
        iowa_pdf.page(1)
        .text()
        .delete(
            TextDeleteRequest.literal("iowa")
            .case_sensitive(False)
            .max_matches(2)
            .build()
        )
    )

    assert response.matched == 2
    assert response.changed == 2
    assert response.pages_changed == (1,)
    assert not response.errors
    (
        PDFAssertions(iowa_pdf)
        .assert_pdf_text_occurrence_count("Iowa", 1, page=1)
        .assert_pdf_text_occurrence_count("Iowa", 11, page=2)
    )


def test_no_match_returns_zero_and_preserves_saved_pdf(iowa_pdf: PDFDancer):
    response = iowa_pdf.text().replace(
        TextReplaceRequest.literal(
            "DOES_NOT_EXIST_IN_TAX_FORM", "SHOULD_NOT_APPEAR"
        ).build()
    )

    assert response.matched == 0
    assert response.changed == 0
    assert response.pages_changed == ()
    assert not response.errors
    (
        PDFAssertions(iowa_pdf)
        .assert_pdf_text_occurrence_count("SHOULD_NOT_APPEAR", 0)
        .assert_pdf_text_occurrence_count("Iowa", 3, page=1)
        .assert_pdf_text_occurrence_count("Iowa", 11, page=2)
    )


def test_page_scoped_style_preserves_text_and_reports_selected_page(
    iowa_pdf: PDFDancer,
):
    response = (
        iowa_pdf.page(1)
        .text()
        .style(
            TextStyleRequest.literal("Iowa")
            .fill_color(PdfColorRequest.rgb(1, 0, 0))
            .build()
        )
    )

    assert response.matched == 3
    assert response.changed == 3
    assert response.pages_changed == (1,)
    assert not response.errors
    (
        PDFAssertions(iowa_pdf)
        .assert_pdf_text_occurrence_count("Iowa", 3, page=1)
        .assert_pdf_text_occurrence_count("Iowa", 11, page=2)
        .assert_pdf_text_contains("2012 IA 1040, page 2", page=2)
    )


def test_document_wide_literal_delete_persists_all_matches(iowa_pdf: PDFDancer):
    response = iowa_pdf.text().delete(TextDeleteRequest.literal("Iowa").build())

    assert response.matched == 14
    assert response.changed == 14
    assert response.pages_changed == (1, 2)
    assert not response.errors
    PDFAssertions(iowa_pdf).assert_pdf_text_occurrence_count("Iowa", 0)


def test_regex_delete_with_reflow_persists(showcase_pdf: PDFDancer):
    response = showcase_pdf.text().delete(
        TextDeleteRequest.regex(r"This line will be replaced\.")
        .reflow_when_supported(TextLayoutProfile.DEFAULT)
        .build()
    )

    assert response.matched == 1
    assert response.changed == 1
    assert not response.errors
    PDFAssertions(showcase_pdf).assert_pdf_text_occurrence_count(
        "This line will be replaced.", 0, page=1
    )


def test_whole_word_insert_honors_match_boundaries_and_limit(iowa_pdf: PDFDancer):
    response = iowa_pdf.text().insert(
        TextInsertRequest.after("Iowa", "_STATE")
        .whole_words(True)
        .max_matches(2)
        .build()
    )

    assert response.matched == 2
    assert response.changed == 2
    assert not response.errors
    (
        PDFAssertions(iowa_pdf)
        .assert_pdf_text_occurrence_count("_STATE", 2)
        .assert_pdf_text_occurrence_count("Iowa", 14)
    )


def test_coordinate_insert_with_rotation_and_style_persists(iowa_pdf: PDFDancer):
    response = iowa_pdf.text().insert(
        TextInsertRequest.at(1, 72, 720, "Coordinate Insert")
        .rotation_degrees(90)
        .font("Helvetica-Bold")
        .size(12)
        .fill_color(PdfColorRequest.rgb(0.8, 0.1, 0.1))
        .build()
    )

    assert response.changed == 1
    assert not response.errors
    PDFAssertions(iowa_pdf).assert_pdf_text_occurrence_count(
        "Coordinate Insert", 1, page=1
    )


def test_regex_style_preserves_text_and_reports_all_matches(showcase_pdf: PDFDancer):
    response = showcase_pdf.text().style(
        TextStyleRequest.regex(r"This line will be replaced\.")
        .fill_color(PdfColorRequest.rgb(1, 0, 0))
        .build()
    )

    assert response.matched == 1
    assert response.changed == 1
    assert response.pages_changed == (1,)
    assert not response.errors
    PDFAssertions(showcase_pdf).assert_pdf_text_occurrence_count(
        "This line will be replaced.", 1, page=1
    )


def test_runs_where_style_selects_the_intended_run(showcase_pdf: PDFDancer):
    response = showcase_pdf.text().style(
        TextStyleRequest.runs_where()
        .where_text_contains("This line will be replaced.")
        .fill_color(PdfColorRequest.rgb(1, 0, 0))
        .build()
    )

    assert response.matched == 1
    assert response.changed == 1
    assert not response.errors
    PDFAssertions(showcase_pdf).assert_pdf_text_occurrence_count(
        "This line will be replaced.", 1, page=1
    )


def test_required_reflow_exposes_layout_diagnostics(showcase_pdf: PDFDancer):
    response = showcase_pdf.text().replace(
        TextReplaceRequest.literal(
            "This line will be replaced.", "Replacement with reflow."
        )
        .require_reflow(TextLayoutProfile.BODY_TEXT)
        .hyphenation_enabled(False)
        .build()
    )

    assert response.matched == 1
    assert response.changed == 1
    assert len(response.change) == 1
    change = response.change[0]
    assert change.requested_layout_mode == "requireReflow"
    assert change.requested_layout_profile == "bodyText"
    assert change.effective_hyphenation_enabled is False
    assert change.applied_layout_mode == "REFLOWED"
    (
        PDFAssertions(showcase_pdf)
        .assert_pdf_text_occurrence_count("This line will be replaced.", 0, page=1)
        .assert_pdf_text_occurrence_count("Replacement with reflow.", 1, page=1)
    )
