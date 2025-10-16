from pdfdancer import PDFDancer, ObjectType
from tests.e2e import _require_env_and_fixture


def test_get_pages():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        pages = pdf.pages()
        assert pages is not None
        assert len(pages) == 12
        assert pages[0].object_type == ObjectType.PAGE


def test_get_page():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        page = pdf.page(2)
        assert page is not None
        assert page.position.page_index == 2
        assert page.internal_id is not None


def test_delete_page():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        page3 = pdf.page(3)
        page3.delete()

        pages_after = pdf.pages()
        assert len(pages_after) == 11
