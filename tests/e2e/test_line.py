import pytest

from pdfdancer import FontType
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_find_lines_by_position_multi():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        for i in range(0, 10):
            for line in pdf.select_text_lines():
                assert line.object_ref().status is not None
                assert not line.object_ref().status.is_modified()
                assert line.object_ref().status.is_encodable()


def test_find_lines_by_position():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        lines = pdf.select_text_lines()
        assert len(lines) == 340

        first = lines[0]
        assert first.internal_id == "TEXTLINE_000001"
        assert first.position is not None
        assert pytest.approx(first.position.x(), rel=0, abs=1) == 326
        assert pytest.approx(first.position.y(), rel=0, abs=1) == 706
        assert first.object_ref().status is not None
        assert not first.object_ref().status.is_modified()
        assert first.object_ref().status.is_encodable()

        last = lines[-1]
        assert last.internal_id == "TEXTLINE_000340"
        assert last.position is not None
        assert pytest.approx(last.position.x(), rel=0, abs=2) == 548
        assert pytest.approx(last.position.y(), rel=0, abs=2) == 35
        assert last.object_ref().status is not None
        assert not last.object_ref().status.is_modified()
        assert last.object_ref().status.is_encodable()


def test_find_lines_by_text():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        lines = pdf.page(0).select_text_lines_starting_with("the complete")
        assert len(lines) == 1

        line = lines[0]
        assert line.internal_id == "TEXTLINE_000002"
        assert pytest.approx(line.position.x(), rel=0, abs=1) == 54
        assert pytest.approx(line.position.y(), rel=0, abs=2) == 606


def test_delete_line():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        line = pdf.page(0).select_text_lines_starting_with("The Complete")[0]
        line.delete()
        assert pdf.page(0).select_text_lines_starting_with("The Complete") == []

    (
        PDFAssertions(pdf)
        .assert_textline_does_not_exist("The Complete")
    )


def test_move_line():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    new_x = None
    new_y = None
    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        line = pdf.page(0).select_text_lines_starting_with("The Complete")[0]
        pos = line.position
        new_x = pos.x() + 100
        new_y = pos.y() + 18
        line.move_to(new_x, new_y)

        moved_line = pdf.page(0).select_text_lines_at(new_x, new_y, 1)[0]
        assert moved_line is not None
        assert moved_line.object_ref().status is not None
        assert moved_line.object_ref().status.is_encodable()
        assert moved_line.object_ref().status.font_type == FontType.EMBEDDED
        assert not moved_line.object_ref().status.is_modified()

    (
        PDFAssertions(pdf)
        .assert_textline_is_at("The Complete", new_x, new_y)
    )


def test_modify_line():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        line = pdf.page(0).select_text_lines_starting_with("The Complete")[0]
        result = line.edit().replace(" replaced ").apply()

        # this should issue a warning about an modified text with an embedded font
        # the information is right now only available when selecting the paragraph again, that's bad
        assert result.warning is not None
        assert "You are using an embedded font and modified the text." in result.warning

        # Validate replacements
        assert pdf.page(0).select_text_lines_starting_with("The Complete") == []
        lines = pdf.page(0).select_text_lines_starting_with(" replaced ")
        assert lines != []
        assert pdf.page(0).select_paragraphs_starting_with(" replaced ") != []
        assert lines[0] is not None
        assert lines[0].object_ref().status is not None
        assert lines[0].object_ref().status.is_encodable
        assert lines[0].object_ref().status.font_type == FontType.EMBEDDED
        assert lines[0].object_ref().status.is_modified
    (
        PDFAssertions(pdf)
        .assert_textline_does_not_exist("The Complete")
        .assert_textline_exists(" replaced ")
        .assert_paragraph_exists(" replaced ")
    )


def test_modify_line_multi():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        line_text = "The Complete"
        for i in range(0, 10):
            line = pdf.page(0).select_text_lines_starting_with(line_text)[0]
            line_text = f"{i} The Complete C"
            # line.edit().replace(line_text).color(Color(255, 0, 0)).apply()
            assert line.edit().replace(line_text).apply()
        pdf.save("/tmp/test_modify_line_multi.pdf")

    (
        PDFAssertions(pdf)
        .assert_textline_exists("9 The Complete C")
    )
