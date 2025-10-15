from pdfdancer import ClientV1, Position, ObjectType
from tests.e2e import _require_env_and_fixture


def test_find_form_fields():
    """Test findFormFields equivalent functionality."""
    base_url, token, pdf_path = _require_env_and_fixture('mixed-form-types.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url) as client:
        form_fields = client.find_form_fields()
        assert len(form_fields) == 10
        assert form_fields[0].type == ObjectType.TEXT_FIELD
        assert form_fields[4].type == ObjectType.CHECK_BOX
        assert form_fields[6].type == ObjectType.RADIO_BUTTON

        all_forms_at_origin = True
        for form in form_fields:
            pos = form.position
            if pos.x() != 0.0 or pos.y() != 0.0:
                all_forms_at_origin = False
        assert not all_forms_at_origin, "All forms should not be at coordinates (0,0)"

        first_page_fields = client.find_form_fields(Position.at_page(0))
        assert len(first_page_fields) == 10

        first_form = client.find_form_fields(Position.at_page_coordinates(0, 290, 460))
        assert len(first_form) == 1
        assert first_form[0].type == ObjectType.RADIO_BUTTON
        assert first_form[0].internal_id == "FORM_FIELD_000008"


def test_delete_form_fields():
    """Test deleteFormFields equivalent functionality."""
    base_url, token, pdf_path = _require_env_and_fixture('mixed-form-types.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url) as client:
        form_fields = client.find_form_fields()
        assert len(form_fields) == 10
        object_ref_to_delete = form_fields[5]
        client.delete(object_ref_to_delete)
        all_form_fields = client.find_form_fields()
        assert len(all_form_fields) == 9
        for field_ref in all_form_fields:
            assert field_ref.internal_id != object_ref_to_delete.internal_id


def test_move_form_field():
    """Test moving form fields."""
    base_url, token, pdf_path = _require_env_and_fixture('mixed-form-types.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url) as client:
        form_fields = client.find_form_fields(Position.at_page_coordinates(0, 290, 460))
        assert len(form_fields) == 1
        object_ref = form_fields[0]
        assert abs(object_ref.position.x() - 280) < 0.1
        assert abs(object_ref.position.y() - 455) < 0.1

        client.move(object_ref, Position.at_page_coordinates(0, 30, 40))

        form_fields = client.find_form_fields(Position.at_page_coordinates(0, 290, 460))
        assert len(form_fields) == 0

        form_fields = client.find_form_fields(Position.at_page_coordinates(0, 30, 40))
        assert len(form_fields) == 1
        assert form_fields[0].internal_id == object_ref.internal_id


def test_edit_form_fields():
    """Test editing form field values."""
    base_url, token, pdf_path = _require_env_and_fixture('mixed-form-types.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url) as client:
        form_fields = client.find_form_fields(Position.by_name("firstName"))
        assert len(form_fields) == 1
        object_ref = form_fields[0]
        assert object_ref.name == "firstName"
        assert object_ref.value is None
        assert object_ref.type == ObjectType.TEXT_FIELD
        assert object_ref.internal_id == "FORM_FIELD_000001"

        assert client.change_form_field(object_ref, "Donald Duck")

        form_fields = client.find_form_fields(Position.by_name("firstName"))
        object_ref = form_fields[0]
        assert object_ref.name == "firstName"
        assert object_ref.value == "Donald Duck"