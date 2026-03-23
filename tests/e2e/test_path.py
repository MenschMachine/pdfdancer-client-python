import pytest

from pdfdancer import Color, ObjectType
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_find_paths():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.select_paths()
        assert len(paths) == 9
        assert paths[0].type == ObjectType.PATH

        p1 = paths[0]
        assert p1 is not None
        assert p1.internal_id == "PATH_0_000001"
        assert pytest.approx(p1.position.x(), rel=0, abs=1) == 80
        assert pytest.approx(p1.position.y(), rel=0, abs=1) == 720

        (PDFAssertions(pdf).assert_path_is_at("PATH_0_000001", 80, 720))


def test_find_paths_by_position():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths_at(80, 720)
        assert len(paths) == 1
        assert paths[0].internal_id == "PATH_0_000001"


def test_delete_path():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        assert len(pdf.select_paths()) == 9
        paths = pdf.page(1).select_paths_at(80, 720)
        assert len(paths) == 1
        path = paths[0]
        assert path.internal_id == "PATH_0_000001"

        path.delete()

        # Should no longer exist at that position
        assert pdf.page(1).select_paths_at(80, 720) == []

        # Remaining paths should be 8 total
        assert len(pdf.select_paths()) == 8

        (PDFAssertions(pdf).assert_no_path_at(80, 720).assert_number_of_paths(8))


def test_move_path():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        path = pdf.page(1).select_paths_at(80, 720)[0]
        pos = path.position

        assert pytest.approx(pos.x(), rel=0, abs=1) == 80
        assert pytest.approx(pos.y(), rel=0, abs=1) == 720

        path.move_to(50.1, 100)

        # Should be gone from old location
        assert pdf.page(1).select_paths_at(80, 720) == []

        # Should now exist at new location
        new_path = pdf.page(1).select_paths_at(50.1, 100)[0]
        new_pos = new_path.position
        assert pytest.approx(new_pos.x(), rel=0, abs=0.05) == 50.1
        assert pytest.approx(new_pos.y(), rel=0, abs=0.05) == 100

        (
            PDFAssertions(pdf)
            .assert_no_path_at(80, 720)
            .assert_path_is_at("PATH_0_000001", 50.1, 100)
        )


def test_modify_path_colors():
    """Test modifying stroke and fill colors of a path."""
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        # PATH_0_000001 is a line at (80, 720)
        path = pdf.page(1).select_paths_at(80, 720)[0]
        assert path.internal_id == "PATH_0_000001"

        # Modify the stroke color to red
        red = Color(255, 0, 0)
        result = path.edit().stroke_color(red).apply()
        assert result.success, f"Expected success but got: {result.message}"

        # Re-fetch path via select_paths() to verify the stroke color was actually changed
        # Note: select_paths_at() goes to API which doesn't return colors,
        # select_paths() uses snapshot which includes color data
        paths_after_stroke = [p for p in pdf.select_paths() if p.internal_id == "PATH_0_000001"]
        assert len(paths_after_stroke) == 1
        path_after_stroke = paths_after_stroke[0]
        stroke_color = path_after_stroke.get_stroke_color()
        assert stroke_color is not None, "Expected stroke color to be set after modification"
        assert stroke_color.r == 255, f"Expected red=255 but got {stroke_color.r}"
        assert stroke_color.g == 0, f"Expected green=0 but got {stroke_color.g}"
        assert stroke_color.b == 0, f"Expected blue=0 but got {stroke_color.b}"

        # Modify both stroke and fill colors
        blue = Color(0, 0, 255)
        result = path.edit().stroke_color(red).fill_color(blue).apply()
        assert result.success, f"Expected success but got: {result.message}"

        # Re-fetch via select_paths() to verify both colors were actually changed
        paths_after_both = [p for p in pdf.select_paths() if p.internal_id == "PATH_0_000001"]
        assert len(paths_after_both) == 1
        path_after_both = paths_after_both[0]
        stroke_color = path_after_both.get_stroke_color()
        fill_color = path_after_both.get_fill_color()
        assert stroke_color is not None, "Expected stroke color to be set"
        assert fill_color is not None, "Expected fill color to be set after modification"
        assert stroke_color.r == 255, f"Expected stroke red=255 but got {stroke_color.r}"
        assert stroke_color.g == 0, f"Expected stroke green=0 but got {stroke_color.g}"
        assert stroke_color.b == 0, f"Expected stroke blue=0 but got {stroke_color.b}"
        assert fill_color.r == 0, f"Expected fill red=0 but got {fill_color.r}"
        assert fill_color.g == 0, f"Expected fill green=0 but got {fill_color.g}"
        assert fill_color.b == 255, f"Expected fill blue=255 but got {fill_color.b}"
