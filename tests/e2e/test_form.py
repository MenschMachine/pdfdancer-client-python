from pathlib import Path

from pdfdancer import ClientV1, Position, ObjectType
from tests.e2e import _require_env_and_fixture


def test_delete_form(tmp_path: Path):
    base_url, token, pdf_path = _require_env_and_fixture('mixed-form-types.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        forms = client.find_forms(None)
        assert len(forms) == 79
        assert forms[0].type == ObjectType.FORM

        # Delete all
        for f in forms:
            assert client.delete(f) is True

        assert client.find_forms(None) == []

        out = tmp_path / 'forms-after-delete.pdf'
        client.save_pdf(out)
        assert out.exists() and out.stat().st_size > 0


def test_find_form_by_position():
    base_url, token, pdf_path = _require_env_and_fixture('mixed-form-types.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        forms = client.find_forms(Position.at_page_coordinates(0, 0, 0))
        assert len(forms) == 0

        forms = client.find_forms(Position.at_page_coordinates(0, 17, 447))
        assert len(forms) == 1
        assert forms[0].internal_id == 'FORM_000001'
