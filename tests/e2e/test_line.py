import pytest

from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture


def test_find_lines_by_position():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        lines = pdf.select_text_lines()
        assert len(lines) == 340

        first = lines[0]
        assert first.internal_id == "LINE_000001"
        assert first.position is not None
        assert pytest.approx(first.position.x(), rel=0, abs=1) == 326
        assert pytest.approx(first.position.y(), rel=0, abs=1) == 706

        last = lines[-1]
        assert last.internal_id == "LINE_000340"
        assert last.position is not None
        assert pytest.approx(last.position.x(), rel=0, abs=2) == 548
        assert pytest.approx(last.position.y(), rel=0, abs=2) == 35


def test_find_lines_by_text():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        lines = pdf.page(0).select_text_lines_starting_with("the complete")
        assert len(lines) == 1

        line = lines[0]
        assert line.internal_id == "LINE_000002"
        assert pytest.approx(line.position.x(), rel=0, abs=1) == 54
        assert pytest.approx(line.position.y(), rel=0, abs=2) == 606


def test_delete_line(tmp_path):
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        line = pdf.page(0).select_text_lines_starting_with("The Complete")[0]
        line.delete()
        assert pdf.page(0).select_text_lines_starting_with("The Complete") == []

        out = tmp_path / "deleteLine.pdf"
        pdf.save(out)
        assert out.exists() and out.stat().st_size > 0


def test_move_line(tmp_path):
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        line = pdf.page(0).select_text_lines_starting_with("The Complete")[0]
        pos = line.position
        line.move_to(pos.x() + 100, pos.y())

        moved_para = pdf.page(0).select_paragraphs_at(pos.x() + 100, pos.y())[0]
        assert moved_para is not None

        out = tmp_path / "moveLine.pdf"
        pdf.save(out)
        assert out.exists() and out.stat().st_size > 0


def test_modify_line(tmp_path):
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        line = pdf.page(0).select_text_lines_starting_with("The Complete")[0]
        line.edit().replace(" replaced ").apply()

        out = tmp_path / "modifyLine.pdf"
        pdf.save(out)
        assert out.exists() and out.stat().st_size > 0

        # Validate replacements
        assert pdf.page(0).select_text_lines_starting_with("The Complete") == []
        assert pdf.page(0).select_text_lines_starting_with(" replaced ") != []
        assert pdf.page(0).select_paragraphs_starting_with(" replaced ") != []
