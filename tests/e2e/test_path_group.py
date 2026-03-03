from pdfdancer.pdfdancer_v1 import PDFDancer
from pdfdancer.types import BoundingRect
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_create_group_by_path_ids():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        assert len(paths) >= 2

        path_ids = [paths[0].internal_id, paths[1].internal_id]
        group = pdf.page(1).group_paths("by-ids", path_ids)

        assert group.group_id == "by-ids"
        assert group.path_count == 2
        assert group.bounding_box is not None

        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
            .assert_path_is_at("PATH_0_000001", 80, 720)
        )


def test_create_group_by_region():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        region = BoundingRect(x=70, y=710, width=100, height=100)
        group = pdf.page(1).group_paths_in_region("region-test", region)

        assert group is not None
        assert group.group_id == "region-test"
        assert group.path_count > 0

        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
            .assert_path_is_at("PATH_0_000001", 80, 720)
        )


def test_list_empty_groups():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        groups = pdf.page(1).get_path_groups()
        assert groups is not None
        assert len(groups) == 0

        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
            .assert_path_is_at("PATH_0_000001", 80, 720)
        )


def test_group_and_move():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_ids = [paths[0].internal_id, paths[1].internal_id]

        pdf.page(1).group_paths("move-test", path_ids)
        pdf.move_path_group(0, "move-test", 200.0, 300.0)

        groups = pdf.page(1).get_path_groups()
        assert len(groups) == 1
        assert abs(groups[0].x - 200.0) < 0.01
        assert abs(groups[0].y - 300.0) < 0.01

        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
            .assert_no_path_at(80, 720)
        )


def test_group_and_remove():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_ids = [paths[0].internal_id]

        pdf.page(1).group_paths("remove-test", path_ids)

        groups = pdf.page(1).get_path_groups()
        assert len(groups) == 1

        pdf.remove_path_group(0, "remove-test")

        groups = pdf.page(1).get_path_groups()
        assert len(groups) == 0

        (
            PDFAssertions(pdf)
            .assert_number_of_paths(8)
            .assert_no_path_at(80, 720)
        )


def test_scale_path_group():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_ids = [paths[0].internal_id, paths[1].internal_id]

        pdf.page(1).group_paths("scale-test", path_ids)
        pdf.scale_path_group(0, "scale-test", 2.0)

        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
        )


def test_rotate_path_group():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_ids = [paths[0].internal_id, paths[1].internal_id]

        pdf.page(1).group_paths("rotate-test", path_ids)
        pdf.rotate_path_group(0, "rotate-test", 90.0)

        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
            .assert_no_path_at(80, 720)
        )


def test_resize_path_group():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_ids = [paths[0].internal_id, paths[1].internal_id]

        pdf.page(1).group_paths("resize-test", path_ids)
        pdf.resize_path_group(0, "resize-test", 50.0, 50.0)

        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
        )


def test_scale_via_reference():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_ids = [paths[0].internal_id, paths[1].internal_id]

        group = pdf.page(1).group_paths("scale-ref-test", path_ids)
        group.scale(0.5)

        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
        )


def test_move_and_remove_via_reference():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_ids = [paths[0].internal_id, paths[1].internal_id]

        group = pdf.page(1).group_paths("ref-test", path_ids)
        group.move_to(150.0, 250.0)

        groups = pdf.page(1).get_path_groups()
        assert len(groups) == 1
        assert abs(groups[0].x - 150.0) < 0.01
        assert abs(groups[0].y - 250.0) < 0.01

        group.remove()

        groups = pdf.page(1).get_path_groups()
        assert len(groups) == 0

        (
            PDFAssertions(pdf)
            .assert_number_of_paths(7)
            .assert_no_path_at(80, 720)
        )
