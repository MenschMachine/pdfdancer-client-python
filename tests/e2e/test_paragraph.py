import pytest

from pdfdancer import Color, StandardFonts
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture


def test_find_paragraphs_by_position():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paras = pdf.select_paragraphs()
        assert len(paras) == 172

        paras_page0 = pdf.page(0).select_paragraphs()
        assert len(paras_page0) == 2

        first = paras_page0[0]
        assert first.internal_id == "PARAGRAPH_000003"
        assert first.position is not None
        assert pytest.approx(first.position.x(), rel=0, abs=1) == 326
        assert pytest.approx(first.position.y(), rel=0, abs=1) == 706

        last = paras_page0[-1]
        assert last.internal_id == "PARAGRAPH_000004"
        assert last.position is not None
        assert pytest.approx(last.position.x(), rel=0, abs=1) == 54
        assert pytest.approx(last.position.y(), rel=0, abs=2) == 496


def test_find_paragraphs_by_text():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paras = pdf.page(0).select_paragraphs_starting_with("The Complete")
        assert len(paras) == 1
        p = paras[0]
        assert p.internal_id == "PARAGRAPH_000004"
        assert pytest.approx(p.position.x(), rel=0, abs=1) == 54
        assert pytest.approx(p.position.y(), rel=0, abs=2) == 496


def test_delete_paragraph():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        paragraph.delete()
        remaining = pdf.page(0).select_paragraphs_starting_with("The Complete")
        assert remaining == []


def test_move_paragraph():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        paragraph.move_to(0.1, 300)
        moved = pdf.page(0).select_paragraphs_at(0.1, 300)[0]
        assert moved is not None


def _assert_new_paragraph_exists(pdf: PDFDancer):
    lines = pdf.page(0).select_text_lines_starting_with("Awesomely")
    assert len(lines) >= 1


def test_modify_paragraph():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]

        paragraph.edit() \
            .replace("Awesomely\nObvious!") \
            .font("Helvetica", 12) \
            .line_spacing(0.7) \
            .move_to(300.1, 500) \
            .apply()

        _assert_new_paragraph_exists(pdf)


def test_modify_paragraph_simple():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        paragraph.edit().replace("Awesomely\nObvious!").apply()
        _assert_new_paragraph_exists(pdf)


def test_add_paragraph_with_custom_font1_expect_not_found():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        with pytest.raises(Exception, match="Font not found"):
            pdf.new_paragraph() \
                .text("Awesomely\nObvious!") \
                .font("Roboto", 14) \
                .line_spacing(0.7) \
                .at(0, 300.1, 500) \
                .add()


def test_add_paragraph_with_custom_font1_1():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph() \
            .text("Awesomely\nObvious!") \
            .font("Roboto-Regular", 14) \
            .line_spacing(0.7) \
            .at(0, 300.1, 500) \
            .add()
        _assert_new_paragraph_exists(pdf)


def test_add_paragraph_on_page_with_custom_font1_1():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.page(0).new_paragraph() \
            .text("Awesomely\nObvious!") \
            .font("Roboto-Regular", 14) \
            .line_spacing(0.7) \
            .at(300.1, 500) \
            .add()
        _assert_new_paragraph_exists(pdf)


def test_add_paragraph_with_custom_font1_2():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        fonts = pdf.find_fonts("Roboto", 14)
        assert len(fonts) > 0
        assert fonts[0].name.startswith("Roboto")

        roboto = fonts[0]
        pdf.new_paragraph() \
            .text("Awesomely\nObvious!") \
            .font(roboto.name, roboto.size) \
            .line_spacing(0.7) \
            .at(0, 300.1, 500) \
            .add()
        _assert_new_paragraph_exists(pdf)


def test_add_paragraph_with_custom_font2():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        fonts = pdf.find_fonts("Asimovian", 14)
        assert len(fonts) > 0
        assert fonts[0].name == "Asimovian-Regular"

        asimov = fonts[0]
        pdf.new_paragraph() \
            .text("Awesomely\nObvious!") \
            .font(asimov.name, asimov.size) \
            .line_spacing(0.7) \
            .at(0, 300.1, 500) \
            .add()
        _assert_new_paragraph_exists(pdf)


def test_add_paragraph_with_custom_font3():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")
    from pathlib import Path
    repo_root = Path(__file__).resolve().parents[2]
    ttf_path = repo_root / "tests/fixtures" / "DancingScript-Regular.ttf"

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph() \
            .text("Awesomely\nObvious!") \
            .font_file(ttf_path, 24) \
            .line_spacing(1.8) \
            .color(Color(0, 0, 255)) \
            .at(0, 300.1, 500) \
            .add()
        _assert_new_paragraph_exists(pdf)


def test_add_paragraph_with_standard_font_helvetica():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph() \
            .text("Standard Font Test\nHelvetica Bold") \
            .font(StandardFonts.HELVETICA_BOLD.value, 16) \
            .line_spacing(1.2) \
            .color(Color(255, 0, 0)) \
            .at(0, 100, 100) \
            .add()

        lines = pdf.page(0).select_text_lines_starting_with("Standard Font Test")
        assert len(lines) >= 1


def test_add_paragraph_with_standard_font_times():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph() \
            .text("Times Roman Test") \
            .font(StandardFonts.TIMES_ROMAN.value, 14) \
            .at(0, 150, 150) \
            .add()

        lines = pdf.page(0).select_text_lines_starting_with("Times Roman Test")
        assert len(lines) >= 1


def test_add_paragraph_with_standard_font_courier():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        pdf.new_paragraph() \
            .text("Courier Monospace\nCode Example") \
            .font(StandardFonts.COURIER_BOLD.value, 12) \
            .line_spacing(1.5) \
            .at(0, 200, 200) \
            .add()

        lines = pdf.page(0).select_text_lines_starting_with("Courier Monospace")
        assert len(lines) >= 1
