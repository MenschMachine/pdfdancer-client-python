import pytest

from pdfdancer import ClientV1, Position, Font, Color
from tests.e2e import _require_env_and_fixture


def test_find_paragraphs_by_position():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        paras = client.find_paragraphs(None)
        assert len(paras) == 172

        paras_page0 = client.find_paragraphs(Position.at_page(0))
        assert len(paras_page0) == 2

        first = paras_page0[0]
        assert first.internal_id == 'PARAGRAPH_000003'
        assert first.position is not None
        assert first.position.bounding_rect.x == pytest.approx(326, rel=0, abs=1)
        assert first.position.bounding_rect.y == pytest.approx(706, rel=0, abs=1)

        last = paras_page0[-1]
        assert last.internal_id == 'PARAGRAPH_000004'
        assert last.position is not None
        assert last.position.bounding_rect.x == pytest.approx(54, rel=0, abs=1)
        assert last.position.bounding_rect.y == pytest.approx(496, rel=0, abs=2)


def test_find_paragraphs_by_text():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pos = Position.at_page(0).with_text_starts('The Complete')
        paras = client.find_paragraphs(pos)
        assert len(paras) == 1
        p = paras[0]
        assert p.internal_id == 'PARAGRAPH_000004'
        assert p.position is not None
        assert p.position.bounding_rect.x == pytest.approx(54, rel=0, abs=1)
        assert p.position.bounding_rect.y == pytest.approx(496, rel=0, abs=2)


def test_delete_paragraph():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pos_del = Position.at_page(0).with_text_starts('The Complete')
        ref = client.find_paragraphs(pos_del)[0]
        assert client.delete(ref) is True
        pos_del2 = Position.at_page(0).with_text_starts('The Complete')
        assert client.find_paragraphs(pos_del2) == []


def test_move_paragraph():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pos_move = Position.at_page(0).with_text_starts('The Complete')
        ref = client.find_paragraphs(pos_move)[0]
        new_pos = Position.at_page_coordinates(0, 0.1, 300)
        assert client.move(ref, new_pos) is True
        ref2 = client.find_paragraphs(new_pos)[0]
        assert ref2 is not None


def _assert_new_paragraph_exists(client: ClientV1):
    # Validate via find_text_lines for text starting with 'Awesomely'
    pos = Position.at_page(0).with_text_starts('Awesomely')
    lines = client.find_text_lines(pos)
    assert len(lines) >= 1


def test_modify_paragraph():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pos_mod = Position.at_page(0).with_text_starts('The Complete')
        ref = client.find_paragraphs(pos_mod)[0]
        new_paragraph = client.paragraph_builder() \
            .from_string('Awesomely\nObvious!') \
            .with_font(Font('Helvetica', 14)) \
            .with_line_spacing(0.7) \
            .with_position(Position.at_page_coordinates(0, 300.1, 500)) \
            .build()
        assert client.modify_paragraph(ref, new_paragraph) is True
        _assert_new_paragraph_exists(client)


def test_modify_paragraph_simple():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pos_mod2 = Position.at_page(0).with_text_starts('The Complete')
        ref = client.find_paragraphs(pos_mod2)[0]
        assert client.modify_paragraph(ref, 'Awesomely\nObvious!') is True
        _assert_new_paragraph_exists(client)


def test_add_paragraph_with_custom_font1_expect_not_found():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pb = client.paragraph_builder() \
            .from_string('Awesomely\nObvious!') \
            .with_font(Font('Roboto', 14)) \
            .with_line_spacing(0.7) \
            .with_position(Position.at_page_coordinates(0, 300.1, 500))
        with pytest.raises(Exception) as excinfo:
            assert client.add_paragraph(pb.build()) is True
        assert 'Font not found' in str(excinfo.value)


def test_add_paragraph_with_custom_font1_1():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pb = client.paragraph_builder() \
            .from_string('Awesomely\nObvious!') \
            .with_font(Font('Roboto-Regular', 14)) \
            .with_line_spacing(0.7) \
            .with_position(Position.at_page_coordinates(0, 300.1, 500))
        assert client.add_paragraph(pb.build()) is True
        _assert_new_paragraph_exists(client)


def test_add_paragraph_with_custom_font1_2():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        fonts = client.find_fonts('Roboto', 14)
        assert len(fonts) > 0
        assert fonts[0].name == 'Roboto-Regular'
        roboto = fonts[0]
        pb = client.paragraph_builder() \
            .from_string('Awesomely\nObvious!') \
            .with_font(roboto) \
            .with_line_spacing(0.7) \
            .with_position(Position.at_page_coordinates(0, 300.1, 500))
        assert client.add_paragraph(pb.build()) is True
        _assert_new_paragraph_exists(client)


def test_add_paragraph_with_custom_font2():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        fonts = client.find_fonts('Asimovian', 14)
        assert len(fonts) > 0
        assert fonts[0].name == 'Asimovian-Regular'
        asimovian = fonts[0]
        pb = client.paragraph_builder() \
            .from_string('Awesomely\nObvious!') \
            .with_font(asimovian) \
            .with_line_spacing(0.7) \
            .with_position(Position.at_page_coordinates(0, 300.1, 500))
        assert client.add_paragraph(pb.build()) is True
        _assert_new_paragraph_exists(client)


def test_add_paragraph_with_custom_font3():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    # Use DancingScript-Regular.ttf from repo fonts directory
    from pathlib import Path
    repo_root = Path(__file__).resolve().parents[2]
    ttf_path = repo_root / 'tests/fixtures' / 'DancingScript-Regular.ttf'
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pb = client.paragraph_builder() \
            .from_string('Awesomely\nObvious!') \
            .with_font_file(str(ttf_path), 24) \
            .with_line_spacing(1.8) \
            .with_color(Color(0, 0, 255)) \
            .with_position(Position.at_page_coordinates(0, 300.1, 500))
        assert client.add_paragraph(pb.build()) is True
        _assert_new_paragraph_exists(client)
