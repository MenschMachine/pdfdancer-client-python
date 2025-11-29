import pytest

from pdfdancer import FontType
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_find_lines_by_position_multi():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        for i in range(0, 10):
            for line in pdf.select_text_lines():
                assert line.object_ref().status is not None
                assert not line.object_ref().status.is_modified()


def test_find_lines_by_position():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        lines = pdf.select_text_lines()
        assert len(lines) == 35

        first = lines[0]
        assert first.position is not None
        assert pytest.approx(first.position.x(), rel=0, abs=1) == 180
        assert pytest.approx(first.position.y(), rel=0, abs=1) == 750
        assert first.object_ref().status is not None
        assert not first.object_ref().status.is_modified()
        # assert first.object_ref().status.is_encodable()

        last = lines[-1]
        assert last.position is not None
        assert pytest.approx(last.position.x(), rel=0, abs=2) == 69.3
        assert pytest.approx(last.position.y(), rel=0, abs=2) == 45
        assert last.object_ref().status is not None
        assert not last.object_ref().status.is_modified()
        # assert last.object_ref().status.is_encodable()


def test_find_lines_by_text():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        lines = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )
        assert len(lines) == 1

        line = lines[0]
        assert pytest.approx(line.position.x(), rel=0, abs=1) == 65
        assert pytest.approx(line.position.y(), rel=0, abs=2) == 706.8


def test_delete_line():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        line = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        line.delete()
        assert (
            pdf.page(1).select_text_lines_starting_with(
                "This is regular Sans text showing alignment and styles."
            )
            == []
        )

        (
            PDFAssertions(pdf).assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles."
            )
        )


def test_move_line():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    new_x = None
    new_y = None
    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        line = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        pos = line.position
        new_x = pos.x() + 100
        new_y = pos.y() + 18
        line.move_to(new_x, new_y)

        moved_line = pdf.page(1).select_text_lines_at(new_x, new_y, 1)[0]
        assert moved_line is not None
        assert moved_line.object_ref().status is not None
        # assert moved_line.object_ref().status.is_encodable()
        assert moved_line.object_ref().status.font_type == FontType.EMBEDDED
        assert not moved_line.object_ref().status.is_modified()

        (
            PDFAssertions(pdf).assert_textline_is_at(
                "This is regular Sans text showing alignment and styles.", new_x, new_y
            )
        )


def test_modify_line():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        line = pdf.page(1).select_text_lines_starting_with(
            "This is regular Sans text showing alignment and styles."
        )[0]
        result = line.edit().replace(" replaced ").apply()

        # Validate replacements
        assert (
            pdf.page(1).select_text_lines_starting_with(
                "This is regular Sans text showing alignment and styles."
            )
            == []
        )
        assert pdf.page(1).select_paragraphs_starting_with(" replaced ") != []
        lines = pdf.page(1).select_text_lines_starting_with(" replaced ")
        assert lines != []
        assert lines[0] is not None
        assert lines[0].object_ref().status is not None
        # assert lines[0].object_ref().status.is_encodable
        assert lines[0].object_ref().status.font_type == FontType.EMBEDDED
        assert lines[0].object_ref().status.is_modified
        (
            PDFAssertions(pdf)
            .assert_textline_does_not_exist(
                "This is regular Sans text showing alignment and styles."
            )
            .assert_textline_exists(" replaced ")
            .assert_paragraph_exists(" replaced ")
        )
