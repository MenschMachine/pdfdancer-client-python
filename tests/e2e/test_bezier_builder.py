"""
End-to-end tests for BezierBuilder.
Tests building bezier curves from scratch and verifying the resulting PDF.
"""

from pdfdancer import Color, Orientation, PageSize, PDFDancer, Point
from tests.e2e import _require_env
from tests.e2e.pdf_assertions import PDFAssertions


class TestBezierBuilderSimpleCurves:
    """Test simple bezier curve creation."""

    def test_simple_bezier_curve(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        pdf.page(1).new_bezier().from_point(100, 200).control_point_1(
            150, 100
        ).control_point_2(250, 100).to_point(300, 200).stroke_color(
            Color(255, 0, 0)
        ).stroke_width(
            2.0
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)

    def test_s_curve(self):
        """Test an S-shaped bezier curve."""
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        pdf.page(1).new_bezier().from_point(100, 300).control_point_1(
            200, 100
        ).control_point_2(300, 500).to_point(400, 300).stroke_color(
            Color(0, 0, 255)
        ).stroke_width(
            3.0
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)


class TestBezierBuilderFillColors:
    """Test bezier curves with fill colors."""

    def test_bezier_with_fill(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        pdf.page(1).new_bezier().from_point(100, 200).control_point_1(
            150, 100
        ).control_point_2(250, 100).to_point(300, 200).stroke_color(
            Color(0, 0, 0)
        ).fill_color(
            Color(255, 200, 200)
        ).stroke_width(
            2.0
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)


class TestBezierBuilderDashedCurves:
    """Test dashed bezier curves."""

    def test_dashed_bezier(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        pdf.page(1).new_bezier().from_point(100, 300).control_point_1(
            200, 200
        ).control_point_2(300, 400).to_point(400, 300).stroke_color(
            Color(128, 128, 128)
        ).stroke_width(
            2.0
        ).dash_pattern(
            [10.0, 5.0], 0.0
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)


class TestBezierBuilderMultipleCurves:
    """Test multiple bezier curves."""

    def test_multiple_bezier_curves(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        # First curve - red
        pdf.page(1).new_bezier().from_point(50, 200).control_point_1(
            100, 100
        ).control_point_2(200, 100).to_point(250, 200).stroke_color(
            Color(255, 0, 0)
        ).stroke_width(
            2.0
        ).add()

        # Second curve - green
        pdf.page(1).new_bezier().from_point(50, 300).control_point_1(
            100, 400
        ).control_point_2(200, 400).to_point(250, 300).stroke_color(
            Color(0, 255, 0)
        ).stroke_width(
            2.0
        ).add()

        # Third curve - blue
        pdf.page(1).new_bezier().from_point(50, 400).control_point_1(
            100, 500
        ).control_point_2(200, 300).to_point(250, 400).stroke_color(
            Color(0, 0, 255)
        ).stroke_width(
            2.0
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(3, page=1)


class TestBezierBuilderMultiplePages:
    """Test bezier curves on different pages."""

    def test_curves_on_different_pages(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
            initial_page_count=3,
        )

        # Curve on page 0
        pdf.page(1).new_bezier().from_point(100, 200).control_point_1(
            150, 100
        ).control_point_2(250, 100).to_point(300, 200).stroke_color(
            Color(255, 0, 0)
        ).stroke_width(
            2.0
        ).add()

        # Curve on page 1
        pdf.page(2).new_bezier().from_point(100, 300).control_point_1(
            150, 200
        ).control_point_2(250, 200).to_point(300, 300).stroke_color(
            Color(0, 255, 0)
        ).stroke_width(
            2.0
        ).add()

        # Curve on page 2
        pdf.page(3).new_bezier().from_point(100, 400).control_point_1(
            150, 300
        ).control_point_2(250, 300).to_point(300, 400).stroke_color(
            Color(0, 0, 255)
        ).stroke_width(
            2.0
        ).add()

        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_number_of_paths(1, page=1)
        assertions.assert_number_of_paths(1, page=2)


class TestBezierBuilderValidation:
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
            pdf.page(1).new_bezier().control_point_1(150, 100).control_point_2(
                250, 100
            ).to_point(300, 200).add()
            assert False, "Should have raised ValidationException"
        except Exception as e:
            assert "start point" in str(e).lower()

    def test_missing_control_point_1(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        try:
            pdf.page(1).new_bezier().from_point(100, 200).control_point_2(
                250, 100
            ).to_point(300, 200).add()
            assert False, "Should have raised ValidationException"
        except Exception as e:
            assert "first control point" in str(e).lower()

    def test_missing_control_point_2(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        try:
            pdf.page(1).new_bezier().from_point(100, 200).control_point_1(
                150, 100
            ).to_point(300, 200).add()
            assert False, "Should have raised ValidationException"
        except Exception as e:
            assert "second control point" in str(e).lower()

    def test_missing_to_point(self):
        base_url, token = _require_env()
        pdf = PDFDancer.new(
            token=token,
            base_url=base_url,
            page_size=PageSize.A4,
            orientation=Orientation.PORTRAIT,
        )

        try:
            pdf.page(1).new_bezier().from_point(100, 200).control_point_1(
                150, 100
            ).control_point_2(250, 100).add()
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
            pdf.page(1).new_bezier().from_point(100, 200).control_point_1(
                150, 100
            ).control_point_2(250, 100).to_point(300, 200).stroke_width(-1).add()
            assert False, "Should have raised ValidationException"
        except Exception as e:
            assert "positive" in str(e).lower()
