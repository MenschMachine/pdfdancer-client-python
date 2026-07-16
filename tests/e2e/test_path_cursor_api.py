import math
from collections.abc import Callable

import pytest

from pdfdancer import (
    Color,
    Orientation,
    PageSize,
    PDFDancer,
    ValidationException,
)
from tests.e2e import _require_env
from tests.e2e.pdf_assertions import PDFAssertions


def _new_pdf() -> PDFDancer:
    base_url, token = _require_env()
    return PDFDancer.new(
        token=token,
        base_url=base_url,
        page_size=PageSize.A4,
        orientation=Orientation.PORTRAIT,
    )


def _assert_validation(action: Callable[[], object], message: str) -> None:
    with pytest.raises(ValidationException, match=message):
        action()


def test_cursor_path_conveniences_persist_at_document_and_page_scope():
    pdf = _new_pdf()

    assert (
        pdf.new_path(1)
        .stroke_color(Color(255, 0, 0))
        .stroke_width(2)
        .fill_color(Color(255, 0, 0, 80))
        .dash_pattern([5, 2], 1)
        .solid()
        .move_to(20, 20)
        .line_to(100, 20)
        .bezier_to(120, 20, 120, 80, 100, 80)
        .line_to(20, 80)
        .close_path()
        .add()
    )
    assert (
        pdf.page(1)
        .new_path()
        .stroke_color(Color.BLACK)
        .dash_pattern([4, 2], 2)
        .rectangle(160, 20, 60, 40)
        .add()
    )
    assert (
        pdf.page(1)
        .new_path()
        .fill_color(Color(200, 220, 255, 128))
        .even_odd_fill()
        .circle(280, 60, 30)
        .add()
    )

    assert len(pdf.page(1).select_paths()) == 3

    assertions = PDFAssertions(pdf)
    (
        assertions.assert_number_of_paths(3, page=1)
        .assert_path_exists_at(20, 20, page=1)
        .assert_path_exists_at(160, 20, page=1)
        .assert_path_exists_at(280, 90, page=1)
    )


def test_cursor_operations_require_a_current_subpath():
    pdf = _new_pdf()

    _assert_validation(
        lambda: pdf.page(1).new_path().line_to(10, 10),
        r"move_to\(\).*line_to",
    )
    _assert_validation(
        lambda: pdf.page(1).new_path().bezier_to(1, 1, 2, 2, 3, 3),
        r"move_to\(\).*bezier_to",
    )
    _assert_validation(
        lambda: pdf.page(1).new_path().close_path(),
        r"move_to\(\).*close_path",
    )
    _assert_validation(
        lambda: pdf.page(1).new_path().add(),
        "at least one segment",
    )
    _assert_validation(
        lambda: pdf.page(1).new_path().add_segment(None),
        "segment cannot be null",
    )


def test_cursor_operations_reject_nonfinite_coordinates():
    pdf = _new_pdf()

    actions = [
        lambda: pdf.page(1).new_path().move_to(math.nan, 0),
        lambda: pdf.page(1).new_path().move_to(0, math.inf),
        lambda: pdf.page(1).new_path().move_to(0, 0).line_to(-math.inf, 10),
        lambda: pdf.page(1).new_path().move_to(0, 0).bezier_to(1, 1, math.nan, 2, 3, 3),
    ]

    for action in actions:
        _assert_validation(action, "finite")


def test_rectangle_and_circle_reject_invalid_geometry():
    pdf = _new_pdf()

    invalid_rectangles = [
        lambda: pdf.page(1).new_path().rectangle(0, 0, 0, 10),
        lambda: pdf.page(1).new_path().rectangle(0, 0, 10, -1),
        lambda: pdf.page(1).new_path().rectangle(math.inf, 0, 10, 10),
    ]
    invalid_circles = [
        lambda: pdf.page(1).new_path().circle(20, 20, 0),
        lambda: pdf.page(1).new_path().circle(20, 20, -1),
        lambda: pdf.page(1).new_path().circle(20, math.nan, 1),
    ]

    for action in invalid_rectangles + invalid_circles:
        _assert_validation(action, "positive|finite")


def test_cursor_styles_reject_invalid_widths_and_dash_patterns():
    pdf = _new_pdf()

    invalid_widths = [
        lambda: pdf.page(1).new_path().stroke_width(-0.1),
        lambda: pdf.page(1).new_path().stroke_width(math.nan),
        lambda: pdf.page(1).new_path().stroke_width(math.inf),
    ]
    invalid_dashes = [
        lambda: pdf.page(1).new_path().dash_pattern(None),
        lambda: pdf.page(1).new_path().dash_pattern([-1, 2]),
        lambda: pdf.page(1).new_path().dash_pattern([math.nan, 2]),
        lambda: pdf.page(1).new_path().dash_pattern([0, 0]),
        lambda: pdf.page(1).new_path().dash_pattern([2, 1], -1),
        lambda: pdf.page(1).new_path().dash_pattern([2, 1], math.inf),
    ]

    for action in invalid_widths + invalid_dashes:
        _assert_validation(action, "finite|nonnegative|all zero|null")


def test_document_scoped_path_builder_rejects_invalid_page_number():
    pdf = _new_pdf()

    _assert_validation(lambda: pdf.new_path(0), ">= 1")
