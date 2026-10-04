from pdfdancer.pdfdancer_v2 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions

CLIPPING_FIXTURE = "invisible-content-clipping-test.pdf"
# The fixture's blue circle is the target; its red stroked rectangle is the
# control path. Use their bounds because path IDs can change after mutations.
TARGET_PATH_BOUNDS = (260, 460, 80, 80)
CONTROL_PATH_BOUNDS = (100, 300, 120, 80)


def _path_with_bounds(pdf, bounds, epsilon=0.1):
    x, y, width, height = bounds
    matches = [
        path
        for path in pdf.page(1).select_paths()
        if path.position.bounding_rect is not None
        and abs(path.position.bounding_rect.x - x) <= epsilon
        and abs(path.position.bounding_rect.y - y) <= epsilon
        and abs(path.position.bounding_rect.width - width) <= epsilon
        and abs(path.position.bounding_rect.height - height) <= epsilon
    ]
    assert len(matches) == 1, (
        f"Expected exactly one path with bounds {bounds}, found {len(matches)}"
    )
    return matches[0]


def _assert_path_clipping(pdf, bounds, *, clipped):
    assertions = PDFAssertions(pdf)
    # PDFAssertions saves and reopens the document, which can regenerate IDs.
    path = _path_with_bounds(assertions.get_pdf(), bounds)
    if clipped:
        assertions.assert_path_has_clipping(path.internal_id)
    else:
        assertions.assert_path_has_no_clipping(path.internal_id)


def test_clear_clipping_via_path_reference():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        path = _path_with_bounds(pdf, TARGET_PATH_BOUNDS)

        _assert_path_clipping(pdf, TARGET_PATH_BOUNDS, clipped=True)
        _assert_path_clipping(pdf, CONTROL_PATH_BOUNDS, clipped=True)
        PDFAssertions(pdf).assert_number_of_paths(3, 1)

        assert path.clear_clipping() is True

        _assert_path_clipping(pdf, TARGET_PATH_BOUNDS, clipped=False)
        _assert_path_clipping(pdf, CONTROL_PATH_BOUNDS, clipped=True)
        PDFAssertions(pdf).assert_number_of_paths(3, 1)


def test_clear_clipping_via_pdf_api():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        path = _path_with_bounds(pdf, TARGET_PATH_BOUNDS)

        _assert_path_clipping(pdf, TARGET_PATH_BOUNDS, clipped=True)

        assert pdf.clear_clipping(path.object_ref()) is True

        _assert_path_clipping(pdf, TARGET_PATH_BOUNDS, clipped=False)
        _assert_path_clipping(pdf, CONTROL_PATH_BOUNDS, clipped=True)


def test_clear_path_group_clipping_via_reference():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        _assert_path_clipping(pdf, TARGET_PATH_BOUNDS, clipped=True)
        _assert_path_clipping(pdf, CONTROL_PATH_BOUNDS, clipped=True)

        path = _path_with_bounds(pdf, TARGET_PATH_BOUNDS)
        group = pdf.page(1).group_paths([path.internal_id])
        assert group.group_id is not None
        assert group.clear_clipping() is True

        _assert_path_clipping(pdf, TARGET_PATH_BOUNDS, clipped=False)
        _assert_path_clipping(pdf, CONTROL_PATH_BOUNDS, clipped=True)
        PDFAssertions(pdf).assert_number_of_paths(3, 1)


def test_clear_path_group_clipping_via_pdf_api():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        _assert_path_clipping(pdf, TARGET_PATH_BOUNDS, clipped=True)
        _assert_path_clipping(pdf, CONTROL_PATH_BOUNDS, clipped=True)

        path = _path_with_bounds(pdf, TARGET_PATH_BOUNDS)
        group = pdf.page(1).group_paths([path.internal_id])
        assert group.group_id is not None
        assert pdf.clear_path_group_clipping(1, group.group_id) is True

        _assert_path_clipping(pdf, TARGET_PATH_BOUNDS, clipped=False)
        _assert_path_clipping(pdf, CONTROL_PATH_BOUNDS, clipped=True)
        PDFAssertions(pdf).assert_number_of_paths(3, 1)


def test_clear_clipping_via_image_reference():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        image = pdf.page(1).select_images()[0]

        PDFAssertions(pdf).assert_image_has_clipping(image.internal_id)
        _assert_path_clipping(pdf, TARGET_PATH_BOUNDS, clipped=True)

        assert image.clear_clipping() is True

        PDFAssertions(pdf).assert_image_has_no_clipping(image.internal_id)
        _assert_path_clipping(pdf, TARGET_PATH_BOUNDS, clipped=True)
        PDFAssertions(pdf).assert_image_with_id_at(image.internal_id, 200, 400)
