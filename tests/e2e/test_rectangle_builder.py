"""
Comprehensive E2E tests for RectangleBuilder - testing new_rectangle() fluent builder.

These tests:
1. Start with a blank PDF
2. Build rectangles using PageClient.new_rectangle()
3. Add them to the PDF
4. Save and verify the PDF contains exactly what we built
"""

import pytest

from pdfdancer import Color, Orientation, PageSize, PDFDancer
from pdfdancer.exceptions import ValidationException
from tests.e2e import _require_env
from tests.e2e.pdf_assertions import PDFAssertions


class TestRectangleBuilderBasic:
    """Test basic rectangle creation with new_rectangle() builder."""

    def test_build_simple_rectangle(self):
        """Build a simple rectangle using fluent builder."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Use fluent builder to create rectangle
        pdf.page(1).new_rectangle().at_coordinates(50, 50).with_size(
            100, 80
        ).stroke_color(Color(0, 0, 0)).stroke_width(1.0).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(50, 50, page=1, tolerance=5.0)

    def test_build_rectangle_with_custom_colors(self):
        """Build a rectangle with custom stroke and fill colors."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Red stroke with yellow fill
        pdf.page(1).new_rectangle().at_coordinates(100, 100).with_size(
            150, 100
        ).stroke_color(Color(255, 0, 0)).fill_color(Color(255, 255, 0)).stroke_width(
            2.0
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(100, 100, page=1, tolerance=5.0)

    def test_build_rectangle_with_dash_pattern(self):
        """Build a dashed rectangle."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Dashed border
        pdf.page(1).new_rectangle().at_coordinates(75, 75).with_size(
            200, 150
        ).stroke_color(Color(0, 0, 0)).stroke_width(1.5).dash_pattern([10.0, 5.0]).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(75, 75, page=1, tolerance=5.0)

    def test_build_rectangle_with_solid(self):
        """Build a solid rectangle after setting dash pattern."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Set dash then override with solid
        pdf.page(1).new_rectangle().at_coordinates(50, 50).with_size(
            100, 80
        ).stroke_color(Color(0, 0, 255)).dash_pattern([5.0, 5.0]).solid().add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(50, 50, page=1, tolerance=5.0)


class TestRectangleBuilderSizes:
    """Test rectangles of different sizes."""

    def test_build_square(self):
        """Build a perfect square."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # 100x100 square
        pdf.page(1).new_rectangle().at_coordinates(100, 100).with_size(
            100, 100
        ).stroke_color(Color(0, 0, 0)).stroke_width(2.0).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(100, 100, page=1, tolerance=5.0)

    def test_build_wide_rectangle(self):
        """Build a wide horizontal rectangle."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Wide 300x50
        pdf.page(1).new_rectangle().at_coordinates(50, 400).with_size(
            300, 50
        ).stroke_color(Color(128, 128, 128)).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(50, 400, page=1, tolerance=5.0)

    def test_build_small_rectangle(self):
        """Build a very small rectangle."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Small 10x10
        pdf.page(1).new_rectangle().at_coordinates(300, 300).with_size(
            10, 10
        ).stroke_color(Color(255, 0, 255)).stroke_width(0.5).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(300, 300, page=1, tolerance=5.0)


class TestRectangleBuilderMultiple:
    """Test multiple rectangles."""

    def test_build_multiple_rectangles_same_page(self):
        """Build multiple rectangles on the same page."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Three rectangles
        pdf.page(1).new_rectangle().at_coordinates(50, 50).with_size(
            100, 80
        ).stroke_color(Color(255, 0, 0)).add()

        pdf.page(1).new_rectangle().at_coordinates(200, 50).with_size(
            100, 80
        ).stroke_color(Color(0, 255, 0)).add()

        pdf.page(1).new_rectangle().at_coordinates(350, 50).with_size(
            100, 80
        ).stroke_color(Color(0, 0, 255)).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(3, page=1)

    def test_build_nested_rectangles(self):
        """Build nested rectangles."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        # Outer
        pdf.page(1).new_rectangle().at_coordinates(100, 100).with_size(
            200, 150
        ).stroke_color(Color(0, 0, 0)).stroke_width(3.0).add()

        # Middle
        pdf.page(1).new_rectangle().at_coordinates(120, 120).with_size(
            160, 110
        ).stroke_color(Color(128, 128, 128)).stroke_width(2.0).add()

        # Inner
        pdf.page(1).new_rectangle().at_coordinates(140, 140).with_size(
            120, 70
        ).stroke_color(Color(255, 0, 0)).stroke_width(1.0).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(3, page=1)

    def test_build_rectangles_different_pages(self):
        """Build rectangles on different pages."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            initial_page_count=3,
            token=token,
            base_url=base_url,
        )

        # Page 0
        pdf.page(1).new_rectangle().at_coordinates(100, 100).with_size(
            150, 100
        ).stroke_color(Color(255, 0, 0)).add()

        # Page 1
        pdf.page(2).new_rectangle().at_coordinates(100, 100).with_size(
            150, 100
        ).stroke_color(Color(0, 255, 0)).add()

        # Page 2
        pdf.page(3).new_rectangle().at_coordinates(100, 100).with_size(
            150, 100
        ).stroke_color(Color(0, 0, 255)).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_number_of_paths(1, page=2)


class TestRectangleBuilderAdvanced:
    """Test advanced rectangle scenarios."""

    def test_build_rectangle_with_even_odd_fill(self):
        """Build a rectangle with even-odd fill rule."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        pdf.page(1).new_rectangle().at_coordinates(100, 100).with_size(
            200, 150
        ).stroke_color(Color(0, 0, 0)).fill_color(Color(255, 0, 0, 128)).even_odd_fill(
            True
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(100, 100, page=1, tolerance=5.0)

    def test_build_rectangle_at_origin(self):
        """Build a rectangle at origin (0,0)."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        pdf.page(1).new_rectangle().at_coordinates(0, 0).with_size(
            100, 80
        ).stroke_color(Color(0, 0, 0)).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(0, 0, page=1, tolerance=5.0)

    def test_build_rectangle_with_decimal_coordinates(self):
        """Build a rectangle with precise decimal coordinates."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        pdf.page(1).new_rectangle().at_coordinates(123.456, 234.567).with_size(
            111.222, 88.999
        ).stroke_color(Color(0, 0, 0)).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_path_exists_at(123.456, 234.567, page=1, tolerance=5.0)


class TestRectangleBuilderValidation:
    """Test validation errors for RectangleBuilder."""

    def test_error_when_position_not_set(self):
        """Building without setting position should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_rectangle().with_size(100, 80).add()

        assert (
            "position" in str(exc_info.value).lower()
            and "at_coordinates" in str(exc_info.value).lower()
        )

    def test_error_when_size_not_set(self):
        """Building without setting size should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_rectangle().at_coordinates(100, 100).add()

        assert (
            "dimensions" in str(exc_info.value).lower()
            and "with_size" in str(exc_info.value).lower()
        )

    def test_error_when_width_zero(self):
        """Building with zero width should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_rectangle().at_coordinates(100, 100).with_size(0, 100).add()

        assert "width must be positive" in str(exc_info.value).lower()

    def test_error_when_width_negative(self):
        """Building with negative width should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_rectangle().at_coordinates(100, 100).with_size(
                -50, 100
            ).add()

        assert "width must be positive" in str(exc_info.value).lower()

    def test_error_when_height_zero(self):
        """Building with zero height should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_rectangle().at_coordinates(100, 100).with_size(100, 0).add()

        assert "height must be positive" in str(exc_info.value).lower()

    def test_error_when_height_negative(self):
        """Building with negative height should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_rectangle().at_coordinates(100, 100).with_size(
                100, -80
            ).add()

        assert "height must be positive" in str(exc_info.value).lower()

    def test_error_when_stroke_width_negative(self):
        """Setting negative stroke width should fail."""
        base_url, token = _require_env()

        pdf = PDFDancer.new(
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            token=token,
            base_url=base_url,
        )

        with pytest.raises(ValidationException) as exc_info:
            pdf.page(1).new_rectangle().at_coordinates(100, 100).with_size(
                100, 80
            ).stroke_width(-1.0).add()

        assert "stroke width must be positive" in str(exc_info.value).lower()
