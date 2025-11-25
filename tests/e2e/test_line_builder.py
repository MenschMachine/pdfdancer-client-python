"""
End-to-end tests for LineBuilder.
Tests building lines from scratch and verifying the resulting PDF.
"""

from pdfdancer import Color, Orientation, PageSize, PDFDancer, Point
from tests.e2e import _require_env
from tests.e2e.pdf_assertions import PDFAssertions


class TestLineBuilderSimpleLines:
    """Test simple line creation with LineBuilder."""

    def test_horizontal_line(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        pdf.page(1).new_line().from_point(100, 200).to_point(300, 200).stroke_color(
            Color(255, 0, 0)
        ).stroke_width(2.0).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)

    def test_vertical_line(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        pdf.page(1).new_line().from_point(150, 100).to_point(150, 400).stroke_color(
            Color(0, 255, 0)
        ).stroke_width(3.0).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)

    def test_diagonal_line(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        pdf.page(1).new_line().from_point(50, 50).to_point(250, 250).stroke_color(
            Color(0, 0, 255)
        ).stroke_width(1.5).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)


class TestLineBuilderDashedLines:
    """Test dashed line patterns."""

    def test_dashed_line(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        pdf.page(1).new_line().from_point(100, 300).to_point(400, 300).stroke_color(
            Color(0, 0, 0)
        ).stroke_width(2.0).dash_pattern([10.0, 5.0], 0.0).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)

    def test_dotted_line(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        pdf.page(1).new_line().from_point(100, 350).to_point(400, 350).stroke_color(
            Color(128, 128, 128)
        ).stroke_width(1.0).dash_pattern([2.0, 3.0], 0.0).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)


class TestLineBuilderMultipleLines:
    """Test multiple lines on the same page."""

    def test_multiple_lines_same_page(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        # Red horizontal line
        pdf.page(1).new_line().from_point(50, 100).to_point(300, 100).stroke_color(
            Color(255, 0, 0)
        ).stroke_width(2.0).add()

        # Green vertical line
        pdf.page(1).new_line().from_point(150, 50).to_point(150, 200).stroke_color(
            Color(0, 255, 0)
        ).stroke_width(2.0).add()

        # Blue diagonal line
        pdf.page(1).new_line().from_point(50, 50).to_point(300, 200).stroke_color(
            Color(0, 0, 255)
        ).stroke_width(2.0).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(3, page=1)

        paths = pdf.page(1).select_paths()
        assert len(paths) == 3

    def test_rectangle_from_lines(self):
        """Create a rectangle using four separate lines."""
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        black = Color(0, 0, 0)
        width = 2.0

        # Top line
        pdf.page(1).new_line().from_point(100, 100).to_point(300, 100).stroke_color(
            black
        ).stroke_width(width).add()

        # Right line
        pdf.page(1).new_line().from_point(300, 100).to_point(300, 300).stroke_color(
            black
        ).stroke_width(width).add()

        # Bottom line
        pdf.page(1).new_line().from_point(300, 300).to_point(100, 300).stroke_color(
            black
        ).stroke_width(width).add()

        # Left line
        pdf.page(1).new_line().from_point(100, 300).to_point(100, 100).stroke_color(
            black
        ).stroke_width(width).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(4, page=1)


class TestLineBuilderMultiplePages:
    """Test lines on different pages."""

    def test_lines_on_different_pages(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            initial_page_count=3,
        )

        # Line on page 0
        pdf.page(1).new_line().from_point(100, 100).to_point(300, 100).stroke_color(
            Color(255, 0, 0)
        ).stroke_width(2.0).add()

        # Line on page 1
        pdf.page(2).new_line().from_point(100, 200).to_point(300, 200).stroke_color(
            Color(0, 255, 0)
        ).stroke_width(2.0).add()

        # Line on page 2
        pdf.page(3).new_line().from_point(100, 300).to_point(300, 300).stroke_color(
            Color(0, 0, 255)
        ).stroke_width(2.0).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_number_of_paths(1, page=2)


class TestLineBuilderValidation:
    """Test validation errors."""

    def test_missing_from_point(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        try:
            pdf.page(1).new_line().to_point(300, 200).stroke_color(
                Color(255, 0, 0)
            ).add()
            assert False, "Should have raised ValidationException"
        except Exception as e:
            assert "start point" in str(e).lower()

    def test_missing_to_point(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        try:
            pdf.page(1).new_line().from_point(100, 200).stroke_color(
                Color(255, 0, 0)
            ).add()
            assert False, "Should have raised ValidationException"
        except Exception as e:
            assert "end point" in str(e).lower()

    def test_invalid_stroke_width(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        try:
            pdf.page(1).new_line().from_point(100, 200).to_point(300, 200).stroke_width(
                0
            ).add()
            assert False, "Should have raised ValidationException"
        except Exception as e:
            assert "positive" in str(e).lower()
