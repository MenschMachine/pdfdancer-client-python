from pathlib import Path

from pdfdancer import ObjectType
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_delete_form(tmp_path: Path):
    base_url, token, pdf_path = _require_env_and_fixture("form-xobject-example.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        all_elements = pdf.select_elements()
        forms = pdf.select_forms()
        assert len(forms) == 17
        assert forms[0].object_type == ObjectType.FORM_X_OBJECT

        # Delete all form XObjects
        for form in forms:
            form.delete()

        assert pdf.select_forms() == []
        assert len(pdf.select_elements()) == len(all_elements) - 17
        pdf.save("/tmp/delete-form1.pdf")

        (PDFAssertions(pdf).assert_number_of_formxobjects(0))


def test_find_form_by_position():
    base_url, token, pdf_path = _require_env_and_fixture("form-xobject-example.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        none_found = pdf.page(1).select_forms_at(0, 0)
        assert len(none_found) == 0

        found = pdf.page(1).select_forms_at(320, 600)
        assert len(found) == 1
        assert found[0].internal_id == "FORM_000005"
