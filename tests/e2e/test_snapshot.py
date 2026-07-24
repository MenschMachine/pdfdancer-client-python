"""
Comprehensive end-to-end tests for PDF snapshot endpoints.
Validates that snapshot data matches select_* method results before, during, and after mutations.
"""

import pytest

from pdfdancer import ObjectType, PDFDancer
from tests.e2e import _require_env_and_fixture


def test_page_snapshot_matches_select_images():
    """Test that page snapshot image data matches select_images() results."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        page = pdf.page(1)

        snapshot = pdf.get_page_snapshot(1)
        snapshot_images = [e for e in snapshot.elements if e.type == ObjectType.IMAGE]

        selected_images = page.select_images()

        assert len(selected_images) == len(
            snapshot_images
        ), "Snapshot should return same image count as select_images()"

        if selected_images:
            snapshot_ids = {e.internal_id for e in snapshot_images}
            selected_ids = {img.internal_id for img in selected_images}

            assert (
                selected_ids == snapshot_ids
            ), "Snapshot and select_images() should return identical image IDs"


def test_page_snapshot_matches_select_forms():
    """Test that page snapshot form data matches select_forms() results."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        page = pdf.page(1)

        snapshot = pdf.get_page_snapshot(1)
        snapshot_forms = [
            e for e in snapshot.elements if e.type == ObjectType.FORM_X_OBJECT
        ]

        selected_forms = page.select_forms()

        assert len(selected_forms) == len(
            snapshot_forms
        ), "Snapshot should return same form count as select_forms()"

        if selected_forms:
            snapshot_ids = {e.internal_id for e in snapshot_forms}
            selected_ids = {form.internal_id for form in selected_forms}

            assert (
                selected_ids == snapshot_ids
            ), "Snapshot and select_forms() should return identical form IDs"


def test_page_snapshot_matches_select_form_fields():
    """Test that page snapshot form field data matches select_form_fields() results."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        page = pdf.page(1)

        snapshot = pdf.get_page_snapshot(1)
        snapshot_form_fields = [
            e
            for e in snapshot.elements
            if e.type
            in (
                ObjectType.FORM_FIELD,
                ObjectType.TEXT_FIELD,
                ObjectType.CHECKBOX,
                ObjectType.RADIO_BUTTON,
            )
        ]

        selected_form_fields = page.select_form_fields()

        assert len(selected_form_fields) == len(
            snapshot_form_fields
        ), "Snapshot should return same form field count as select_form_fields()"

        if selected_form_fields:
            snapshot_ids = {e.internal_id for e in snapshot_form_fields}
            selected_ids = {field.internal_id for field in selected_form_fields}

            assert (
                selected_ids == snapshot_ids
            ), "Snapshot and select_form_fields() should return identical form field IDs"


def test_page_snapshot_contains_all_element_types():
    """Test that page snapshot contains all expected element types with valid data."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        snapshot = pdf.get_page_snapshot(1)

        # Count elements by type
        text_line_count = sum(
            1 for e in snapshot.elements if e.type == ObjectType.TEXT_LINE
        )

        # Verify we have at least some text elements
        assert text_line_count > 0, "Page should expose TEXT_LINE elements"

        # Verify all elements have required fields
        for element in snapshot.elements:
            assert element.type is not None, "Element should have a type"
            assert element.internal_id is not None, "Element should have an internal ID"
            assert element.position is not None, "Element should have a position"


def test_document_snapshot_matches_all_pages():
    """Test that document snapshot matches individual page snapshots."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        doc_snapshot = pdf.get_document_snapshot()

        # Verify each page matches individual page snapshot
        for i in range(1, doc_snapshot.page_count + 1):
            doc_page_snap = doc_snapshot.pages[i - 1]
            individual_page_snap = pdf.get_page_snapshot(i)

            assert len(individual_page_snap.elements) == len(
                doc_page_snap.elements
            ), f"Page {i} element count should match between document and individual snapshot"

            doc_page_ids = {e.internal_id for e in doc_page_snap.elements}
            individual_page_ids = {e.internal_id for e in individual_page_snap.elements}

            assert (
                individual_page_ids == doc_page_ids
            ), f"Page {i} should have identical elements in document and individual snapshots"


def test_multiple_type_filters_combined():
    """Test that multiple type filters work correctly when combined."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        # Get snapshot with multiple type filter
        multi_snapshot = pdf.get_page_snapshot(1, "TEXT_LINE,IMAGE")

        # Verify only specified types are present
        assert all(
            e.type in (ObjectType.TEXT_LINE, ObjectType.IMAGE)
            for e in multi_snapshot.elements
        ), "Multi-type filter should only contain specified types"

        # Count should be sum of those types from unfiltered snapshot
        full_snapshot = pdf.get_page_snapshot(1)
        expected_count = sum(
            1
            for e in full_snapshot.elements
            if e.type in (ObjectType.TEXT_LINE, ObjectType.IMAGE)
        )

        assert expected_count == len(
            multi_snapshot.elements
        ), "Multi-type filter should return correct combined count"


def test_total_element_count_matches_expected():
    """Test that total element count matches expected values."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        all_elements = pdf.select_elements()
        assert all_elements, "Showcase.pdf should expose selectable elements"
        assert any(
            e.object_type == ObjectType.TEXT_LINE for e in all_elements
        ), "Showcase.pdf should expose text lines"
        assert any(
            e.object_type == ObjectType.IMAGE for e in all_elements
        ), "Showcase.pdf should expose images"

        doc_snapshot = pdf.get_document_snapshot()
        snapshot_total = sum(len(p.elements) for p in doc_snapshot.pages)

        assert snapshot_total == len(
            all_elements
        ), "Document snapshot total should match select_elements() count"

        # Verify page count
        assert len(pdf.pages()) == 7, "Should have 7 pages"


def test_snapshot_consistency_across_multiple_pages():
    """Test that snapshots are consistent across multiple pages."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        doc_snapshot = pdf.get_document_snapshot()

        assert doc_snapshot.page_count > 1, "Need multiple pages for this test"

        # Test that each page's snapshot is independent
        for i in range(1, min(4, doc_snapshot.page_count + 1)):
            page_snap = pdf.get_page_snapshot(i)
            assert page_snap is not None, f"Page {i} snapshot should not be None"
            assert (
                page_snap.page_ref.position.page_number == i
            ), "Page snapshot should have correct page number"


@pytest.mark.skip(reason="TODO Not yet implemented")
def test_document_snapshot_contains_fonts():
    """Test that document snapshot includes font information."""
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        doc_snapshot = pdf.get_document_snapshot()

        # Should have fonts
        assert (
            doc_snapshot.fonts is not None
        ), "Document snapshot should have fonts list"
        assert len(doc_snapshot.fonts) > 0, "Document should have at least one font"

        # Verify font structure
        for font in doc_snapshot.fonts:
            assert font.font_name is not None, "Font should have a name"
            assert font.font_type is not None, "Font should have a type"
            assert (
                font.similarity_score is not None
            ), "Font should have similarity score"
