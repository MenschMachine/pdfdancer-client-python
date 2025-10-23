import pytest

from pdfdancer import Color, StandardFonts, FontType
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


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

        assert last.object_ref().status is not None
        assert last.object_ref().status.is_encodable()
        assert last.object_ref().status.font_type == FontType.EMBEDDED
        assert not last.object_ref().status.is_modified()


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

        assert moved.object_ref().status is not None
        assert moved.object_ref().status.is_encodable()
        assert moved.object_ref().status.font_type == FontType.EMBEDDED
        assert not moved.object_ref().status.is_modified()


def test_modify_paragraph():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]

        (
            paragraph.edit()
            .replace("Awesomely\nObvious!")
            .font("Helvetica", 12)
            .line_spacing(0.7)
            .move_to(300.1, 500)
            .apply()
        )

        moved = pdf.page(0).select_paragraphs_at(300.1, 500)[0]
        assert moved.object_ref().status is not None
        assert moved.object_ref().status.is_encodable()
        assert moved.object_ref().status.font_type == FontType.STANDARD
        assert moved.object_ref().status.is_modified()

    (
        PDFAssertions(pdf)
        .assert_textline_has_font("Awesomely", "Helvetica", 12)
        .assert_textline_has_font("Obvious!", "Helvetica", 12)
        .assert_textline_has_color("Awesomely", Color(255, 255, 255))
        .assert_textline_has_color("Obvious!", Color(255, 255, 255))
        .assert_paragraph_is_at("Awesomely", 300.1, 500)
    )


def test_modify_paragraph_without_position():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        original_x = paragraph.position.x()
        original_y = paragraph.position.y()

        (
            paragraph.edit()
            .replace("Awesomely\nObvious!")
            .font("Helvetica", 12)
            .line_spacing(0.7)
            .apply()
        )

    (
        PDFAssertions(pdf)
        .assert_textline_has_font("Awesomely", "Helvetica", 12)
        .assert_textline_has_font("Obvious!", "Helvetica", 12)
        .assert_textline_has_color("Awesomely", Color(255, 255, 255))
        .assert_textline_has_color("Obvious!", Color(255, 255, 255))
        .assert_paragraph_is_at("Awesomely", original_x, original_y)
    )


def test_modify_paragraph_without_position_and_spacing():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        original_x = paragraph.position.x()
        original_y = paragraph.position.y()
        (
            paragraph.edit()
            .replace("Awesomely\nObvious!")
            .font("Helvetica", 12)
            .apply()
        )

    (
        PDFAssertions(pdf)
        .assert_textline_has_font("Awesomely", "Helvetica", 12)
        .assert_textline_has_font("Obvious!", "Helvetica", 12)
        .assert_textline_has_color("Awesomely", Color(255, 255, 255))
        .assert_textline_has_color("Obvious!", Color(255, 255, 255))
        .assert_paragraph_is_at("Awesomely", original_x, original_y)
    )


def test_modify_paragraph_noop():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        (
            paragraph.edit()
            .apply()
        )
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        assert paragraph.object_ref().status is not None
        assert paragraph.object_ref().status.is_encodable()
        assert paragraph.object_ref().status.font_type == FontType.EMBEDDED
        assert not paragraph.object_ref().status.is_modified()

    (
        PDFAssertions(pdf)
        .assert_textline_has_font("The Complete", "IXKSWR+Poppins-Bold", 1)
        .assert_textline_has_color("The Complete", Color(255, 255, 255))
    )


def test_modify_paragraph_only_text():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        result = (
            paragraph.edit()
            .replace("lorem\nipsum\nCaesar")
            .apply()
        )

        # this should issue a warning about an modified text with an embedded font
        # the information is right now only available when selecting the paragraph again, that's bad
        assert result.warning is not None
        assert "You are using an embedded font and modified the text." in result.warning

        paragraph = pdf.page(0).select_paragraphs_starting_with("lorem")[0]
        assert paragraph.object_ref().status is not None
        assert paragraph.object_ref().status.is_encodable()
        assert paragraph.object_ref().status.font_type == FontType.EMBEDDED
        assert paragraph.object_ref().status.is_modified()

    (
        PDFAssertions(pdf)
        .assert_textline_does_not_exist("The Complete")
        .assert_textline_has_color("lorem", Color(255, 255, 255))
        .assert_textline_has_color("ipsum", Color(255, 255, 255))
        .assert_textline_has_color("Caesar", Color(255, 255, 255))
    )


def test_modify_paragraph_only_font():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        (
            paragraph.edit()
            .font("Helvetica", 28)
            .apply()
        )
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        assert paragraph.object_ref().status is not None
        assert paragraph.object_ref().status.is_encodable()
        assert paragraph.object_ref().status.font_type == FontType.STANDARD
        assert paragraph.object_ref().status.is_modified()

    # TODO does not preserve color and fucks up line spacings
    (
        PDFAssertions(pdf)
        .assert_textline_has_font("The Complete", "Helvetica", 28)
        .assert_textline_has_color("The Complete", Color(255, 255, 255))
    )


def test_modify_paragraph_only_move():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]

        (
            paragraph.edit()
            .move_to(1, 1)
            .apply()
        )

        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        assert paragraph.object_ref().status is not None
        assert paragraph.object_ref().status.is_encodable()
        assert paragraph.object_ref().status.font_type == FontType.EMBEDDED
        assert paragraph.object_ref().status.is_modified()  # This should actually not be marked as 'modified' but since we are using a ModifyObject operation we are not (yet) able to detect this

    (
        PDFAssertions(pdf)
        .assert_textline_has_font("The Complete", "IXKSWR+Poppins-Bold", 1)
        .assert_textline_is_at("The Complete", 1, 1, 0, epsilon=0.22)
        .assert_textline_has_color("The Complete", Color(255, 255, 255))
    )


def test_modify_paragraph_simple():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paragraph = pdf.page(0).select_paragraphs_starting_with("The Complete")[0]
        paragraph.edit().replace("Awesomely\nObvious!").apply()

        paragraph = pdf.page(0).select_paragraphs_starting_with("Awesomely")[0]
        assert paragraph.object_ref().status is not None
        assert paragraph.object_ref().status.is_encodable()
        assert paragraph.object_ref().status.font_type == FontType.EMBEDDED
        assert paragraph.object_ref().status.is_modified()

    (
        PDFAssertions(pdf)
        .assert_textline_has_font("Awesomely", "IXKSWR+Poppins-Bold", 1)
        .assert_textline_has_font("Obvious!", "IXKSWR+Poppins-Bold", 1)
        .assert_textline_has_color("Awesomely", Color(255, 255, 255))
        .assert_textline_has_color("Obvious!", Color(255, 255, 255))
    )


def test_add_paragraph_with_custom_font1_expect_not_found():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        with pytest.raises(Exception, match="Font not found"):
            response = (
                pdf.new_paragraph()
                .text("Awesomely\nObvious!")
                .font("Roboto", 14)
                .line_spacing(0.7)
                .at(0, 300.1, 500)
                .add()
            )
            print(response)


def test_add_paragraph_with_custom_font1_1():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            pdf.new_paragraph()
            .text("Awesomely\nObvious!")
            .font("Roboto-Regular", 14)
            .line_spacing(0.7)
            .at(0, 300.1, 500)
            .add()
        )

    (
        PDFAssertions(pdf)
        .assert_textline_has_font_matching("Awesomely", "Roboto-Regular", 14)
        .assert_textline_has_font_matching("Obvious!", "Roboto-Regular", 14)
        .assert_textline_has_color("Awesomely", Color(0, 0, 0))
        .assert_textline_has_color("Obvious!", Color(0, 0, 0))
        .assert_paragraph_is_at("Awesomely", 300.1, 500, 0)
    )


def test_add_paragraph_on_page_with_custom_font1_1():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            pdf.page(0).new_paragraph()
            .text("Awesomely\nObvious!")
            .font("Roboto-Regular", 14)
            .line_spacing(0.7)
            .at(300.1, 500)
            .add()
        )

    (
        PDFAssertions(pdf)
        .assert_textline_has_font_matching("Awesomely", "Roboto-Regular", 14)
        .assert_textline_has_font_matching("Obvious!", "Roboto-Regular", 14)
        .assert_textline_has_color("Awesomely", Color(0, 0, 0))
        .assert_textline_has_color("Obvious!", Color(0, 0, 0))
        .assert_paragraph_is_at("Awesomely", 300.1, 500, 0)
    )


def test_add_paragraph_with_custom_font1_2():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        fonts = pdf.find_fonts("Roboto", 14)
        assert len(fonts) > 0
        assert fonts[0].name.startswith("Roboto")

        roboto = fonts[0]
        (
            pdf.new_paragraph()
            .text("Awesomely\nObvious!")
            .font(roboto.name, roboto.size)
            .line_spacing(0.7)
            .at(0, 300.1, 500)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_font_matching("Awesomely", "Roboto", 14)
            .assert_textline_has_font_matching("Obvious!", "Roboto", 14)
            .assert_textline_has_color("Awesomely", Color(0, 0, 0))
            .assert_textline_has_color("Obvious!", Color(0, 0, 0))
            .assert_paragraph_is_at("Awesomely", 300.1, 500, 0)
        )


def test_add_paragraph_with_custom_font2():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        fonts = pdf.find_fonts("Asimovian", 14)
        assert len(fonts) > 0
        assert fonts[0].name == "Asimovian-Regular"

        asimov = fonts[0]
        (
            pdf.new_paragraph()
            .text("Awesomely\nObvious!")
            .font(asimov.name, asimov.size)
            .line_spacing(0.7)
            .at(0, 300.1, 500)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_font_matching("Awesomely", "Asimovian-Regular", 14)
            .assert_textline_has_font_matching("Obvious!", "Asimovian-Regular", 14)
            .assert_textline_has_color("Awesomely", Color(0, 0, 0))
            .assert_textline_has_color("Obvious!", Color(0, 0, 0))
            .assert_paragraph_is_at("Awesomely", 300.1, 500, 0)
        )


def test_add_paragraph_with_custom_font3():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")
    from pathlib import Path
    repo_root = Path(__file__).resolve().parents[2]
    ttf_path = repo_root / "tests/fixtures" / "DancingScript-Regular.ttf"

    with (PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf):
        (
            pdf.new_paragraph()
            .text("Awesomely\nObvious!")
            .font_file(ttf_path, 24)
            .line_spacing(1.8)
            .color(Color(0, 0, 255))
            .at(0, 300.1, 500)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_font_matching("Awesomely", "DancingScript-Regular", 24)
            .assert_textline_has_font_matching("Obvious!", "DancingScript-Regular", 24)
            .assert_textline_has_color("Awesomely", Color(0, 0, 255))
            .assert_textline_has_color("Obvious!", Color(0, 0, 255))
            .assert_paragraph_is_at("Awesomely", 300.1, 500, 0)
        )


def test_add_paragraph_with_standard_font_times():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            pdf.new_paragraph()
            .text("Times Roman Test")
            .font(StandardFonts.TIMES_ROMAN.value, 14)
            .at(0, 150, 150)
            .add()
        )
    (
        PDFAssertions(pdf)
        .assert_text_has_font("Times Roman Test", StandardFonts.TIMES_ROMAN.value, 14)
        .assert_paragraph_is_at("Times Roman Test", 150, 150, 0)
    )


def test_add_paragraph_with_standard_font_courier():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            pdf.new_paragraph()
            .text("Courier MonospacenCode Example")
            .font(StandardFonts.COURIER_BOLD.value, 12)
            .line_spacing(1.5)
            .at(0, 200, 200)
            .add()
        )

    (
        PDFAssertions(pdf)
        .assert_text_has_font("Courier Monospace", StandardFonts.COURIER_BOLD.value, 12, page=0)
        .assert_paragraph_is_at("Courier Monospace", 200, 200, page=0)
    )


def test_paragraph_color_reading():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            pdf.new_paragraph()
            .text("Red Color Test")
            .font(StandardFonts.HELVETICA.value, 14)
            .color(Color(255, 0, 0))
            .at(0, 100, 100)
            .add()
        )

        (
            pdf.new_paragraph()
            .text("Blue Color Test")
            .font(StandardFonts.HELVETICA.value, 14)
            .color(Color(0, 0, 255))
            .at(0, 100, 120)
            .add()
        )

        (
            PDFAssertions(pdf)
            .assert_textline_has_color("Blue Color Test", Color(0, 0, 255), page=0)
            .assert_textline_has_color("Red Color Test", Color(255, 0, 0), page=0)
        )


def test_add_paragraph_to_new_page():
    base_url, token, pdf_path = _require_env_and_fixture("Empty.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url) as pdf:
        (
            pdf.page(0).new_paragraph()
            .text("Awesome")
            .font("Roboto-Regular", 14)
            .at(50, 100)
            .add()
        )

    (
        PDFAssertions(pdf)
        .assert_textline_has_font_matching("Awesome", "Roboto-Regular", 14)
        .assert_textline_has_color("Awesome", Color(0, 0, 0))
        .assert_paragraph_is_at("Awesome", 50, 100, 0)
    )
