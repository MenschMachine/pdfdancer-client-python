import tempfile

import pytest

from pdfdancer import PDFDancer, Color


class PDFAssertions(object):

    # noinspection PyProtectedMember
    def __init__(self, pdf_dancer: PDFDancer):
        token = pdf_dancer._token
        base_url = pdf_dancer._base_url
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode="w+t") as temp_file:
            pdf_dancer.save(temp_file.name)
        self.pdf = PDFDancer.open(temp_file.name, token=token, base_url=base_url)

    def assert_text_has_color(self, text, color: Color, page=0):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1
        reference = lines[0].object_ref()
        assert color == reference.get_color(), f"{color} != {reference.get_color()}"
        assert text in reference.get_text()

        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1
        reference = paragraphs[0].object_ref()
        assert color == reference.get_color(), f"{color} != {reference.get_color()}"
        assert text in reference.get_text()
        return self

    def assert_text_has_font(self, text, font_name, font_size, page=0):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1, f"Expected 1 line but got {len(lines)}"
        reference = lines[0].object_ref()
        assert font_name == reference.get_font_name(), f"Expected {font_name} but got {reference.get_font_name()}"
        assert font_size == reference.get_font_size()

        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(lines)}"
        reference = paragraphs[0].object_ref()
        assert font_name == reference.get_font_name(), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()

        return self

    def assert_text_is_at(self, text, x, y, page):
        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(paragraphs)}"
        reference = paragraphs[0].object_ref()
        assert reference.get_position().x() == pytest.approx(x, rel=1e-6,
                                                             abs=1e-9), f"{x} != {reference.get_position().x()}"
        assert y == reference.get_position().y(), f"Expected {y} but got {reference.get_position().y()}"

        paragraph_by_position = self.pdf.page(page).select_paragraphs_at(x, y)
        assert paragraphs[0] == paragraph_by_position[0]

        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1
        reference = lines[0].object_ref()
        assert reference.get_position().x() == pytest.approx(x, rel=1e-6, abs=1e-9)
        # y on lines compared to paragraphs can differ
        assert y > reference.get_position().y() > y - 5, f"{reference.get_position().y()} is out of range {y} +-5"

        by_position = self.pdf.page(page).select_text_lines_at(x, y)
        assert lines[0] == by_position[0]
        return self

    def assert_text_has_font_matching(self, text, font_name, font_size, page=0):
        lines = self.pdf.page(page).select_text_lines_starting_with(text)
        assert len(lines) == 1, f"Expected 1 line but got {len(lines)}"
        reference = lines[0].object_ref()
        assert font_name in reference.get_font_name(), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()

        paragraphs = self.pdf.page(page).select_paragraphs_matching(f".*{text}.*")
        assert len(paragraphs) == 1, f"Expected 1 paragraph but got {len(lines)}"
        reference = paragraphs[0].object_ref()
        assert font_name in reference.get_font_name(), f"Expected {reference.get_font_name()} to match {font_name}"
        assert font_size == reference.get_font_size()
        return self
