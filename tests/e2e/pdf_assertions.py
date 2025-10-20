import tempfile
from typing import Optional

import pytest

from pdfdancer import PDFDancer, Color, Orientation


class PDFAssertions(object):

    # noinspection PyProtectedMember
    def __init__(self, pdf_dancer: PDFDancer):
        token = pdf_dancer._token
        base_url = pdf_dancer._base_url
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode="w+t") as temp_file:
            pdf_dancer.save(temp_file.name)
            print(f"Saving PDF file to {temp_file.name}")
        self.pdf = PDFDancer.open(temp_file.name, token=token, base_url=base_url)

    def assert_text_has_color(self, text, color: Color, page=0):
        self.assert_textline_has_color(text, color, page)

        paragraphs = self.pdf.page(page).select_paragraphs_matching(text)
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()
        assert text in reference.get_text()
        assert color == reference.get_color(), f"{color} != {reference.get_color()}"
        return self

    def assert_text_has_font(self, text, font_name, font_size, page=0):
        self.assert_textline_has_font(text, font_name, font_size, page)

        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()
        assert font_name == reference.get_font_name(), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()

        return self

    def assert_paragraph_is_at(self, text, x, y, page=0, epsilon=1e-6):
        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()

        assert reference.get_position().x() == pytest.approx(x, rel=epsilon,
                                                             abs=epsilon), f"{x} != {reference.get_position().x()}"
        assert reference.get_position().y() == pytest.approx(y, rel=epsilon,
                                                             abs=epsilon), f"{y} != {reference.get_position().y()}"

        paragraph_by_position = self.pdf.page(page).select_paragraphs_at(x, y)
        assert paragraphs[0] == paragraph_by_position[0]
        return self

    def assert_text_has_font_matching(self, text, font_name, font_size, page=0):
        self.assert_textline_has_font_matching(text, font_name, font_size, page)

        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()
        assert font_name in reference.get_font_name(), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()
        return self

    def assert_textline_has_color(self, text: str, color: Color, page=0):
        lines = self.pdf.page(page).select_text_lines_matching(text)
        assert len(lines) == 1, f"Expected 1 line but got {len(lines)}"
        reference = lines[0].object_ref()
        assert color == reference.get_color(), f"{color} != {reference.get_color()}"
        assert text in reference.get_text()
        return self

    def assert_textline_has_font(self, text: str, font_name: str, font_size: int, page=0):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1, f"Expected 1 line but got {len(lines)}"
        reference = lines[0].object_ref()
        assert font_name == reference.get_font_name(), f"Expected {font_name} but got {reference.get_font_name()}"
        assert font_size == reference.get_font_size(), f"{font_size} != {reference.get_font_size()}"
        return self

    def assert_textline_has_font_matching(self, text, font_name: str, font_size: int, page=0):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1, f"Expected 1 line but got {len(lines)}"
        reference = lines[0].object_ref()
        assert font_name in reference.get_font_name(), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()
        return self

    def assert_textline_is_at(self, text: str, x: float, y: float, page=0, epsilon=1e-6):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1
        reference = lines[0].object_ref()
        assert reference.get_position().x() == pytest.approx(x, rel=epsilon,
                                                             abs=epsilon), f"{x} != {reference.get_position().x()}"
        assert reference.get_position().y() == pytest.approx(y, rel=epsilon,
                                                             abs=epsilon), f"{y} != {reference.get_position().y()}"

        by_position = self.pdf.page(page).select_text_lines_at(x, y)
        assert lines[0] == by_position[0]
        return self

    def assert_textline_does_not_exist(self, text, page=0):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 0
        return self

    def assert_textline_exists(self, text, page=0):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1
        return self

    def assert_paragraph_exists(self, text, page=0):
        lines = self.pdf.page(page).select_paragraphs_starting_with(text)
        assert len(lines) == 1, f"No paragraphs starting with {text} found on page {page}"
        return self

    def assert_number_of_pages(self, page_count: int):
        assert len(self.pdf.pages()) == page_count, f"Expected {page_count} pages, but got {len(self.pdf.pages())}"
        return self

    def assert_path_is_at(self, internal_id: str, x: float, y: float, page=0, epsilon=1e-6):
        paths = self.pdf.page(page).select_paths_at(x, y)
        assert len(paths) == 1
        reference = paths[0].object_ref()
        assert reference.internal_id == internal_id, f"{internal_id} != {reference.internal_id}"
        assert reference.get_position().x() == pytest.approx(x, rel=epsilon,
                                                             abs=epsilon), f"{x} != {reference.get_position().x()}"
        assert reference.get_position().y() == pytest.approx(y, rel=epsilon,
                                                             abs=epsilon), f"{y} != {reference.get_position().y()}"

        return self

    def assert_no_path_at(self, x: float, y: float, page=0):
        paths = self.pdf.page(page).select_paths_at(x, y)
        assert len(paths) == 0
        return self

    def assert_number_of_paths(self, path_count: int, page=0):
        paths = self.pdf.page(page).select_paths()
        assert len(paths) == path_count, f"Expected {path_count} paths, but got {len(paths)}"
        return self

    def assert_number_of_images(self, image_count, page=0):
        images = self.pdf.page(page).select_images()
        assert len(images) == image_count, f"Expected {image_count} image but got {len(images)}"
        return self

    def assert_image_at(self, x: float, y: float, page=0):
        images = self.pdf.page(page).select_images_at(x, y)
        all_images = self.pdf.page(page).select_images()
        assert len(
            images) == 1, f"Expected 1 image but got {len(images)}, total images: {len(all_images)}, first pos: {all_images[0].position}"
        return self

    def assert_no_image_at(self, x: float, y: float, page=0) -> 'PDFAssertions':
        images = self.pdf.page(page).select_images_at(x, y)
        assert len(images) == 0, f"Expected 0 image at {x}/{y} but got {len(images)}, {images[0].internal_id}"
        return self

    def assert_image_with_id_at(self, internal_id: str, x: float, y: float, page=0) -> 'PDFAssertions':
        images = self.pdf.page(page).select_images_at(x, y)
        assert len(images) == 1, f"Expected 1 image but got {len(images)}"
        assert images[0].internal_id == internal_id, f"{internal_id} != {images[0].internal_id}"
        return self

    def assert_total_number_of_elements(self, nr_of_elements, page_index=None) -> 'PDFAssertions':
        total = 0
        if page_index is None:
            for page in self.pdf.pages():
                total = total + len(page.select_elements())
        else:
            total = len(self.pdf.page(page_index).select_elements())
        assert total == nr_of_elements, f"Total number of elements differ, actual {total} != expected {nr_of_elements}"
        return self

    def assert_page_count(self, page_count: int) -> 'PDFAssertions':
        assert page_count == len(self.pdf.pages())
        return self

    def assert_page_dimension(self, width: float, height: float, orientation: Optional[Orientation] = None,
                              page_index=0) -> 'PDFAssertions':
        page = self.pdf.page(page_index)
        assert width == page.size.width, f"{width} != {page.size.width}"
        assert height == page.size.height, f"{height} != {page.size.height}"
        if orientation is not None:
            actual_orientation = page.orientation
            if isinstance(actual_orientation, str):
                try:
                    actual_orientation = Orientation(actual_orientation.strip().upper())
                except ValueError:
                    pass
            assert orientation == actual_orientation, f"{orientation} != {actual_orientation}"
        return self
