from pdfdancer import ClientV1, ObjectType
from tests.e2e import _require_env_and_fixture


def test_get_pages():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pages = client.get_pages()
        assert pages is not None
        assert pages[0].type == ObjectType.PAGE
        assert len(pages) == 12


def test_get_page():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        page = client.get_page(2)
        assert page is not None
        assert page.position.page_index == 2
        assert page.internal_id is not None


def test_delete_page():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        page3 = client.get_page(3)
        assert client.delete_page(page3) is True
        new_pages = client.get_pages()
        assert len(new_pages) == 11
