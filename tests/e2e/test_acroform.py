from pdfdancer import ObjectType
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture


def test_find_form_fields():
    base_url, token, pdf_path = _require_env_and_fixture("mixed-form-types.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        form_fields = pdf.select_form_fields()
        assert len(form_fields) == 10
        assert form_fields[0].object_type == ObjectType.TEXT_FIELD
        assert form_fields[4].object_type == ObjectType.CHECK_BOX
        assert form_fields[6].object_type == ObjectType.RADIO_BUTTON

        # Verify not all fields at origin
        all_at_origin = all(
            abs(f.position.x()) < 1e-6 and abs(f.position.y()) < 1e-6
            for f in form_fields
        )
        assert not all_at_origin, "All forms should not be at coordinates (0,0)"

        first_page_fields = pdf.page(0).select_form_fields()
        assert len(first_page_fields) == 10

        first_form = pdf.page(0).select_form_fields_at(290, 460)
        assert len(first_form) == 1
        f = first_form[0]
        assert f.object_type == ObjectType.RADIO_BUTTON
        assert f.internal_id == "FORM_FIELD_000008"


def test_delete_form_fields():
    base_url, token, pdf_path = _require_env_and_fixture("mixed-form-types.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        form_fields = pdf.select_form_fields()
        assert len(form_fields) == 10

        to_delete = form_fields[5]
        to_delete.delete()

        all_form_fields = pdf.select_form_fields()
        assert len(all_form_fields) == 9
        assert all(f.internal_id != to_delete.internal_id for f in all_form_fields)


def test_move_form_field():
    base_url, token, pdf_path = _require_env_and_fixture("mixed-form-types.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        form_fields = pdf.page(0).select_form_fields_at(290, 460)
        assert len(form_fields) == 1
        f = form_fields[0]
        assert abs(f.position.x() - 280) < 0.1
        assert abs(f.position.y() - 455) < 0.1

        f.move_to(30, 40)

        assert pdf.page(0).select_form_fields_at(290, 460) == []

        moved = pdf.page(0).select_form_fields_at(30, 40)
        assert len(moved) == 1
        assert moved[0].internal_id == f.internal_id


def test_edit_form_fields():
    base_url, token, pdf_path = _require_env_and_fixture("mixed-form-types.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        fields = pdf.select_form_fields_by_name("firstName")
        assert len(fields) == 1
        f = fields[0]
        assert f.name == "firstName"
        assert f.value is None
        assert f.object_type == ObjectType.TEXT_FIELD
        assert f.internal_id == "FORM_FIELD_000001"

        f.edit().value("Donald Duck").apply()

        updated = pdf.select_form_fields_by_name("firstName")[0]
        assert updated.name == "firstName"
        assert updated.value == "Donald Duck"
