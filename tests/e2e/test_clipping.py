from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_examples_fixture
from tests.e2e.pdf_assertions import PDFAssertions

CLIPPING_FIXTURE = "clipping/invisible-content-clipping-test.pdf"
TEXT_CLIPPING_FIXTURE = "clipping/basic-text-clipping-test.pdf"
TARGET_PATH_ID = "PATH_0_000004"
CONTROL_PATH_ID = "PATH_0_000003"
TARGET_TEXT_LINE = "This text extends beyond the clipping area"
TARGET_PARAGRAPH_PREFIX = "Line 1: This is a long text that should be clipped"


def test_clear_clipping_via_path_reference():
    base_url, token, pdf_path = _require_env_and_examples_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        path = next(
            p for p in pdf.page(1).select_paths() if p.internal_id == TARGET_PATH_ID
        )

        (
            PDFAssertions(pdf)
            .assert_path_has_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3)
        )

        assert path.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3)
        )


def test_clear_clipping_via_pdfdancer_object_ref_api():
    base_url, token, pdf_path = _require_env_and_examples_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        path = next(
            p for p in pdf.page(1).select_paths() if p.internal_id == TARGET_PATH_ID
        )

        PDFAssertions(pdf).assert_path_has_clipping(TARGET_PATH_ID)

        assert pdf.clear_clipping(path.object_ref()) is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
        )


def test_clear_path_group_clipping_via_reference():
    base_url, token, pdf_path = _require_env_and_examples_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            PDFAssertions(pdf)
            .assert_path_has_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
        )

        group = pdf.page(1).group_paths([TARGET_PATH_ID])
        assert group.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3)
        )


def test_clear_path_group_clipping_via_pdfdancer_api():
    base_url, token, pdf_path = _require_env_and_examples_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            PDFAssertions(pdf)
            .assert_path_has_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
        )

        group = pdf.page(1).group_paths([TARGET_PATH_ID])
        assert pdf.clear_path_group_clipping(1, group.group_id) is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3)
        )


def test_clear_clipping_via_image_reference():
    base_url, token, pdf_path = _require_env_and_examples_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        image = pdf.page(1).select_images()[0]

        (
            PDFAssertions(pdf)
            .assert_image_has_clipping(image.internal_id)
            .assert_path_has_clipping(TARGET_PATH_ID)
        )

        assert image.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_image_has_no_clipping(image.internal_id)
            .assert_path_has_clipping(TARGET_PATH_ID)
            .assert_image_with_id_at(image.internal_id, 200, 400)
        )


def test_clear_clipping_via_text_line_reference():
    base_url, token, pdf_path = _require_env_and_examples_fixture(TEXT_CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        text_line = next(
            line
            for line in pdf.page(1).select_text_lines()
            if line.text == TARGET_TEXT_LINE
        )
        control_paragraph = next(
            paragraph
            for paragraph in pdf.page(1).select_paragraphs()
            if paragraph.text.startswith(TARGET_PARAGRAPH_PREFIX)
        )

        (
            PDFAssertions(pdf)
            .assert_text_line_has_clipping(text_line.internal_id)
            .assert_paragraph_has_clipping(control_paragraph.internal_id)
            .assert_textline_exists(TARGET_TEXT_LINE)
            .assert_paragraph_exists(TARGET_PARAGRAPH_PREFIX)
        )

        assert text_line.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_text_line_has_no_clipping(text_line.internal_id)
            .assert_paragraph_has_clipping(control_paragraph.internal_id)
            .assert_textline_exists(TARGET_TEXT_LINE)
            .assert_paragraph_exists(TARGET_PARAGRAPH_PREFIX)
        )


def test_clear_clipping_via_paragraph_reference():
    base_url, token, pdf_path = _require_env_and_examples_fixture(TEXT_CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = next(
            paragraph
            for paragraph in pdf.page(1).select_paragraphs()
            if paragraph.text.startswith(TARGET_PARAGRAPH_PREFIX)
        )
        control_text_line = next(
            line
            for line in pdf.page(1).select_text_lines()
            if line.text == TARGET_TEXT_LINE
        )

        (
            PDFAssertions(pdf)
            .assert_paragraph_has_clipping(paragraph.internal_id)
            .assert_text_line_has_clipping(control_text_line.internal_id)
            .assert_paragraph_exists(TARGET_PARAGRAPH_PREFIX)
            .assert_textline_exists(TARGET_TEXT_LINE)
        )

        assert paragraph.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_paragraph_has_no_clipping(paragraph.internal_id)
            .assert_text_line_has_clipping(control_text_line.internal_id)
            .assert_paragraph_exists(TARGET_PARAGRAPH_PREFIX)
            .assert_textline_exists(TARGET_TEXT_LINE)
        )
