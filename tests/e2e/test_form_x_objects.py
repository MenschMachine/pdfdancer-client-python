from pathlib import Path

from pdfdancer import ClientV1, Position, ObjectType
from tests.e2e import _require_env_and_fixture


def test_delete_form(tmp_path: Path):
    base_url, token, pdf_path = _require_env_and_fixture('form-xobject-example.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url) as client:
        forms = client.find_form_x_objects(None)
        assert len(forms) == 17
        assert forms[0].type == ObjectType.FORM_X_OBJECT

        # Delete all
        for f in forms:
            assert client.delete(f) is True

        assert client.find_form_x_objects(None) == []

        out = tmp_path / 'forms-after-delete.pdf'
        client.save_pdf(out)
        assert out.exists() and out.stat().st_size > 0


def test_find_form_by_position():
    base_url, token, pdf_path = _require_env_and_fixture('form-xobject-example.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url) as client:
        forms = client.find_form_x_objects(Position.at_page_coordinates(0, 0, 0))
        assert len(forms) == 0

        forms = client.find_form_x_objects(Position.at_page_coordinates(0, 321, 601))
        assert len(forms) == 1
        assert forms[0].internal_id == 'FORM_000005'
