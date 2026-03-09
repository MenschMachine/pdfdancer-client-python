from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
)

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


def _write_pdf_with_form_xobject_draw(file_path: Path) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)

    form_xobject = DecodedStreamObject()
    form_xobject.set_data(b"0 0 1 1 re f\n")
    form_xobject.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Form"),
            NameObject("/FormType"): NumberObject(1),
            NameObject("/BBox"): ArrayObject(
                [NumberObject(0), NumberObject(0), NumberObject(1), NumberObject(1)]
            ),
        }
    )
    form_xobject_ref = writer._add_object(form_xobject)

    page_resources = page.get("/Resources")
    if page_resources is None:
        page_resources = DictionaryObject()
        page[NameObject("/Resources")] = page_resources
    page_resources = page_resources.get_object()
    page_xobjects = page_resources.get("/XObject")
    if page_xobjects is None:
        page_xobjects = DictionaryObject()
        page_resources[NameObject("/XObject")] = page_xobjects
    page_xobjects = page_xobjects.get_object()
    page_xobjects[NameObject("/Fm0")] = form_xobject_ref

    content = DecodedStreamObject()
    content.set_data(
        b"\n".join(
            [
                b"q",
                b"50 0 0 50 10 10 cm",
                b"/Fm0 Do",
                b"Q",
            ]
        )
        + b"\n"
    )
    page[NameObject("/Contents")] = writer._add_object(content)

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


def test_extract_page_draw_events_ignores_non_image_xobject_do(tmp_path: Path):
    pdf_path = tmp_path / "form-xobject-only.pdf"
    _write_pdf_with_form_xobject_draw(pdf_path)

    assertions = PDFAssertions.__new__(PDFAssertions)
    assertions._saved_pdf_path = str(pdf_path)

    events = assertions._extract_page_draw_events(1)["images"]
    assert events == []
