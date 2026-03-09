from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_examples_fixture
from tests.e2e.pdf_assertions import PDFAssertions

CLIPPING_FIXTURE = "clipping/invisible-content-clipping-test.pdf"
TARGET_PATH_ID = "PATH_0_000004"
CONTROL_PATH_ID = "PATH_0_000003"


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
