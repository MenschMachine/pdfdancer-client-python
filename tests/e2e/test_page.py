from pdfdancer import ObjectType, Orientation, PageSize, PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_get_all_elements():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        assert (
            95 <= len(pdf.select_elements()) <= 97
        ), f"{len(pdf.select_elements())} elements found but  95-97 elements expected"
        actual_total = 0
        for page in pdf.pages():
            actual_total += len(page.select_elements())
        assert (
            95 <= actual_total <= 97
        ), f"{actual_total} elements found but  95-97 elements expected"


def test_get_pages():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        pages = pdf.pages()
        assert pages is not None
        assert len(pages) == 7
        assert pages[0].object_type == ObjectType.PAGE


def test_get_page():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        page = pdf.page(3)
        assert page is not None
        assert page.position.page_number == 3
        assert page.internal_id is not None


def test_delete_page():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        page3 = pdf.page(3)
        page3.delete()

        pages_after = pdf.pages()
        assert len(pages_after) == 6

        (PDFAssertions(pdf).assert_number_of_pages(6))


def test_move_page():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        pages_before = pdf.pages()
        assert len(pages_before) == 7
        assert pdf.move_page(1, 7)

        (
            PDFAssertions(pdf).assert_paragraph_exists(
                "This is regular Sans text showing alignment and styles.", 7
            )
        )


def test_add_page():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        pages_before = pdf.pages()
        assert len(pages_before) == 7
        pdf.new_page(orientation=Orientation.LANDSCAPE, size=PageSize.A4).add()
        pages_after = pdf.pages()
        assert len(pages_after) == 8
        assert pages_after[7].position.page_number == 8
        assert pages_after[7].internal_id is not None


def test_add_page_with_builder_default():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        pages_before = pdf.pages()
        assert len(pages_before) == 7

        page_ref = pdf.new_page().add()

        assert page_ref.position.page_number == 8
        pages_after = pdf.pages()
        assert len(pages_after) == 8


def test_add_page_with_builder_a4_portrait():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        assert len(pdf.pages()) == 7

        page_ref = pdf.new_page().a4().portrait().add()

        assert page_ref.position.page_number == 8
        assert len(pdf.pages()) == 8


def test_add_page_with_builder_letter_landscape():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        assert len(pdf.pages()) == 7

        page_ref = pdf.new_page().letter().landscape().add()

        assert page_ref.position.page_number == 8
        assert len(pdf.pages()) == 8


def test_add_page_with_builder_at_index():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        assert len(pdf.pages()) == 7

        page_ref = pdf.new_page().at_index(5).a5().landscape().add()

        assert page_ref.position.page_number == 6
        assert len(pdf.pages()) == 8

        (
            PDFAssertions(pdf)
            .assert_page_dimension(
                PageSize.A5.width, PageSize.A5.height, Orientation.LANDSCAPE, 6
            )
            .assert_total_number_of_elements(0, 6)
        )


def test_add_page_with_builder_custom_size():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        assert len(pdf.pages()) == 7

        page_ref = pdf.new_page().custom_size(400, 600).landscape().add()

        assert page_ref.position.page_number == 8
        assert len(pdf.pages()) == 8


def test_add_page_with_builder_all_options():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        assert len(pdf.pages()) == 7

        page_ref = (
            pdf.new_page()
            .at_index(3)
            .page_size(PageSize.A3)
            .orientation(Orientation.LANDSCAPE)
            .add()
        )

        assert page_ref.position.page_number == 4
        assert len(pdf.pages()) == 8
