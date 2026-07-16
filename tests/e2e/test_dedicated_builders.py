from pdfdancer import Color, Orientation, PageSize, PDFDancer
from tests.e2e import _require_env
from tests.e2e.pdf_assertions import PDFAssertions


def test_dedicated_builders_persist_at_document_and_page_scope():
    base_url, token = _require_env()
    pdf = PDFDancer.new(
        token=token,
        base_url=base_url,
        page_size=PageSize.A4,
        orientation=Orientation.PORTRAIT,
    )

    assert (
        pdf.new_line(1)
        .from_point(20, 20)
        .to_point(120, 20)
        .stroke_color(Color(255, 0, 0))
        .stroke_width(2)
        .add()
    )
    assert (
        pdf.page(1)
        .new_line()
        .from_point(20, 40)
        .to_point(120, 40)
        .dash_pattern([4, 2])
        .add()
    )

    assert (
        pdf.new_bezier(1)
        .from_point(20, 80)
        .control_point_1(50, 120)
        .control_point_2(90, 40)
        .to_point(120, 80)
        .add()
    )
    assert (
        pdf.page(1)
        .new_bezier()
        .from_point(20, 100)
        .control_point_1(50, 140)
        .control_point_2(90, 60)
        .to_point(120, 100)
        .fill_color(Color(200, 220, 255, 128))
        .add()
    )

    assert (
        pdf.new_rectangle(1)
        .at_coordinates(150, 20)
        .with_size(80, 40)
        .stroke_color(Color(0, 0, 0))
        .add()
    )
    assert (
        pdf.page(1)
        .new_rectangle()
        .at_coordinates(150, 80)
        .with_size(80, 40)
        .fill_color(Color(255, 220, 200))
        .dash_pattern([4, 2], 2)
        .add()
    )

    assert len(pdf.select_paths()) == 6
    PDFAssertions(pdf).assert_number_of_paths(6, page=1)
