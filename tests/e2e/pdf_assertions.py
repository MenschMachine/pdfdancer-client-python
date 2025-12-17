import tempfile
from typing import List, Optional

import pytest

from pdfdancer import Bezier, Color, Line, Orientation, PathSegment, PDFDancer, Point


class PDFAssertions(object):

    # noinspection PyProtectedMember
    def __init__(self, pdf_dancer: PDFDancer):
        token = pdf_dancer._token
        base_url = pdf_dancer._base_url
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf", mode="w+t"
        ) as temp_file:
            pdf_dancer.save(temp_file.name)
            print(f"Saving PDF file to {temp_file.name}")
        self.pdf = PDFDancer.open(temp_file.name, token=token, base_url=base_url)

    def assert_text_has_color(self, text, color: Color, page=1):
        self.assert_textline_has_color(text, color, page)

        paragraphs = self.pdf.page(page).select_paragraphs_matching(text)
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()
        assert text in reference.get_text()
        assert color == reference.get_color(), f"{color} != {reference.get_color()}"
        return self

    def assert_text_has_font(self, text, font_name, font_size, page=1):
        self.assert_textline_has_font(text, font_name, font_size, page)

        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()
        assert (
            font_name == reference.get_font_name()
        ), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()

        return self

    def assert_paragraph_is_at(
        self, text, x, y, page=1, epsilon=2
    ):  # adjust for baseline vs bounding box differences
        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()

        assert reference.get_position().x() == pytest.approx(
            x, rel=epsilon, abs=epsilon
        ), f"{x} != {reference.get_position().x()}"
        assert reference.get_position().y() == pytest.approx(
            y, rel=epsilon, abs=epsilon
        ), f"{y} != {reference.get_position().y()}"

        paragraph_by_position = self.pdf.page(page).select_paragraphs_at(x, y)
        assert paragraphs[0] == paragraph_by_position[0]
        return self

    def assert_text_has_font_matching(self, text, font_name, font_size, page=1):
        self.assert_textline_has_font_matching(text, font_name, font_size, page)

        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()
        assert (
            font_name in reference.get_font_name()
        ), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()
        return self

    def assert_textline_has_color(self, text: str, color: Color, page=1):
        lines = self.pdf.page(page).select_text_lines_matching(text)
        assert len(lines) == 1, f"Expected 1 line but got {len(lines)}"
        reference = lines[0].object_ref()
        assert color == reference.get_color(), f"{color} != {reference.get_color()}"
        assert text in reference.get_text()
        return self

    def assert_textline_has_font(
        self, text: str, font_name: str, font_size: int, page=1
    ):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1, f"Expected 1 line but got {len(lines)}"
        reference = lines[0].object_ref()
        assert (
            font_name == reference.get_font_name()
        ), f"Expected {font_name} but got {reference.get_font_name()}"
        assert (
            font_size == reference.get_font_size()
        ), f"{font_size} != {reference.get_font_size()}"
        return self

    def assert_textline_has_font_matching(
        self, text, font_name: str, font_size: int, page=1
    ):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1, f"Expected 1 line but got {len(lines)}"
        reference = lines[0].object_ref()
        assert (
            font_name in reference.get_font_name()
        ), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()
        return self

    def assert_textline_is_at(
        self, text: str, x: float, y: float, page=1, epsilon=1e-6
    ):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1
        reference = lines[0].object_ref()
        assert reference.get_position().x() == pytest.approx(
            x, rel=epsilon, abs=epsilon
        ), f"{x} != {reference.get_position().x()}"
        assert reference.get_position().y() == pytest.approx(
            y, rel=epsilon, abs=epsilon
        ), f"{y} != {reference.get_position().y()}"

        by_position = self.pdf.page(page).select_text_lines_at(x, y)
        assert lines[0] == by_position[0]
        return self

    def assert_textline_does_not_exist(self, text, page=1):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 0
        return self

    def assert_textline_exists(self, text, page=1):
        lines = self.pdf.page(page).select_text_lines_matching(f".*{text}.*")
        assert len(lines) == 1
        return self

    def assert_paragraph_exists(self, text, page=1):
        lines = self.pdf.page(page).select_paragraphs_starting_with(text)
        assert (
            len(lines) == 1
        ), f"No paragraphs starting with {text} found on page {page}"
        return self

    def assert_number_of_pages(self, page_count: int):
        assert (
            len(self.pdf.pages()) == page_count
        ), f"Expected {page_count} pages, but got {len(self.pdf.pages())}"
        return self

    def assert_path_is_at(
        self, internal_id: str, x: float, y: float, page=1, epsilon=1e-6
    ):
        paths = self.pdf.page(page).select_paths_at(x, y)
        assert len(paths) == 1
        reference = paths[0].object_ref()
        assert (
            reference.internal_id == internal_id
        ), f"{internal_id} != {reference.internal_id}"
        assert reference.get_position().x() == pytest.approx(
            x, rel=epsilon, abs=epsilon
        ), f"{x} != {reference.get_position().x()}"
        assert reference.get_position().y() == pytest.approx(
            y, rel=epsilon, abs=epsilon
        ), f"{y} != {reference.get_position().y()}"

        return self

    def assert_no_path_at(self, x: float, y: float, page=1):
        paths = self.pdf.page(page).select_paths_at(x, y)
        assert len(paths) == 0
        return self

    def assert_number_of_paths(self, path_count: int, page=1):
        paths = self.pdf.page(page).select_paths()
        assert (
            len(paths) == path_count
        ), f"Expected {path_count} paths, but got {len(paths)}"
        return self

    def assert_number_of_images(self, image_count, page=1):
        images = self.pdf.page(page).select_images()
        assert (
            len(images) == image_count
        ), f"Expected {image_count} image but got {len(images)}"
        return self

    def assert_image_at(self, x: float, y: float, page=1):
        images = self.pdf.page(page).select_images_at(x, y)
        all_images = self.pdf.page(page).select_images()
        assert (
            len(images) == 1
        ), f"Expected 1 image but got {len(images)}, total images: {len(all_images)}, first pos: {all_images[0].position}"
        return self

    def assert_no_image_at(self, x: float, y: float, page=1) -> "PDFAssertions":
        images = self.pdf.page(page).select_images_at(x, y)
        assert (
            len(images) == 0
        ), f"Expected 0 image at {x}/{y} but got {len(images)}, {images[0].internal_id}"
        return self

    def assert_image_with_id_at(
        self, internal_id: str, x: float, y: float, page=1
    ) -> "PDFAssertions":
        images = self.pdf.page(page).select_images_at(x, y)
        assert len(images) == 1, f"Expected 1 image but got {len(images)}"
        assert (
            images[0].internal_id == internal_id
        ), f"{internal_id} != {images[0].internal_id}"
        return self

    def assert_total_number_of_elements(
        self, nr_of_elements, page_number=None
    ) -> "PDFAssertions":
        total = 0
        if page_number is None:
            for page in self.pdf.pages():
                total = total + len(page.select_elements())
        else:
            total = len(self.pdf.page(page_number).select_elements())
        assert (
            total == nr_of_elements
        ), f"Total number of elements differ, actual {total} != expected {nr_of_elements}"
        return self

    def assert_page_count(self, page_count: int) -> "PDFAssertions":
        assert page_count == len(self.pdf.pages())
        return self

    def assert_page_dimension(
        self,
        width: float,
        height: float,
        orientation: Optional[Orientation] = None,
        page_number=1,
    ) -> "PDFAssertions":
        page = self.pdf.page(page_number)
        assert width == page.size.width, f"{width} != {page.size.width}"
        assert height == page.size.height, f"{height} != {page.size.height}"
        if orientation is not None:
            actual_orientation = page.orientation
            if isinstance(actual_orientation, str):
                try:
                    actual_orientation = Orientation(actual_orientation.strip().upper())
                except ValueError:
                    pass
            assert (
                orientation == actual_orientation
            ), f"{orientation} != {actual_orientation}"
        return self

    def assert_number_of_formxobjects(
        self, nr_of_formxobjects, page_number=1
    ) -> "PDFAssertions":
        assert nr_of_formxobjects == len(
            self.pdf.page(page_number).select_forms()
        ), f"Expected nr of formxobjects {nr_of_formxobjects} but got {len(self.pdf.page(page_number).select_forms())}"
        return self

    def assert_number_of_form_fields(
        self, nr_of_form_fields, page_number=1
    ) -> "PDFAssertions":
        assert nr_of_form_fields == len(
            self.pdf.page(page_number).select_form_fields()
        ), f"Expected nr of form fields {nr_of_form_fields} but got {len(self.pdf.page(page_number).select_form_fields())}"
        return self

    def assert_form_field_at(self, x: float, y: float, page=1) -> "PDFAssertions":
        form_fields = self.pdf.page(page).select_form_fields_at(x, y, 1)
        all_form_fields = self.pdf.page(page).select_form_fields()
        assert (
            len(form_fields) == 1
        ), f"Expected 1 form field but got {len(form_fields)}, total form_fields: {len(all_form_fields)}, first pos: {all_form_fields[0].position}"
        return self

    def assert_form_field_not_at(self, x: float, y: float, page=1) -> "PDFAssertions":
        form_fields = self.pdf.page(page).select_form_fields_at(x, y, 1)
        assert (
            len(form_fields) == 0
        ), f"Expected 0 form fields at {x}/{y} but got {len(form_fields)}, {form_fields[0].internal_id}"
        return self

    def assert_form_field_exists(
        self, field_name: str, page_number=1
    ) -> "PDFAssertions":
        form_fields = self.pdf.page(page_number).select_form_fields_by_name(field_name)
        assert (
            len(form_fields) == 1
        ), f"Expected 1 form field but got {len(form_fields)}"
        return self

    def assert_form_field_has_value(
        self, field_name: str, field_value: str, page_number=1
    ) -> "PDFAssertions":
        form_fields = self.pdf.page(page_number).select_form_fields_by_name(field_name)
        assert (
            len(form_fields) == 1
        ), f"Expected 1 form field but got {len(form_fields)}"
        assert (
            form_fields[0].value == field_value
        ), f"{form_fields[0].value} != {field_value}"
        return self

    # ========================================
    # Path-specific assertions
    # ========================================

    def assert_path_exists_at(
        self, x: float, y: float, page=1, tolerance: float = 5.0
    ) -> "PDFAssertions":
        """Assert that at least one path exists at the specified coordinates."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert (
            len(paths) > 0
        ), f"Expected at least 1 path at ({x}, {y}) on page {page}, but found none"
        return self

    def assert_path_count_at(
        self, count: int, x: float, y: float, page=1, tolerance: float = 5.0
    ) -> "PDFAssertions":
        """Assert exact number of paths at the specified coordinates."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert (
            len(paths) == count
        ), f"Expected {count} paths at ({x}, {y}) but got {len(paths)}"
        return self

    def assert_path_has_id(
        self, internal_id: str, x: float, y: float, page=1, tolerance: float = 5.0
    ) -> "PDFAssertions":
        """Assert that a path with specific ID exists at the coordinates."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        path_ids = [p.internal_id for p in paths]
        assert (
            internal_id in path_ids
        ), f"Expected path {internal_id} at ({x}, {y}), but found: {path_ids}"
        return self

    def assert_path_bounding_box(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        page=1,
        tolerance: float = 5.0,
        epsilon: float = 1.0,
    ) -> "PDFAssertions":
        """Assert that a path at the coordinates has the specified bounding box."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert len(paths) > 0, f"No paths found at ({x}, {y})"

        path = paths[0]
        bbox = path.position.bounding_rect
        assert bbox is not None, f"Path {path.internal_id} has no bounding rect"

        assert bbox.x == pytest.approx(
            x, abs=epsilon
        ), f"Bounding box x {bbox.x} != {x}"
        assert bbox.y == pytest.approx(
            y, abs=epsilon
        ), f"Bounding box y {bbox.y} != {y}"
        assert bbox.width == pytest.approx(
            width, abs=epsilon
        ), f"Bounding box width {bbox.width} != {width}"
        assert bbox.height == pytest.approx(
            height, abs=epsilon
        ), f"Bounding box height {bbox.height} != {height}"
        return self

    def get_path_at(self, x: float, y: float, page=1, tolerance: float = 5.0):
        """Helper to get the first path at coordinates for detailed inspection."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert len(paths) > 0, f"No paths found at ({x}, {y})"
        return paths[0]

    def assert_path_segment_count(
        self, expected_count: int, x: float, y: float, page=1, tolerance: float = 5.0
    ) -> "PDFAssertions":
        """Assert the number of segments in a path at the specified coordinates.

        Note: This requires the path to have detailed segment information loaded.
        """
        # This would work if the path object has path_segments loaded
        # For now, we'll document that this needs API support
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert len(paths) > 0, f"No paths found at ({x}, {y})"

        path = paths[0]
        # Note: This assumes the path has been enriched with segment data
        # In practice, this might require a special API call to get full path details
        if hasattr(path, "path_segments") and path.path_segments is not None:
            actual_count = len(path.path_segments)
            assert (
                actual_count == expected_count
            ), f"Expected {expected_count} segments but got {actual_count}"
        else:
            pytest.skip("Path segment inspection requires full path data from API")
        return self

    def assert_line_segment_points(
        self, segment: Line, p0: Point, p1: Point, epsilon: float = 0.1
    ) -> "PDFAssertions":
        """Assert that a Line segment has the expected start and end points."""
        assert segment.get_p0() is not None, "Line segment p0 is None"
        assert segment.get_p1() is not None, "Line segment p1 is None"

        assert segment.get_p0().x == pytest.approx(
            p0.x, abs=epsilon
        ), f"Line p0.x {segment.get_p0().x} != {p0.x}"
        assert segment.get_p0().y == pytest.approx(
            p0.y, abs=epsilon
        ), f"Line p0.y {segment.get_p0().y} != {p0.y}"

        assert segment.get_p1().x == pytest.approx(
            p1.x, abs=epsilon
        ), f"Line p1.x {segment.get_p1().x} != {p1.x}"
        assert segment.get_p1().y == pytest.approx(
            p1.y, abs=epsilon
        ), f"Line p1.y {segment.get_p1().y} != {p1.y}"
        return self

    def assert_bezier_segment_points(
        self,
        segment: Bezier,
        p0: Point,
        p1: Point,
        p2: Point,
        p3: Point,
        epsilon: float = 0.1,
    ) -> "PDFAssertions":
        """Assert that a Bezier segment has the expected four control points."""
        assert segment.get_p0() is not None, "Bezier segment p0 is None"
        assert segment.get_p1() is not None, "Bezier segment p1 is None"
        assert segment.get_p2() is not None, "Bezier segment p2 is None"
        assert segment.get_p3() is not None, "Bezier segment p3 is None"

        for actual, expected, name in [
            (segment.get_p0(), p0, "p0"),
            (segment.get_p1(), p1, "p1"),
            (segment.get_p2(), p2, "p2"),
            (segment.get_p3(), p3, "p3"),
        ]:
            assert actual.x == pytest.approx(
                expected.x, abs=epsilon
            ), f"Bezier {name}.x {actual.x} != {expected.x}"
            assert actual.y == pytest.approx(
                expected.y, abs=epsilon
            ), f"Bezier {name}.y {actual.y} != {expected.y}"
        return self

    def assert_segment_stroke_color(
        self, segment: PathSegment, color: Color
    ) -> "PDFAssertions":
        """Assert that a path segment has the expected stroke color."""
        stroke_color = segment.get_stroke_color()
        assert stroke_color is not None, "Segment has no stroke color"
        assert (
            stroke_color.r == color.r
        ), f"Stroke color R {stroke_color.r} != {color.r}"
        assert (
            stroke_color.g == color.g
        ), f"Stroke color G {stroke_color.g} != {color.g}"
        assert (
            stroke_color.b == color.b
        ), f"Stroke color B {stroke_color.b} != {color.b}"
        assert (
            stroke_color.a == color.a
        ), f"Stroke color A {stroke_color.a} != {color.a}"
        return self

    def assert_segment_fill_color(
        self, segment: PathSegment, color: Color
    ) -> "PDFAssertions":
        """Assert that a path segment has the expected fill color."""
        fill_color = segment.get_fill_color()
        assert fill_color is not None, "Segment has no fill color"
        assert fill_color.r == color.r, f"Fill color R {fill_color.r} != {color.r}"
        assert fill_color.g == color.g, f"Fill color G {fill_color.g} != {color.g}"
        assert fill_color.b == color.b, f"Fill color B {fill_color.b} != {color.b}"
        assert fill_color.a == color.a, f"Fill color A {fill_color.a} != {color.a}"
        return self

    def assert_segment_stroke_width(
        self, segment: PathSegment, width: float, epsilon: float = 0.1
    ) -> "PDFAssertions":
        """Assert that a path segment has the expected stroke width."""
        stroke_width = segment.get_stroke_width()
        assert stroke_width is not None, "Segment has no stroke width"
        assert stroke_width == pytest.approx(
            width, abs=epsilon
        ), f"Stroke width {stroke_width} != {width}"
        return self

    def assert_segment_has_dash_pattern(
        self,
        segment: PathSegment,
        dash_array: List[float],
        dash_phase: float = 0.0,
        epsilon: float = 0.1,
    ) -> "PDFAssertions":
        """Assert that a path segment has the expected dash pattern."""
        actual_array = segment.get_dash_array()
        assert actual_array is not None, "Segment has no dash array"
        assert len(actual_array) == len(
            dash_array
        ), f"Dash array length {len(actual_array)} != {len(dash_array)}"

        for i, (actual, expected) in enumerate(zip(actual_array, dash_array)):
            assert actual == pytest.approx(
                expected, abs=epsilon
            ), f"Dash array[{i}] {actual} != {expected}"

        actual_phase = segment.get_dash_phase()
        if actual_phase is not None:
            assert actual_phase == pytest.approx(
                dash_phase, abs=epsilon
            ), f"Dash phase {actual_phase} != {dash_phase}"
        return self

    def assert_segment_is_solid(self, segment: PathSegment) -> "PDFAssertions":
        """Assert that a path segment has no dash pattern (solid line)."""
        dash_array = segment.get_dash_array()
        assert (
            dash_array is None or len(dash_array) == 0
        ), f"Expected solid line but found dash pattern: {dash_array}"
        return self

    def assert_segment_type(
        self, segment: PathSegment, expected_type: type
    ) -> "PDFAssertions":
        """Assert that a segment is of a specific type (Line or Bezier)."""
        assert isinstance(
            segment, expected_type
        ), f"Expected segment type {expected_type.__name__} but got {type(segment).__name__}"
        return self

    def assert_path_has_even_odd_fill(
        self, x: float, y: float, expected: bool, page=1, tolerance: float = 5.0
    ) -> "PDFAssertions":
        """Assert that a path has the expected even-odd fill rule setting."""
        paths = self.pdf.page(page).select_paths_at(x, y, tolerance)
        assert len(paths) > 0, f"No paths found at ({x}, {y})"

        path = paths[0]
        if hasattr(path, "even_odd_fill") and path.even_odd_fill is not None:
            assert (
                path.even_odd_fill == expected
            ), f"Expected even_odd_fill={expected} but got {path.even_odd_fill}"
        else:
            pytest.skip(
                "Path even-odd fill inspection requires full path data from API"
            )
        return self

    # ========================================
    # Image-specific assertions
    # ========================================

    def get_image_by_id(self, internal_id: str, page: int = None):
        """Get an image by its internal ID.

        Args:
            internal_id: The internal ID of the image
            page: Optional page number to search on. If None, searches all pages.

        Returns:
            The ImageObject with the specified ID

        Raises:
            AssertionError if no image with the ID is found
        """
        if page is not None:
            images = self.pdf.page(page).select_images()
        else:
            images = self.pdf.select_images()

        for img in images:
            if img.internal_id == internal_id:
                return img

        assert False, f"No image found with internal_id={internal_id}"

    def get_image_at(self, x: float, y: float, page: int = 1, tolerance: float = 5.0):
        """Get the first image at the specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            page: Page number (1-based)
            tolerance: Coordinate tolerance

        Returns:
            The ImageObject at the coordinates

        Raises:
            AssertionError if no image is found at the coordinates
        """
        images = self.pdf.page(page).select_images_at(x, y, tolerance)
        assert len(images) > 0, f"No image found at ({x}, {y}) on page {page}"
        return images[0]

    def assert_image_size(
        self,
        internal_id: str,
        width: float,
        height: float,
        page: int = None,
        epsilon: float = 1.0,
    ) -> "PDFAssertions":
        """Assert that an image has the expected size (from bounding rect).

        Args:
            internal_id: The internal ID of the image
            width: Expected width
            height: Expected height
            page: Optional page number
            epsilon: Tolerance for float comparison
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image {internal_id} has no bounding rect"
        assert bbox.width == pytest.approx(
            width, abs=epsilon
        ), f"Image width {bbox.width} != expected {width}"
        assert bbox.height == pytest.approx(
            height, abs=epsilon
        ), f"Image height {bbox.height} != expected {height}"
        return self

    def assert_image_size_at(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        page: int = 1,
        tolerance: float = 5.0,
        epsilon: float = 1.0,
    ) -> "PDFAssertions":
        """Assert that an image at the coordinates has the expected size.

        Args:
            x: X coordinate
            y: Y coordinate
            width: Expected width
            height: Expected height
            page: Page number (1-based)
            tolerance: Coordinate tolerance for finding the image
            epsilon: Tolerance for size comparison
        """
        image = self.get_image_at(x, y, page, tolerance)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image at ({x}, {y}) has no bounding rect"
        assert bbox.width == pytest.approx(
            width, abs=epsilon
        ), f"Image width {bbox.width} != expected {width}"
        assert bbox.height == pytest.approx(
            height, abs=epsilon
        ), f"Image height {bbox.height} != expected {height}"
        return self

    def assert_image_aspect_ratio(
        self,
        internal_id: str,
        expected_ratio: float,
        page: int = None,
        epsilon: float = 0.05,
    ) -> "PDFAssertions":
        """Assert that an image has the expected aspect ratio (width/height).

        Args:
            internal_id: The internal ID of the image
            expected_ratio: Expected width/height ratio
            page: Optional page number
            epsilon: Tolerance for ratio comparison
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image {internal_id} has no bounding rect"
        assert bbox.height > 0, f"Image height is 0, cannot compute aspect ratio"

        actual_ratio = bbox.width / bbox.height
        assert actual_ratio == pytest.approx(
            expected_ratio, abs=epsilon
        ), f"Image aspect ratio {actual_ratio:.3f} != expected {expected_ratio:.3f}"
        return self

    def assert_image_aspect_ratio_at(
        self,
        x: float,
        y: float,
        expected_ratio: float,
        page: int = 1,
        tolerance: float = 5.0,
        epsilon: float = 0.05,
    ) -> "PDFAssertions":
        """Assert that an image at coordinates has the expected aspect ratio.

        Args:
            x: X coordinate
            y: Y coordinate
            expected_ratio: Expected width/height ratio
            page: Page number (1-based)
            tolerance: Coordinate tolerance for finding the image
            epsilon: Tolerance for ratio comparison
        """
        image = self.get_image_at(x, y, page, tolerance)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image at ({x}, {y}) has no bounding rect"
        assert bbox.height > 0, f"Image height is 0, cannot compute aspect ratio"

        actual_ratio = bbox.width / bbox.height
        assert actual_ratio == pytest.approx(
            expected_ratio, abs=epsilon
        ), f"Image aspect ratio {actual_ratio:.3f} != expected {expected_ratio:.3f}"
        return self

    def assert_image_width_changed(
        self,
        internal_id: str,
        original_width: float,
        page: int = None,
        epsilon: float = 1.0,
    ) -> "PDFAssertions":
        """Assert that an image's width has changed from the original.

        Args:
            internal_id: The internal ID of the image
            original_width: The original width before transformation
            page: Optional page number
            epsilon: Tolerance - actual width must differ by more than this
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image {internal_id} has no bounding rect"
        assert (
            abs(bbox.width - original_width) > epsilon
        ), f"Image width {bbox.width} has not changed significantly from original {original_width}"
        return self

    def assert_image_height_changed(
        self,
        internal_id: str,
        original_height: float,
        page: int = None,
        epsilon: float = 1.0,
    ) -> "PDFAssertions":
        """Assert that an image's height has changed from the original.

        Args:
            internal_id: The internal ID of the image
            original_height: The original height before transformation
            page: Optional page number
            epsilon: Tolerance - actual height must differ by more than this
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image {internal_id} has no bounding rect"
        assert (
            abs(bbox.height - original_height) > epsilon
        ), f"Image height {bbox.height} has not changed significantly from original {original_height}"
        return self

    def assert_image_scaled_by_factor(
        self,
        internal_id: str,
        original_width: float,
        original_height: float,
        scale_factor: float,
        page: int = None,
        epsilon: float = 2.0,
    ) -> "PDFAssertions":
        """Assert that an image has been scaled by the expected factor.

        Args:
            internal_id: The internal ID of the image
            original_width: The original width before scaling
            original_height: The original height before scaling
            scale_factor: The expected scale factor
            page: Optional page number
            epsilon: Tolerance for size comparison
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect

        assert bbox is not None, f"Image {internal_id} has no bounding rect"

        expected_width = original_width * scale_factor
        expected_height = original_height * scale_factor

        assert bbox.width == pytest.approx(
            expected_width, abs=epsilon
        ), f"Scaled width {bbox.width} != expected {expected_width} (original {original_width} * {scale_factor})"
        assert bbox.height == pytest.approx(
            expected_height, abs=epsilon
        ), f"Scaled height {bbox.height} != expected {expected_height} (original {original_height} * {scale_factor})"
        return self

    def get_image_size(self, internal_id: str, page: int = None) -> tuple:
        """Get the width and height of an image.

        Args:
            internal_id: The internal ID of the image
            page: Optional page number

        Returns:
            Tuple of (width, height)
        """
        image = self.get_image_by_id(internal_id, page)
        bbox = image.position.bounding_rect
        assert bbox is not None, f"Image {internal_id} has no bounding rect"
        return (bbox.width, bbox.height)
