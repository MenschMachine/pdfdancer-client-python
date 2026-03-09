from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

from tests.e2e.pdf_assertions import PDFAssertions


def _write_pdf_with_chained_cm(file_path: Path) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)

    stream = DecodedStreamObject()
    stream.set_data(
        b"\n".join(
            [
                b"q",
                b"1 0 0 1 10 20 cm",
                b"2 0 0 3 0 0 cm",
                b"0 0 1 1 re",
                b"f",
                b"Q",
            ]
        )
        + b"\n"
    )
    page[NameObject("/Contents")] = writer._add_object(stream)

    with file_path.open("wb") as handle:
        writer.write(handle)


def test_extract_page_draw_events_uses_pdf_cm_order(tmp_path: Path):
    pdf_path = tmp_path / "chained-cm.pdf"
    _write_pdf_with_chained_cm(pdf_path)

    assertions = PDFAssertions.__new__(PDFAssertions)
    assertions._saved_pdf_path = str(pdf_path)

    events = assertions._extract_page_draw_events(1)["paths"]
    assert len(events) == 1

    # PDF cm operators concatenate as CTM = CTM * M, so this sequence
    # (translate, then scale) yields a translated unit square of size 2x3.
    assert events[0]["bbox"] == pytest.approx((10.0, 20.0, 12.0, 23.0))
