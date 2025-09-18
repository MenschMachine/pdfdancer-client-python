import pytest
from pdfdancer import ClientV1, Position

from tests.e2e import _require_env_and_fixture


def test_find_lines_by_position():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        lines = client.find_text_lines(None)
        assert len(lines) == 340

        first = lines[0]
        assert first.internal_id == 'LINE_000001'
        assert first.position is not None
        assert first.position.bounding_rect.x == pytest.approx(326, rel=0, abs=1)
        assert first.position.bounding_rect.y == pytest.approx(706, rel=0, abs=1)

        last = lines[-1]
        assert last.internal_id == 'LINE_000340'
        assert last.position is not None
        assert last.position.bounding_rect.x == pytest.approx(548, rel=0, abs=2)
        assert last.position.bounding_rect.y == pytest.approx(35, rel=0, abs=2)


def test_find_lines_by_text():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pos = Position.from_page_index(0)
        pos.text_starts_with = 'the complete'
        lines = client.find_text_lines(pos)
        assert len(lines) == 1
        line = lines[0]
        assert line.internal_id == 'LINE_000002'
        assert line.position is not None
        assert line.position.bounding_rect.x == pytest.approx(54, rel=0, abs=1)
        assert line.position.bounding_rect.y == pytest.approx(606, rel=0, abs=2)


def test_delete_line(tmp_path):
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pos = Position.from_page_index(0)
        pos.text_starts_with = 'The Complete'
        ref = client.find_text_lines(pos)[0]
        assert client.delete(ref) is True
        pos2 = Position.from_page_index(0)
        pos2.text_starts_with = 'The Complete'
        assert client.find_text_lines(pos2) == []
        out = tmp_path / 'deleteLine.pdf'
        client.save_pdf(out)
        assert out.exists() and out.stat().st_size > 0


def test_move_line(tmp_path):
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pos3 = Position.from_page_index(0)
        pos3.text_starts_with = 'The Complete'
        ref = client.find_text_lines(pos3)[0]
        new_pos = ref.position.copy()
        new_pos.move_x(100)
        assert client.move(ref, new_pos) is True

        ref2 = client.find_paragraphs(new_pos)[0]
        assert ref2 is not None
        out = tmp_path / 'moveLine.pdf'
        client.save_pdf(out)
        assert out.exists() and out.stat().st_size > 0


def test_modify_line(tmp_path):
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        pos4 = Position.from_page_index(0)
        pos4.text_starts_with = 'The Complete'
        ref = client.find_text_lines(pos4)[0]
        assert client.modify_text_line(ref, ' replaced ') is True

        out = tmp_path / 'modifyLine.pdf'
        client.save_pdf(out)
        assert out.exists() and out.stat().st_size > 0

        pos5 = Position.from_page_index(0)
        pos5.text_starts_with = 'The Complete'
        assert client.find_text_lines(pos5) == []
        pos6 = Position.from_page_index(0)
        pos6.text_starts_with = ' replaced '
        assert client.find_text_lines(pos6) != []
        pos7 = Position.from_page_index(0)
        pos7.text_starts_with = ' replaced '
        assert client.find_paragraphs(pos7) != []
