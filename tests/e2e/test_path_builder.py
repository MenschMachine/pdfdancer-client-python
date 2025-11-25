"""
Comprehensive E2E tests for PathBuilder - testing the BUILDER pattern, not the parser.

These tests:
1. Start with a blank PDF
2. Build paths using PathBuilder (lines, beziers, complex paths)
3. Add them to the PDF
4. Save and reload the PDF
5. Make comprehensive assertions that the PDF contains exactly what we built
"""

import pytest

from pdfdancer import Color, Orientation, PageSize, PDFDancer, Point
from tests.e2e import _require_env
from tests.e2e.pdf_assertions import PDFAssertions


class TestPathBuilderSimplePaths:
    """Test building and adding simple paths (single line segments) to blank PDFs."""

    def test_add_simple_horizontal_line(self):
        """Build a simple horizontal line and add it to a blank PDF."""
        base_url, token = _require_env()

        # Start with a blank PDF
        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Build and add a horizontal line with absolute coordinates
        pdf.page(1).new_path().stroke_color(Color(255, 0, 0)).stroke_width(
            2.0
        ).add_line(Point(50, 100), Point(250, 150)).add()

        # Save and reload to verify persistence
        assertions = PDFAssertions(pdf)

        # Verify the path exists
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(50, 100, page=1, tolerance=5.0)

    def test_add_vertical_line_with_custom_width(self):
        """Build a vertical line with thick stroke."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Thick vertical line with absolute coordinates
        pdf.page(1).new_path().stroke_color(Color(0, 0, 255)).stroke_width(
            5.0
        ).add_line(Point(100, 50), Point(100, 300)).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(100, 50, page=1, tolerance=5.0)

    def test_add_diagonal_line_with_dash_pattern(self):
        """Build a dashed diagonal line."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Dashed diagonal line with absolute coordinates
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(
            1.5
        ).dash_pattern([10.0, 5.0]).add_line(Point(50, 50), Point(250, 250)).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(50, 50, page=1, tolerance=5.0)


class TestPathBuilderBezierCurves:
    """Test building and adding Bezier curves to blank PDFs."""

    def test_add_simple_bezier_curve(self):
        """Build a simple cubic Bezier curve."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Smooth S-curve using Bezier with absolute coordinates
        pdf.page(1).new_path().stroke_color(Color(0, 255, 0)).stroke_width(
            2.0
        ).add_bezier(
            Point(100, 300),  # Start
            Point(150, 400),  # Control 1
            Point(250, 400),  # Control 2
            Point(300, 300),  # End
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(100, 300, page=1, tolerance=5.0)

    def test_add_bezier_with_fill_color(self):
        """Build a Bezier curve with both stroke and fill."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Curve with fill (semi-transparent)
        pdf.page(1).new_path().stroke_color(Color(255, 0, 0, 255)).fill_color(
            Color(255, 255, 0, 128)
        ).stroke_width(1.0).add_bezier(
            Point(0, 0), Point(25, 50), Point(75, 50), Point(100, 0)
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(0, 0, page=1, tolerance=5.0)


class TestPathBuilderComplexPaths:
    """Test building complex paths with multiple segments."""

    def test_add_mixed_line_and_bezier_path(self):
        """Build a path with both line and Bezier segments."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Complex path: line → curve → line
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(2.0).add_line(
            Point(0, 0), Point(100, 0)
        ).add_bezier(
            Point(100, 0), Point(125, 25), Point(125, 75), Point(100, 100)
        ).add_line(
            Point(100, 100), Point(0, 100)
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(0, 0, page=1, tolerance=5.0)

    def test_add_closed_rectangle(self):
        """Build a closed rectangle using 4 line segments."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Rectangle (closed shape)
        pdf.page(1).new_path().stroke_color(Color(0, 0, 255)).stroke_width(
            2.0
        ).add_line(Point(0, 0), Point(150, 0)).add_line(
            Point(150, 0), Point(150, 100)
        ).add_line(
            Point(150, 100), Point(0, 100)
        ).add_line(
            Point(0, 100), Point(0, 0)
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(0, 0, page=1, tolerance=5.0)

    def test_add_rounded_rectangle(self):
        """Build a rounded rectangle using lines and Bezier curves for corners."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Rounded rectangle
        radius = 10.0
        width = 120.0
        height = 80.0

        pdf.page(1).new_path().stroke_color(Color(255, 0, 255)).stroke_width(
            2.0
        ).add_line(Point(radius, 0), Point(width - radius, 0)).add_bezier(
            Point(width - radius, 0),
            Point(width, 0),
            Point(width, 0),
            Point(width, radius),
        ).add_line(
            Point(width, radius), Point(width, height - radius)
        ).add_bezier(
            Point(width, height - radius),
            Point(width, height),
            Point(width, height),
            Point(width - radius, height),
        ).add_line(
            Point(width - radius, height), Point(radius, height)
        ).add_bezier(
            Point(radius, height),
            Point(0, height),
            Point(0, height),
            Point(0, height - radius),
        ).add_line(
            Point(0, height - radius), Point(0, radius)
        ).add_bezier(
            Point(0, radius), Point(0, 0), Point(0, 0), Point(radius, 0)
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(10, 0, page=1, tolerance=5.0)


class TestPathBuilderMultiplePaths:
    """Test adding multiple paths with different properties to the same PDF."""

    def test_add_multiple_paths_different_colors(self):
        """Add multiple paths with different stroke colors."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Red line
        pdf.page(1).new_path().stroke_color(Color(255, 0, 0)).stroke_width(
            2.0
        ).add_line(Point(0, 0), Point(100, 0)).add()

        # Green line
        pdf.page(1).new_path().stroke_color(Color(0, 255, 0)).stroke_width(
            2.0
        ).add_line(Point(0, 0), Point(100, 0)).add()

        # Blue line
        pdf.page(1).new_path().stroke_color(Color(0, 0, 255)).stroke_width(
            2.0
        ).add_line(Point(0, 0), Point(100, 0)).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(3, page=1)
        # All three lines start at (0, 0)
        assertions.assert_path_exists_at(0, 0, page=1, tolerance=5.0)

    def test_add_paths_with_varying_widths(self):
        """Add paths with different stroke widths."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Thin line (0.5pt)
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(0.5).add_line(
            Point(0, 0), Point(150, 0)
        ).add()

        # Medium line (2.0pt)
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(2.0).add_line(
            Point(0, 0), Point(150, 0)
        ).add()

        # Thick line (5.0pt)
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(5.0).add_line(
            Point(0, 0), Point(150, 0)
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(3, page=1)
        assertions.assert_path_exists_at(0, 0, page=1, tolerance=5.0)

    def test_add_solid_and_dashed_paths(self):
        """Add mix of solid and dashed paths."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Solid line
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(
            1.5
        ).solid().add_line(Point(0, 0), Point(200, 0)).add()

        # Dashed line (simple pattern)
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(
            1.5
        ).dash_pattern([10.0, 5.0]).add_line(Point(0, 0), Point(200, 0)).add()

        # Dashed line (complex pattern)
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(
            1.5
        ).dash_pattern([15.0, 5.0, 3.0, 5.0]).add_line(Point(0, 0), Point(200, 0)).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(3, page=1)
        assertions.assert_path_exists_at(0, 0, page=1, tolerance=5.0)


class TestPathBuilderPageSpecific:
    """Test using page-specific path builder."""

    def test_page_builder_sets_page_automatically(self):
        """Use page.new_path() to add path to specific page."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            initial_page_count=3,
            token=token,
            base_url=base_url,
        )

        # Add path to page 1 using page-specific builder
        pdf.page(2).new_path().stroke_color(Color(255, 0, 0)).stroke_width(
            2.0
        ).add_line(Point(0, 0), Point(100, 100)).add()

        assertions = PDFAssertions(pdf)
        # Page 1 should have no paths
        assertions.assert_number_of_paths(0, page=1)
        # Page 2 should have 1 path
        assertions.assert_number_of_paths(1, page=2)
        # Page 3 should have no paths
        assertions.assert_number_of_paths(0, page=3)


class TestPathBuilderValidation:
    """Test validation errors in PathBuilder."""

    def test_error_when_no_segments(self):
        """Adding a path with no segments should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Try to add empty path
        with pytest.raises(Exception) as exc_info:
            pdf.page(1).new_path().add()

        assert "at least one segment" in str(exc_info.value).lower()

    def test_error_when_invalid_stroke_width(self):
        """Setting negative stroke width should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Try to set negative stroke width
        with pytest.raises(Exception) as exc_info:
            pdf.page(1).new_path().stroke_width(-1.0).add_line(
                Point(0, 0), Point(100, 100)
            ).add()

        assert (
            "positive" in str(exc_info.value).lower()
            or "width" in str(exc_info.value).lower()
        )
