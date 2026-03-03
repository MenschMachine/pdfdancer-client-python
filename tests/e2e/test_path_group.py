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
        group = pdf.page(1).group_paths(path_ids)

        assert group.group_id is not None
        assert group.path_count == 2
        assert group.bounding_box is not None

        # Grouping without move should not change the PDF
        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
            .assert_path_is_at("PATH_0_000001", 80, 720)
        )


def test_group_paths_in_region():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        region = BoundingRect(x=70, y=710, width=100, height=100)
        group = pdf.page(1).group_paths_in_region(region)

        assert group is not None
        assert group.group_id is not None
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

        group = pdf.page(1).group_paths(path_ids)
        group.move_to(200.0, 300.0)

        groups = pdf.page(1).get_path_groups()
        assert len(groups) == 1
        assert abs(groups[0].x - 200.0) < 0.01
        assert abs(groups[0].y - 300.0) < 0.01

        # Paths should have moved away from original positions
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

        group = pdf.page(1).group_paths(path_ids)

        groups = pdf.page(1).get_path_groups()
        assert len(groups) == 1

        group.remove()

        groups = pdf.page(1).get_path_groups()
        assert len(groups) == 0

        # Removing a group deletes its paths from the PDF
        (
            PDFAssertions(pdf)
            .assert_number_of_paths(8)
            .assert_no_path_at(80, 720)
        )


def test_scale_path_group():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_id = paths[0].internal_id
        path_ids = [path_id, paths[1].internal_id]

        # Record original bounds
        orig_bbox = paths[0].position.bounding_rect
        orig_w = orig_bbox.width
        orig_h = orig_bbox.height

        group = pdf.page(1).group_paths(path_ids)
        group.scale(2.0)

        # After scaling 2x, path bounds should roughly double
        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
            .assert_path_has_bounds(path_id, orig_w * 2, orig_h * 2, epsilon=2.0)
        )


def test_rotate_path_group():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_ids = [paths[0].internal_id, paths[1].internal_id]

        group = pdf.page(1).group_paths(path_ids)
        group.rotate(90.0)

        # Paths should have moved from original positions after 90° rotation
        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
            .assert_no_path_at(80, 720)
        )


def test_resize_path_group():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_id = paths[0].internal_id
        path_ids = [path_id, paths[1].internal_id]

        # Record original bounds
        orig_bbox = paths[0].position.bounding_rect

        group = pdf.page(1).group_paths(path_ids)
        group.resize(50.0, 50.0)

        # After resize, path bounds should have changed from original
        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(9)

        # Verify the path's bounding rect actually changed
        reloaded_paths = assertions.get_pdf().page(1).select_paths()
        reloaded = next(p for p in reloaded_paths if p.internal_id == path_id)
        new_bbox = reloaded.position.bounding_rect
        assert orig_bbox != new_bbox, "Path bounds should change after resize"


def test_scale_via_reference():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_id = paths[0].internal_id
        path_ids = [path_id, paths[1].internal_id]

        # Record original bounds
        orig_bbox = paths[0].position.bounding_rect
        orig_w = orig_bbox.width
        orig_h = orig_bbox.height

        group = pdf.page(1).group_paths(path_ids)
        group.scale(0.5)

        # After scaling 0.5x, path bounds should roughly halve
        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
            .assert_path_has_bounds(path_id, orig_w * 0.5, orig_h * 0.5, epsilon=2.0)
        )


def test_rotate_via_reference():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_ids = [paths[0].internal_id, paths[1].internal_id]

        group = pdf.page(1).group_paths(path_ids)
        group.rotate(45)

        # 45° rotation should move paths from original position
        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
            .assert_no_path_at(80, 720)
        )


def test_move_and_remove_via_reference():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_ids = [paths[0].internal_id, paths[1].internal_id]

        group = pdf.page(1).group_paths(path_ids)
        group.move_to(150.0, 250.0)

        groups = pdf.page(1).get_path_groups()
        assert len(groups) == 1
        assert abs(groups[0].x - 150.0) < 0.01
        assert abs(groups[0].y - 250.0) < 0.01

        group.remove()

        groups = pdf.page(1).get_path_groups()
        assert len(groups) == 0

        # Move then remove: paths are deleted from the PDF
        (
            PDFAssertions(pdf)
            .assert_number_of_paths(7)
            .assert_no_path_at(80, 720)
        )
