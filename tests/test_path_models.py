"""
Tests for Path, Line, Bezier, and PathSegment models.
"""

import pytest

from pdfdancer import Bezier, Color, Line, Path, PathSegment, Point, Position


class TestPoint:
    """Test Point model."""

    def test_point_creation(self):
        """Test creating a Point."""
        point = Point(100.0, 200.0)
        assert point.x == 100.0
        assert point.y == 200.0

    def test_point_with_negative_coords(self):
        """Test Point with negative coordinates."""
        point = Point(-50.0, -75.0)
        assert point.x == -50.0
        assert point.y == -75.0


class TestPathSegment:
    """Test PathSegment base class."""

    def test_path_segment_creation(self):
        """Test creating a PathSegment with all properties."""
        stroke_color = Color(255, 0, 0)
        fill_color = Color(0, 255, 0)

        segment = PathSegment(
            stroke_color=stroke_color,
            fill_color=fill_color,
            stroke_width=2.0,
            dash_array=[5.0, 3.0],
            dash_phase=1.0,
        )

        assert segment.get_stroke_color() == stroke_color
        assert segment.get_fill_color() == fill_color
        assert segment.get_stroke_width() == 2.0
        assert segment.get_dash_array() == [5.0, 3.0]
        assert segment.get_dash_phase() == 1.0

    def test_path_segment_defaults(self):
        """Test PathSegment with default values."""
        segment = PathSegment()

        assert segment.get_stroke_color() is None
        assert segment.get_fill_color() is None
        assert segment.get_stroke_width() is None
        assert segment.get_dash_array() is None
        assert segment.get_dash_phase() is None


class TestLine:
    """Test Line model."""

    def test_line_creation(self):
        """Test creating a Line segment."""
        p0 = Point(0.0, 0.0)
        p1 = Point(100.0, 100.0)
        stroke_color = Color(0, 0, 0)

        line = Line(p0=p0, p1=p1, stroke_color=stroke_color, stroke_width=1.0)

        assert line.get_p0() == p0
        assert line.get_p1() == p1
        assert line.get_stroke_color() == stroke_color
        assert line.get_stroke_width() == 1.0

    def test_line_defaults(self):
        """Test Line with default values."""
        line = Line()

        assert line.get_p0() is None
        assert line.get_p1() is None

    def test_line_with_dashed_stroke(self):
        """Test Line with dashed stroke pattern."""
        line = Line(
            p0=Point(0.0, 0.0),
            p1=Point(50.0, 50.0),
            stroke_width=2.0,
            dash_array=[10.0, 5.0, 2.0, 5.0],
            dash_phase=0.0,
        )

        assert line.get_dash_array() == [10.0, 5.0, 2.0, 5.0]
        assert line.get_dash_phase() == 0.0


class TestBezier:
    """Test Bezier model."""

    def test_bezier_creation(self):
        """Test creating a Bezier curve."""
        p0 = Point(0.0, 0.0)
        p1 = Point(50.0, 100.0)
        p2 = Point(150.0, 100.0)
        p3 = Point(200.0, 0.0)

        bezier = Bezier(
            p0=p0, p1=p1, p2=p2, p3=p3, stroke_color=Color(0, 0, 255), stroke_width=1.5
        )

        assert bezier.get_p0() == p0
        assert bezier.get_p1() == p1
        assert bezier.get_p2() == p2
        assert bezier.get_p3() == p3
        assert bezier.get_stroke_width() == 1.5

    def test_bezier_defaults(self):
        """Test Bezier with default values."""
        bezier = Bezier()

        assert bezier.get_p0() is None
        assert bezier.get_p1() is None
        assert bezier.get_p2() is None
        assert bezier.get_p3() is None

    def test_bezier_with_fill(self):
        """Test Bezier with both stroke and fill colors."""
        bezier = Bezier(
            p0=Point(0.0, 0.0),
            p1=Point(25.0, 50.0),
            p2=Point(75.0, 50.0),
            p3=Point(100.0, 0.0),
            stroke_color=Color(255, 0, 0),
            fill_color=Color(255, 255, 0, 128),
        )

        assert bezier.get_stroke_color().r == 255
        assert bezier.get_fill_color().r == 255
        assert bezier.get_fill_color().a == 128


class TestPath:
    """Test Path model."""

    def test_path_creation_with_segments(self):
        """Test creating a Path with multiple segments."""
        line = Line(p0=Point(0.0, 0.0), p1=Point(100.0, 0.0))
        bezier = Bezier(
            p0=Point(100.0, 0.0),
            p1=Point(150.0, 50.0),
            p2=Point(150.0, 100.0),
            p3=Point(100.0, 150.0),
        )

        path = Path(path_segments=[line, bezier], even_odd_fill=False)

        segments = path.get_path_segments()
        assert segments is not None
        assert len(segments) == 2
        assert isinstance(segments[0], Line)
        assert isinstance(segments[1], Bezier)
        assert path.get_even_odd_fill() is False

    def test_path_with_position(self):
        """Test Path with position information."""
        position = Position.at_page_coordinates(1, 50.0, 50.0)
        line = Line(p0=Point(0.0, 0.0), p1=Point(50.0, 50.0))

        path = Path(position=position, path_segments=[line])

        assert path.get_position() == position
        assert path.get_position().page_number == 1

    def test_path_defaults(self):
        """Test Path with default values."""
        path = Path()

        assert path.get_position() is None
        assert path.get_path_segments() is None
        assert path.get_even_odd_fill() is None

    def test_path_even_odd_fill(self):
        """Test Path with even-odd fill rule."""
        line1 = Line(p0=Point(0.0, 0.0), p1=Point(100.0, 0.0))
        line2 = Line(p0=Point(100.0, 0.0), p1=Point(100.0, 100.0))
        line3 = Line(p0=Point(100.0, 100.0), p1=Point(0.0, 100.0))
        line4 = Line(p0=Point(0.0, 100.0), p1=Point(0.0, 0.0))

        path = Path(path_segments=[line1, line2, line3, line4], even_odd_fill=True)

        assert path.get_even_odd_fill() is True
        assert len(path.get_path_segments()) == 4

    def test_path_set_position(self):
        """Test setting position on a Path."""
        path = Path()
        position = Position.at_page_coordinates(1, 100.0, 200.0)

        path.set_position(position)

        assert path.get_position() == position
        assert path.get_position().page_number == 1


class TestPathIntegration:
    """Integration tests for path models."""

    def test_complex_path_with_mixed_segments(self):
        """Test complex path with both lines and bezier curves."""
        segments = [
            Line(
                p0=Point(0.0, 0.0),
                p1=Point(100.0, 0.0),
                stroke_color=Color(0, 0, 0),
                stroke_width=2.0,
            ),
            Bezier(
                p0=Point(100.0, 0.0),
                p1=Point(125.0, 25.0),
                p2=Point(125.0, 75.0),
                p3=Point(100.0, 100.0),
                stroke_color=Color(0, 0, 0),
                stroke_width=2.0,
            ),
            Line(
                p0=Point(100.0, 100.0),
                p1=Point(0.0, 100.0),
                stroke_color=Color(0, 0, 0),
                stroke_width=2.0,
            ),
        ]

        path = Path(
            path_segments=segments, position=Position.at_page(1), even_odd_fill=False
        )

        assert len(path.get_path_segments()) == 3
        assert all(seg.get_stroke_width() == 2.0 for seg in path.get_path_segments())

    def test_path_with_dashed_segments(self):
        """Test path with dashed line segments."""
        dash_pattern = [10.0, 5.0]

        line = Line(
            p0=Point(0.0, 0.0),
            p1=Point(200.0, 200.0),
            stroke_color=Color(255, 0, 0),
            stroke_width=1.0,
            dash_array=dash_pattern,
            dash_phase=0.0,
        )

        path = Path(path_segments=[line])

        segment = path.get_path_segments()[0]
        assert segment.get_dash_array() == dash_pattern
        assert segment.get_dash_phase() == 0.0
