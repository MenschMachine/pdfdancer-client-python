from pdfdancer import PDFDancer, ReadingUnitMode, ReadingUnitRole
from tests.e2e import _require_env_and_fixture


def test_document_and_page_reading_units_expose_complete_page_data():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")
    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        document = pdf.analyze_reading_units()
        assert document.mode is ReadingUnitMode.PRIMARY
        assert document.page_count > 0
        assert len(document.pages) == document.page_count
        assert [page.page_number for page in document.pages] == list(
            range(1, document.page_count + 1)
        )

        page = pdf.page(1).analyze_reading_units()
        assert page == document.pages[0]
        assert page.units

        unit = page.units[0]
        assert unit.role in set(ReadingUnitRole)
        assert unit.raw_role
        assert unit.id
        assert isinstance(unit.text, str)
        assert unit.provenance.page_number == 1
        assert unit.provenance.source_element_ids
        assert unit.provenance.bounds.width >= 0
        assert unit.provenance.bounds.height >= 0
        assert unit.stream["PRIMARY"].included is True
        assert unit.stream["PRIMARY"].order > 0


def test_each_reading_unit_analysis_call_is_fresh():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")
    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        first = pdf.page(1).analyze_reading_units()
        second = pdf.page(1).analyze_reading_units()
        assert second == first
