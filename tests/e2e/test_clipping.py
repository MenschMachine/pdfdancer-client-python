from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions

CLIPPING_FIXTURE = "invisible-content-clipping-test.pdf"
TARGET_PATH_ID = "PATH_0_000004"
CONTROL_PATH_ID = "PATH_0_000003"


def test_clear_clipping_via_path_reference():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        path = next(
            (
                candidate
                for candidate in pdf.page(1).select_paths()
                if candidate.internal_id == TARGET_PATH_ID
            ),
            None,
        )
        assert path is not None

        (
            PDFAssertions(pdf)
            .assert_path_has_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3, 1)
        )

        assert path.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3, 1)
        )


def test_clear_clipping_via_pdf_api():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        path = next(
            (
                candidate
                for candidate in pdf.page(1).select_paths()
                if candidate.internal_id == TARGET_PATH_ID
            ),
            None,
        )
        assert path is not None

        PDFAssertions(pdf).assert_path_has_clipping(TARGET_PATH_ID)

        assert pdf.clear_clipping(path.object_ref()) is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
        )


def test_clear_path_group_clipping_via_reference():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            PDFAssertions(pdf)
            .assert_path_has_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
        )

        group = pdf.page(1).group_paths([TARGET_PATH_ID])
        assert group.group_id is not None
        assert group.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3, 1)
        )


def test_clear_path_group_clipping_via_pdf_api():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            PDFAssertions(pdf)
            .assert_path_has_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
        )

        group = pdf.page(1).group_paths([TARGET_PATH_ID])
        assert group.group_id is not None
        assert pdf.clear_path_group_clipping(1, group.group_id) is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3, 1)
        )


def test_clear_clipping_via_image_reference():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

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
