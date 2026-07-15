"""E2E tests for live-valid Python-only TEXT_LINE reference selection."""

from pathlib import Path

from dotenv import load_dotenv

from pdfdancer import PDFDancer
from tests.e2e import _get_base_url, _server_up


SHOWCASE = Path(__file__).resolve().parents[1] / "fixtures" / "Showcase.pdf"


def _open_showcase_with_fresh_token() -> PDFDancer:
    load_dotenv()
    base_url = _get_base_url()
    up, message = _server_up(base_url)
    assert up, f"PDFDancer server not reachable at {base_url}: {message}"
    token = PDFDancer._obtain_anonymous_token(base_url)
    return PDFDancer.open(SHOWCASE, token=token, base_url=base_url)


def test_text_line_start_and_regex_selection_remain_available():
    with _open_showcase_with_fresh_token() as pdf:
        by_prefix = pdf.page(1).select_text_line_starting_with("PDFDancer Showcase")
        by_regex = pdf.page(1).select_text_line_matching(r"PDFDancer Showcase.*")

        assert by_prefix is not None
        assert by_regex is not None
        assert by_prefix.internal_id == by_regex.internal_id
        assert by_prefix.object_ref().get_text().startswith("PDFDancer Showcase")


def test_text_line_reference_supports_generic_move():
    with _open_showcase_with_fresh_token() as pdf:
        line = pdf.page(1).select_text_line_starting_with("PDFDancer Showcase")
        assert line is not None
        x, y = line.position.x(), line.position.y()
        assert x is not None and y is not None

        target_x, target_y = x + 1.0, y + 1.0
        assert line.move_to(target_x, target_y) is True

        moved = pdf.page(1).select_text_line_at(target_x, target_y, tolerance=0.1)
        assert moved is not None
        assert moved.internal_id == line.internal_id
