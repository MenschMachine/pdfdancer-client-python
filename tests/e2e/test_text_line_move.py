import pytest

from pdfdancer import ObjectType
from pdfdancer.pdfdancer_v2 import PDFDancer
from tests.e2e import _require_env_and_fixture

TOLERANCE = 0.05


def _open():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")
    return PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0)


# Empty area on page 1 of Showcase.pdf. Lines are moved here because a line moved onto
# another line's baseline is re-detected by the server as a single merged line.
EMPTY_X, EMPTY_Y = 300.0, 300.0


def _pick_movable_line(pdf, page_number=1):
    """A line with unique, non-empty text."""
    lines = [ln for ln in pdf.page(page_number).select_text_lines() if ln.text]
    counts = {}
    for ln in lines:
        counts[ln.text] = counts.get(ln.text, 0) + 1
    for ln in lines:
        if counts[ln.text] == 1:
            return ln
    pytest.skip("No uniquely identifiable text line found on the page")


def _reread(pdf, text, page_number=1):
    matches = [
        ln for ln in pdf.page(page_number).select_text_lines() if ln.text == text
    ]
    assert len(matches) == 1, f"expected exactly one line with text {text!r}"
    return matches[0]


def test_select_text_lines():
    with _open() as pdf:
        lines = pdf.select_text_lines()
        assert lines, "document has no text lines"
        assert all(ln.object_type == ObjectType.TEXT_LINE for ln in lines)
        assert any(ln.text for ln in lines)

        page_lines = pdf.page(1).select_text_lines()
        assert page_lines
        assert all(ln.position.page_number == 1 for ln in page_lines)


def test_move_text_line_to():
    with _open() as pdf:
        line = _pick_movable_line(pdf)
        text = line.text
        old_x, old_y = line.position.x(), line.position.y()

        assert line.move_to(EMPTY_X, EMPTY_Y) is True

        moved = _reread(pdf, text)
        assert moved.position.x() == pytest.approx(EMPTY_X, abs=TOLERANCE)
        assert moved.position.y() == pytest.approx(EMPTY_Y, abs=TOLERANCE)
        assert (moved.position.x(), moved.position.y()) != (old_x, old_y)


def test_move_text_line_relative_composes():
    with _open() as pdf:
        text = _pick_movable_line(pdf).text
        assert _pick_movable_line(pdf).move_to(EMPTY_X, EMPTY_Y) is True

        line = _reread(pdf, text)
        x0, y0 = line.position.x(), line.position.y()

        # Same object, two relative moves: the second must build on the first.
        assert line.move_x(20) is True
        assert line.move_y(-15) is True

        moved = _reread(pdf, text)
        # Observed deltas must match the requested offsets (this catches any
        # mismatch between the reported bounding box and the line's text origin).
        assert moved.position.x() - x0 == pytest.approx(20, abs=TOLERANCE)
        assert moved.position.y() - y0 == pytest.approx(-15, abs=TOLERANCE)


def test_delete_text_line():
    with _open() as pdf:
        line = _pick_movable_line(pdf)
        text = line.text

        assert line.delete() is True

        remaining = [ln for ln in pdf.page(1).select_text_lines() if ln.text == text]
        assert remaining == []


def test_move_image_relative():
    with _open() as pdf:
        image = pdf.select_images()[10]
        page = image.position.page_number
        old_x, old_y = image.position.x(), image.position.y()

        assert image.move_x(20) is True
        assert image.move_y(-15) is True

        new_x, new_y = old_x + 20, old_y - 15
        moved = pdf.page(page).select_images_at(new_x, new_y)
        assert len(moved) == 1
        assert moved[0].position.x() == pytest.approx(new_x, abs=TOLERANCE)
        assert moved[0].position.y() == pytest.approx(new_y, abs=TOLERANCE)
