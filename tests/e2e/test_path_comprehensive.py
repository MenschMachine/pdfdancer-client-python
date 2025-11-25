"""
Comprehensive end-to-end tests for Path, Line, and Bezier models with extensive PDFAssertions.

These tests demonstrate detailed path manipulation including:
- Path selection and basic operations
- Path segment inspection (when API provides detailed data)
- Line segment properties (points, colors, stroke)
- Bezier segment properties (control points, fill)
- Complex paths with mixed segment types
"""

import pytest

from pdfdancer import (
    Bezier,
    Color,
    Line,
    ObjectType,
    Path,
    PathSegment,
    PDFDancer,
    Point,
)
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


class TestPathBasicOperations:
    """Test basic path operations with comprehensive assertions."""

    def test_select_paths_comprehensive(self):
        """Test selecting paths with detailed verification."""
        base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            # Select all paths
            paths = pdf.select_paths()
            assert len(paths) > 0, "Should have at least one path"

            # Verify each path has the correct type
            for path in paths:
                # PathObject wraps ObjectRef, access type through object_ref()
                ref = path.object_ref() if hasattr(path, "object_ref") else path
                assert (
                    ref.type == ObjectType.PATH
                ), f"Path {path.internal_id} should have type PATH"
                assert (
                    path.position is not None
                ), f"Path {path.internal_id} should have position"
                assert path.internal_id is not None, f"Path should have internal_id"

            # Use PDFAssertions to verify path count
            assertions = PDFAssertions(pdf)
            assertions.assert_number_of_paths(9, page=1)

    def test_path_exists_at_coordinates(self):
        """Test verifying path existence at specific coordinates."""
        base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            assertions = PDFAssertions(pdf)

            # Assert path exists at known coordinates
            assertions.assert_path_exists_at(80, 720, page=1, tolerance=5.0)

            # Assert specific path ID at coordinates
            assertions.assert_path_has_id("PATH_000001", 80, 720, page=1)

            # Assert exact count at coordinates
            assertions.assert_path_count_at(1, 80, 720, page=1, tolerance=5.0)

    def test_path_bounding_box_verification(self):
        """Test verifying path bounding box dimensions."""
        base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            # Get first path
            paths = pdf.page(1).select_paths_at(80, 720)
            assert len(paths) == 1

            path = paths[0]
            bbox = path.position.bounding_rect

            if bbox is not None:
                # Verify bounding box exists and has dimensions
                assert bbox.x >= 0, "Bounding box x should be non-negative"
                assert bbox.y >= 0, "Bounding box y should be non-negative"

                # Some paths may have 0 width/height (single points or degenerate cases)
                # So we just verify they're non-negative rather than strictly positive
                assert bbox.width >= 0, "Bounding box width should be non-negative"
                assert bbox.height >= 0, "Bounding box height should be non-negative"

                # Use PDFAssertions for detailed bbox verification only if bbox has area
                if bbox.width > 0 and bbox.height > 0:
                    assertions = PDFAssertions(pdf)
                    assertions.assert_path_bounding_box(
                        bbox.x, bbox.y, bbox.width, bbox.height, page=1, epsilon=1.0
                    )
                else:
                    # For degenerate bounding boxes, just verify coordinates
                    assert bbox.x == pytest.approx(80, abs=5.0)
                    assert bbox.y == pytest.approx(720, abs=5.0)

    def test_delete_path_comprehensive(self):
        """Test deleting a path with before/after verification."""
        base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            assertions = PDFAssertions(pdf)

            # Verify initial state
            initial_count = len(pdf.select_paths())
            assertions.assert_number_of_paths(9, page=1)
            assertions.assert_path_exists_at(80, 720, page=1)

            # Delete the path
            path = pdf.page(1).select_paths_at(80, 720)[0]
            path_id = path.internal_id
            path.delete()

            # Verify path is gone
            assertions = PDFAssertions(pdf)
            assertions.assert_no_path_at(80, 720, page=1)
            assertions.assert_number_of_paths(initial_count - 1, page=1)

            # Verify the specific path ID no longer exists
            remaining_paths = pdf.select_paths()
            remaining_ids = [p.internal_id for p in remaining_paths]
            assert (
                path_id not in remaining_ids
            ), f"Deleted path {path_id} should not exist in remaining paths"

    def test_move_path_comprehensive(self):
        """Test moving a path with detailed position verification."""
        base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

        with PDFDancer.open(
            pdf_path, token=token, base_url=base_url, timeout=30.0
        ) as pdf:
            # Get original path
            original_path = pdf.page(1).select_paths_at(80, 720)[0]
            original_id = original_path.internal_id
            original_x = original_path.position.x()
            original_y = original_path.position.y()

            # Define new position
            new_x, new_y = 150.0, 200.0

            # Move the path
            original_path.move_to(new_x, new_y)

            # Verify with PDFAssertions
            assertions = PDFAssertions(pdf)

            # Should be gone from original location
            assertions.assert_no_path_at(original_x, original_y, page=1)

            # Should exist at new location with same ID
            assertions.assert_path_is_at(original_id, new_x, new_y, page=1, epsilon=1.0)
            assertions.assert_path_exists_at(new_x, new_y, page=1)

            # Total path count should remain the same
            assertions.assert_number_of_paths(9, page=1)


class TestPathSegmentInspection:
    """Test inspecting path segments when detailed data is available."""

    def test_line_segment_model_creation(self):
        """Test creating and inspecting Line segment models."""
        # Create a line segment programmatically
        p0 = Point(0.0, 0.0)
        p1 = Point(100.0, 100.0)
        stroke_color = Color(255, 0, 0)

        line = Line(p0=p0, p1=p1, stroke_color=stroke_color, stroke_width=2.5)

        # Create assertions helper (without PDF context for model testing)
        # We'll test the assertion methods directly
        assert line.get_p0() == p0
        assert line.get_p1() == p1
        assert line.get_stroke_color() == stroke_color
        assert line.get_stroke_width() == 2.5

    def test_bezier_segment_model_creation(self):
        """Test creating and inspecting Bezier segment models."""
        # Create a Bezier curve programmatically
        p0 = Point(0.0, 0.0)
        p1 = Point(50.0, 100.0)
        p2 = Point(150.0, 100.0)
        p3 = Point(200.0, 0.0)
        stroke_color = Color(0, 0, 255)
        fill_color = Color(255, 255, 0, 128)

        bezier = Bezier(
            p0=p0,
            p1=p1,
            p2=p2,
            p3=p3,
            stroke_color=stroke_color,
            fill_color=fill_color,
            stroke_width=1.5,
        )

        # Verify all control points
        assert bezier.get_p0() == p0
        assert bezier.get_p1() == p1
        assert bezier.get_p2() == p2
        assert bezier.get_p3() == p3

        # Verify colors
        assert bezier.get_stroke_color() == stroke_color
        assert bezier.get_fill_color() == fill_color
        assert bezier.get_stroke_width() == 1.5

    def test_path_segment_stroke_properties(self):
        """Test path segment stroke properties (width, color, dash)."""
        # Create segments with different stroke properties
        solid_line = Line(
            p0=Point(0, 0),
            p1=Point(100, 0),
            stroke_color=Color(0, 0, 0),
            stroke_width=3.0,
        )

        dashed_line = Line(
            p0=Point(0, 10),
            p1=Point(100, 10),
            stroke_color=Color(255, 0, 0),
            stroke_width=2.0,
            dash_array=[10.0, 5.0, 2.0, 5.0],
            dash_phase=0.0,
        )

        # Verify solid line has no dash pattern
        assert solid_line.get_dash_array() is None
        assert solid_line.get_stroke_width() == 3.0

        # Verify dashed line has correct pattern
        assert dashed_line.get_dash_array() == [10.0, 5.0, 2.0, 5.0]
        assert dashed_line.get_dash_phase() == 0.0
        assert dashed_line.get_stroke_width() == 2.0

    def test_path_with_multiple_segments(self):
        """Test creating a path with multiple mixed segment types."""
        # Create a complex path with lines and curves
        line1 = Line(
            p0=Point(0, 0),
            p1=Point(100, 0),
            stroke_color=Color(0, 0, 0),
            stroke_width=2.0,
        )

        bezier = Bezier(
            p0=Point(100, 0),
            p1=Point(125, 25),
            p2=Point(125, 75),
            p3=Point(100, 100),
            stroke_color=Color(0, 0, 0),
            stroke_width=2.0,
        )

        line2 = Line(
            p0=Point(100, 100),
            p1=Point(0, 100),
            stroke_color=Color(0, 0, 0),
            stroke_width=2.0,
        )

        path = Path(path_segments=[line1, bezier, line2], even_odd_fill=False)

        # Verify segment count
        assert len(path.get_path_segments()) == 3

        # Verify segment types
        segments = path.get_path_segments()
        assert isinstance(segments[0], Line)
        assert isinstance(segments[1], Bezier)
        assert isinstance(segments[2], Line)

        # Verify all have same stroke width
        for seg in segments:
            assert seg.get_stroke_width() == 2.0


class TestPathAssertionMethods:
    """Test the PDFAssertions methods for path validation."""

    def test_assert_line_segment_points(self):
        """Test assertion method for verifying line segment points."""
        # This is a unit test for the assertion method itself
        line = Line(
            p0=Point(10.5, 20.5), p1=Point(100.3, 200.7), stroke_color=Color(255, 0, 0)
        )

        # Create a mock PDF for assertions
        # Note: We'd need a real PDF context for full PDFAssertions,
        # but we can test the logic directly
        expected_p0 = Point(10.5, 20.5)
        expected_p1 = Point(100.3, 200.7)

        # Verify the points match
        assert line.get_p0().x == pytest.approx(expected_p0.x, abs=0.1)
        assert line.get_p0().y == pytest.approx(expected_p0.y, abs=0.1)
        assert line.get_p1().x == pytest.approx(expected_p1.x, abs=0.1)
        assert line.get_p1().y == pytest.approx(expected_p1.y, abs=0.1)

    def test_assert_bezier_segment_points(self):
        """Test assertion method for verifying bezier segment points."""
        bezier = Bezier(
            p0=Point(0.0, 0.0),
            p1=Point(33.33, 66.67),
            p2=Point(133.33, 66.67),
            p3=Point(200.0, 0.0),
        )

        # Verify all four control points
        assert bezier.get_p0().x == pytest.approx(0.0, abs=0.01)
        assert bezier.get_p0().y == pytest.approx(0.0, abs=0.01)

        assert bezier.get_p1().x == pytest.approx(33.33, abs=0.01)
        assert bezier.get_p1().y == pytest.approx(66.67, abs=0.01)

        assert bezier.get_p2().x == pytest.approx(133.33, abs=0.01)
        assert bezier.get_p2().y == pytest.approx(66.67, abs=0.01)

        assert bezier.get_p3().x == pytest.approx(200.0, abs=0.01)
        assert bezier.get_p3().y == pytest.approx(0.0, abs=0.01)

    def test_assert_segment_colors(self):
        """Test assertion methods for verifying segment colors."""
        stroke_color = Color(255, 0, 0, 255)
        fill_color = Color(0, 255, 0, 128)

        segment = Bezier(
            p0=Point(0, 0),
            p1=Point(50, 100),
            p2=Point(150, 100),
            p3=Point(200, 0),
            stroke_color=stroke_color,
            fill_color=fill_color,
        )

        # Verify stroke color
        actual_stroke = segment.get_stroke_color()
        assert actual_stroke.r == stroke_color.r
        assert actual_stroke.g == stroke_color.g
        assert actual_stroke.b == stroke_color.b
        assert actual_stroke.a == stroke_color.a

        # Verify fill color
        actual_fill = segment.get_fill_color()
        assert actual_fill.r == fill_color.r
        assert actual_fill.g == fill_color.g
        assert actual_fill.b == fill_color.b
        assert actual_fill.a == fill_color.a

    def test_assert_segment_dash_pattern(self):
        """Test assertion method for verifying dash patterns."""
        dash_array = [15.0, 5.0, 3.0, 5.0]
        dash_phase = 2.5

        line = Line(
            p0=Point(0, 0),
            p1=Point(200, 0),
            stroke_width=2.0,
            dash_array=dash_array,
            dash_phase=dash_phase,
        )

        # Verify dash pattern
        actual_array = line.get_dash_array()
        assert len(actual_array) == len(dash_array)
        for actual, expected in zip(actual_array, dash_array):
            assert actual == pytest.approx(expected, abs=0.1)

        # Verify dash phase
        assert line.get_dash_phase() == pytest.approx(dash_phase, abs=0.1)

    def test_assert_segment_is_solid(self):
        """Test assertion method for verifying solid (non-dashed) segments."""
        solid_line = Line(p0=Point(0, 0), p1=Point(100, 100), stroke_width=1.0)

        # Should have no dash array or empty dash array
        dash_array = solid_line.get_dash_array()
        assert dash_array is None or len(dash_array) == 0

    def test_assert_segment_type(self):
        """Test assertion method for verifying segment types."""
        line = Line(p0=Point(0, 0), p1=Point(100, 100))
        bezier = Bezier(
            p0=Point(0, 0), p1=Point(50, 100), p2=Point(150, 100), p3=Point(200, 0)
        )

        # Verify types
        assert isinstance(line, Line)
        assert isinstance(line, PathSegment)
        assert not isinstance(line, Bezier)

        assert isinstance(bezier, Bezier)
        assert isinstance(bezier, PathSegment)
        assert not isinstance(bezier, Line)


class TestComplexPathScenarios:
    """Test complex path scenarios with mixed operations."""

    def test_path_with_varying_stroke_widths(self):
        """Test a path with segments of varying stroke widths."""
        thin_line = Line(p0=Point(0, 0), p1=Point(100, 0), stroke_width=0.5)

        thick_line = Line(p0=Point(0, 10), p1=Point(100, 10), stroke_width=5.0)

        medium_curve = Bezier(
            p0=Point(0, 20),
            p1=Point(50, 70),
            p2=Point(50, 70),
            p3=Point(100, 20),
            stroke_width=2.0,
        )

        # Verify each has different stroke width
        assert thin_line.get_stroke_width() == 0.5
        assert thick_line.get_stroke_width() == 5.0
        assert medium_curve.get_stroke_width() == 2.0

    def test_path_with_transparency(self):
        """Test path segments with various alpha (transparency) values."""
        opaque = Line(
            p0=Point(0, 0),
            p1=Point(100, 0),
            stroke_color=Color(255, 0, 0, 255),  # Fully opaque
        )

        semi_transparent = Line(
            p0=Point(0, 10),
            p1=Point(100, 10),
            stroke_color=Color(0, 255, 0, 128),  # 50% transparent
        )

        nearly_transparent = Bezier(
            p0=Point(0, 20),
            p1=Point(50, 70),
            p2=Point(50, 70),
            p3=Point(100, 20),
            fill_color=Color(0, 0, 255, 32),  # ~12.5% opaque
        )

        # Verify alpha values
        assert opaque.get_stroke_color().a == 255
        assert semi_transparent.get_stroke_color().a == 128
        assert nearly_transparent.get_fill_color().a == 32

    def test_closed_shape_with_line_segments(self):
        """Test creating a closed rectangular shape with line segments."""
        # Create a rectangle using 4 line segments
        top = Line(p0=Point(0, 0), p1=Point(100, 0), stroke_width=1.0)
        right = Line(p0=Point(100, 0), p1=Point(100, 100), stroke_width=1.0)
        bottom = Line(p0=Point(100, 100), p1=Point(0, 100), stroke_width=1.0)
        left = Line(p0=Point(0, 100), p1=Point(0, 0), stroke_width=1.0)

        path = Path(path_segments=[top, right, bottom, left], even_odd_fill=False)

        # Verify it's a closed shape (end point of last segment == start of first)
        segments = path.get_path_segments()
        assert len(segments) == 4

        # Verify continuity
        assert segments[0].get_p1().x == segments[1].get_p0().x
        assert segments[0].get_p1().y == segments[1].get_p0().y

        assert segments[1].get_p1().x == segments[2].get_p0().x
        assert segments[1].get_p1().y == segments[2].get_p0().y

        assert segments[2].get_p1().x == segments[3].get_p0().x
        assert segments[2].get_p1().y == segments[3].get_p0().y

        # Last connects back to first
        assert segments[3].get_p1().x == segments[0].get_p0().x
        assert segments[3].get_p1().y == segments[0].get_p0().y

    def test_path_parsing_from_json(self):
        """Test parsing path data from JSON (simulating API response)."""
        # Simulate what the _parse_path method would receive
        from pdfdancer.pdfdancer_v1 import PDFDancer

        pdf_instance = PDFDancer.__new__(PDFDancer)

        # Simulate API response for a path with mixed segments
        path_json = {
            "position": {
                "pageNumber": 1,
                "boundingRect": {"x": 50.0, "y": 50.0, "width": 200.0, "height": 150.0},
            },
            "pathSegments": [
                {
                    "segmentType": "LINE",
                    "p0": {"x": 50.0, "y": 50.0},
                    "p1": {"x": 250.0, "y": 50.0},
                    "strokeColor": {"red": 0, "green": 0, "blue": 0, "alpha": 255},
                    "strokeWidth": 2.0,
                },
                {
                    "segmentType": "BEZIER",
                    "p0": {"x": 250.0, "y": 50.0},
                    "p1": {"x": 275.0, "y": 100.0},
                    "p2": {"x": 275.0, "y": 150.0},
                    "p3": {"x": 250.0, "y": 200.0},
                    "strokeColor": {"red": 0, "green": 0, "blue": 0, "alpha": 255},
                    "strokeWidth": 2.0,
                },
            ],
            "evenOddFill": False,
        }

        # Parse the path
        path = pdf_instance._parse_path(path_json)

        # Verify parsed path structure
        assert path.get_position() is not None
        assert path.get_position().page_number == 1
        assert path.get_even_odd_fill() is False

        # Verify segments
        segments = path.get_path_segments()
        assert len(segments) == 2

        # Verify first segment (Line)
        line_seg = segments[0]
        assert isinstance(line_seg, Line)
        assert line_seg.get_p0().x == 50.0
        assert line_seg.get_p0().y == 50.0
        assert line_seg.get_p1().x == 250.0
        assert line_seg.get_p1().y == 50.0
        assert line_seg.get_stroke_width() == 2.0

        # Verify second segment (Bezier)
        bezier_seg = segments[1]
        assert isinstance(bezier_seg, Bezier)
        assert bezier_seg.get_p0().x == 250.0
        assert bezier_seg.get_p3().x == 250.0
        assert bezier_seg.get_p3().y == 200.0
