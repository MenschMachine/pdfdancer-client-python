"""
Comprehensive E2E tests for PathBuilder.add_rectangle() method.

These tests:
1. Start with a blank PDF
2. Build rectangles using PathBuilder.add_rectangle()
3. Add them to the PDF
4. Save and verify the PDF contains exactly what we built
"""

import pytest

from pdfdancer import Color, Orientation, PageSize, PDFDancer
from pdfdancer.exceptions import ValidationException
from tests.e2e import _require_env
from tests.e2e.pdf_assertions import PDFAssertions


class TestPathBuilderRectangleBasic:
    """Test basic rectangle creation with add_rectangle()."""

    def test_add_simple_rectangle(self):
        """Build a simple rectangle with default stroke."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Add a 100x80 rectangle at (50, 50)
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(
            1.0
        ).add_rectangle(50, 50, 100, 80).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(50, 50, page=1, tolerance=5.0)

    def test_add_rectangle_with_custom_stroke(self):
        """Build a rectangle with custom stroke color and width."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Red rectangle with thick stroke
        pdf.page(1).new_path().stroke_color(Color(255, 0, 0)).stroke_width(
            3.0
        ).add_rectangle(100, 100, 150, 100).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(100, 100, page=1, tolerance=5.0)

    def test_add_rectangle_with_fill(self):
        """Build a rectangle with both stroke and fill color."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Blue stroke, yellow fill
        pdf.page(1).new_path().stroke_color(Color(0, 0, 255)).fill_color(
            Color(255, 255, 0)
        ).stroke_width(2.0).add_rectangle(200, 200, 120, 90).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(200, 200, page=1, tolerance=5.0)

    def test_add_rectangle_with_dash_pattern(self):
        """Build a dashed rectangle."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Dashed border rectangle
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(
            1.5
        ).dash_pattern([10.0, 5.0]).add_rectangle(75, 75, 200, 150).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(75, 75, page=1, tolerance=5.0)


class TestPathBuilderRectangleSizes:
    """Test rectangles of different sizes and aspect ratios."""

    def test_add_square(self):
        """Build a perfect square using add_rectangle()."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # 100x100 square
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(
            2.0
        ).add_rectangle(100, 100, 100, 100).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(100, 100, page=1, tolerance=5.0)

    def test_add_wide_rectangle(self):
        """Build a wide horizontal rectangle."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Wide rectangle 300x50
        pdf.page(1).new_path().stroke_color(Color(128, 128, 128)).stroke_width(
            1.0
        ).add_rectangle(50, 400, 300, 50).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(50, 400, page=1, tolerance=5.0)

    def test_add_tall_rectangle(self):
        """Build a tall vertical rectangle."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Tall rectangle 50x300
        pdf.page(1).new_path().stroke_color(Color(64, 64, 64)).stroke_width(
            1.0
        ).add_rectangle(400, 50, 50, 300).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(400, 50, page=1, tolerance=5.0)

    def test_add_small_rectangle(self):
        """Build a very small rectangle."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Small 10x10 rectangle
        pdf.page(1).new_path().stroke_color(Color(255, 0, 255)).stroke_width(
            0.5
        ).add_rectangle(300, 300, 10, 10).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(300, 300, page=1, tolerance=5.0)

    def test_add_large_rectangle(self):
        """Build a large rectangle covering most of the page."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Large rectangle (almost full page A4 is ~595x842 pts)
        pdf.page(1).new_path().stroke_color(Color(0, 128, 0)).stroke_width(
            2.0
        ).add_rectangle(20, 20, 550, 800).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(20, 20, page=1, tolerance=5.0)


class TestPathBuilderRectangleMultiple:
    """Test multiple rectangles in the same PDF."""

    def test_add_multiple_rectangles_same_page(self):
        """Add multiple rectangles to the same page."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Rectangle 1
        pdf.page(1).new_path().stroke_color(Color(255, 0, 0)).stroke_width(
            1.0
        ).add_rectangle(50, 50, 100, 80).add()

        # Rectangle 2
        pdf.page(1).new_path().stroke_color(Color(0, 255, 0)).stroke_width(
            1.0
        ).add_rectangle(200, 50, 100, 80).add()

        # Rectangle 3
        pdf.page(1).new_path().stroke_color(Color(0, 0, 255)).stroke_width(
            1.0
        ).add_rectangle(350, 50, 100, 80).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(3, page=1)
        assertions.assert_path_exists_at(50, 50, page=1, tolerance=5.0)

    def test_add_nested_rectangles(self):
        """Add nested rectangles (one inside another)."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Outer rectangle
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(
            3.0
        ).add_rectangle(100, 100, 200, 150).add()

        # Middle rectangle
        pdf.page(1).new_path().stroke_color(Color(128, 128, 128)).stroke_width(
            2.0
        ).add_rectangle(120, 120, 160, 110).add()

        # Inner rectangle
        pdf.page(1).new_path().stroke_color(Color(255, 0, 0)).stroke_width(
            1.0
        ).add_rectangle(140, 140, 120, 70).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(3, page=1)
        assertions.assert_path_exists_at(100, 100, page=1, tolerance=5.0)

    def test_add_rectangles_different_pages(self):
        """Add rectangles to different pages."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            initial_page_count=3,
            token=token,
            base_url=base_url,
        )

        # Rectangle on page 0
        pdf.page(1).new_path().stroke_color(Color(255, 0, 0)).stroke_width(
            2.0
        ).add_rectangle(100, 100, 150, 100).add()

        # Rectangle on page 1
        pdf.page(2).new_path().stroke_color(Color(0, 255, 0)).stroke_width(
            2.0
        ).add_rectangle(100, 100, 150, 100).add()

        # Rectangle on page 2
        pdf.page(3).new_path().stroke_color(Color(0, 0, 255)).stroke_width(
            2.0
        ).add_rectangle(100, 100, 150, 100).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_number_of_paths(1, page=2)


class TestPathBuilderRectangleAdvanced:
    """Test advanced rectangle scenarios."""

    def test_add_rectangle_in_complex_path(self):
        """Add a rectangle as part of a complex path with other segments."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Complex path: rectangle + line
        from pdfdancer import Point

        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(
            2.0
        ).add_rectangle(100, 100, 150, 100).add_line(
            Point(250, 150), Point(350, 200)
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(100, 100, page=1, tolerance=5.0)

    def test_add_rectangle_with_changing_stroke_properties(self):
        """Add separate rectangle paths with different stroke properties."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Three separate paths, each with its own rectangle and properties
        pdf.page(1).new_path().stroke_color(Color(255, 0, 0)).stroke_width(
            1.0
        ).add_rectangle(50, 50, 80, 60).add()

        pdf.page(1).new_path().stroke_color(Color(0, 255, 0)).stroke_width(
            2.0
        ).add_rectangle(150, 50, 80, 60).add()

        pdf.page(1).new_path().stroke_color(Color(0, 0, 255)).stroke_width(
            3.0
        ).add_rectangle(250, 50, 80, 60).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(3, page=1)
        assertions.assert_path_exists_at(50, 50, page=1, tolerance=5.0)

    def test_add_rectangle_with_even_odd_fill(self):
        """Add overlapping filled rectangles with even-odd fill rule."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Overlapping rectangles with even-odd fill
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).fill_color(
            Color(255, 0, 0, 128)
        ).stroke_width(1.0).even_odd_fill(True).add_rectangle(
            100, 100, 200, 150
        ).add_rectangle(
            150, 125, 200, 150
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(100, 100, page=1, tolerance=5.0)

    def test_add_rectangle_at_origin(self):
        """Add a rectangle at the origin (0,0)."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Rectangle at origin
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(
            2.0
        ).add_rectangle(0, 0, 100, 80).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(0, 0, page=1, tolerance=5.0)

    def test_add_rectangle_with_decimal_coordinates(self):
        """Add a rectangle with precise decimal coordinates."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Rectangle with decimal coordinates
        pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).stroke_width(
            1.0
        ).add_rectangle(123.456, 234.567, 111.222, 88.999).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(123.456, 234.567, page=1, tolerance=5.0)


class TestPathBuilderRectangleValidation:
    """Test validation errors for add_rectangle()."""

    def test_error_when_width_zero(self):
        """Adding a rectangle with zero width should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).add_rectangle(
                100, 100, 0, 100
            ).add()

        assert "width must be positive" in str(exc_info.value).lower()

    def test_error_when_width_negative(self):
        """Adding a rectangle with negative width should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).add_rectangle(
                100, 100, -50, 100
            ).add()

        assert "width must be positive" in str(exc_info.value).lower()

    def test_error_when_height_zero(self):
        """Adding a rectangle with zero height should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).add_rectangle(
                100, 100, 100, 0
            ).add()

        assert "height must be positive" in str(exc_info.value).lower()

    def test_error_when_height_negative(self):
        """Adding a rectangle with negative height should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).add_rectangle(
                100, 100, 100, -80
            ).add()

        assert "height must be positive" in str(exc_info.value).lower()

    def test_error_when_both_dimensions_invalid(self):
        """Adding a rectangle with both invalid dimensions should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_path().stroke_color(Color(0, 0, 0)).add_rectangle(
                100, 100, -50, -80
            ).add()

        # Should fail on width check first
        assert "width must be positive" in str(exc_info.value).lower()
