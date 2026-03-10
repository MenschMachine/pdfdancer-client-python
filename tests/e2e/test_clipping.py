from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions

CLIPPING_FIXTURE = "invisible-content-clipping-test.pdf"
TARGET_PATH_ID = "PATH_0_000004"
CONTROL_PATH_ID = "PATH_0_000003"
CLIPPED_TEXT = "Clipped endstream endobj text line"
MULTI_STREAM_CLIPPED_TEXT = "Clipped text line from second stream"


def _create_pdf_with_content_streams(content_streams: list[str]) -> bytes:
    content_object_ids = [5 + index for index, _ in enumerate(content_streams)]
    if len(content_object_ids) == 1:
        contents_entry = f"{content_object_ids[0]} 0 R"
    else:
        refs = " ".join(f"{object_id} 0 R" for object_id in content_object_ids)
        contents_entry = f"[{refs}]"

    objects = [
        (1, "<< /Type /Catalog /Pages 2 0 R >>"),
        (2, "<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
        (
            3,
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 4 0 R >> >> /Contents {contents_entry} >>",
        ),
        (4, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
    ]

    for object_id, content_stream in zip(content_object_ids, content_streams):
        objects.append(
            (
                object_id,
                f"<< /Length {len(content_stream.encode('latin1'))} >>\n"
                f"stream\n{content_stream}endstream",
            )
        )

    pdf = "%PDF-1.4\n"
    offsets = {0: 0}
    for object_id, body in objects:
        offsets[object_id] = len(pdf.encode("latin1"))
        pdf += f"{object_id} 0 obj\n{body}\nendobj\n"

    xref_offset = len(pdf.encode("latin1"))
    pdf += f"xref\n0 {len(objects) + 1}\n"
    pdf += "0000000000 65535 f \n"
    for object_id, _ in objects:
        pdf += f"{offsets[object_id]:010d} 00000 n \n"
    pdf += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )

    return pdf.encode("latin1")


def _create_clipped_text_pdf() -> bytes:
    clipped_text_stream = "\n".join(
        [
            "q",
            "0 0 50 50 re",
            "W n",
            "BT",
            "/F1 24 Tf",
            "1 0 0 1 200 400 Tm",
            f"({CLIPPED_TEXT}) Tj",
            "ET",
            "Q",
            "",
        ]
    )
    return _create_pdf_with_content_streams([clipped_text_stream])


def _create_multi_stream_clipped_text_pdf() -> bytes:
    clipping_setup_stream = "\n".join(
        [
            "q",
            "0 0 50 50 re",
            "W n",
            "",
        ]
    )
    clipped_text_stream = "\n".join(
        [
            "BT",
            "/F1 24 Tf",
            "1 0 0 1 200 400 Tm",
            f"({MULTI_STREAM_CLIPPED_TEXT}) Tj",
            "ET",
            "Q",
            "",
        ]
    )
    return _create_pdf_with_content_streams(
        [clipping_setup_stream, clipped_text_stream]
    )


def test_clear_clipping_via_path_reference():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        path = next(
            (
                candidate
                for candidate in pdf.page(1).select_paths()
                if candidate.internal_id == TARGET_PATH_ID
            ),
            None,
        )
        assert path is not None

        (
            PDFAssertions(pdf)
            .assert_path_has_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3, 1)
        )

        assert path.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3, 1)
        )


def test_clear_clipping_via_pdf_api():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        path = next(
            (
                candidate
                for candidate in pdf.page(1).select_paths()
                if candidate.internal_id == TARGET_PATH_ID
            ),
            None,
        )
        assert path is not None

        PDFAssertions(pdf).assert_path_has_clipping(TARGET_PATH_ID)

        assert pdf.clear_clipping(path.object_ref()) is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
        )


def test_clear_path_group_clipping_via_reference():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            PDFAssertions(pdf)
            .assert_path_has_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
        )

        group = pdf.page(1).group_paths([TARGET_PATH_ID])
        assert group.group_id is not None
        assert group.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3, 1)
        )


def test_clear_path_group_clipping_via_pdf_api():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            PDFAssertions(pdf)
            .assert_path_has_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
        )

        group = pdf.page(1).group_paths([TARGET_PATH_ID])
        assert group.group_id is not None
        assert pdf.clear_path_group_clipping(1, group.group_id) is True

        (
            PDFAssertions(pdf)
            .assert_path_has_no_clipping(TARGET_PATH_ID)
            .assert_path_has_clipping(CONTROL_PATH_ID)
            .assert_number_of_paths(3, 1)
        )


def test_clear_clipping_via_image_reference():
    base_url, token, pdf_path = _require_env_and_fixture(CLIPPING_FIXTURE)

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        image = pdf.page(1).select_images()[0]

        (
            PDFAssertions(pdf)
            .assert_image_has_clipping(image.internal_id)
            .assert_path_has_clipping(TARGET_PATH_ID)
        )

        assert image.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_image_has_no_clipping(image.internal_id)
            .assert_path_has_clipping(TARGET_PATH_ID)
            .assert_image_with_id_at(image.internal_id, 200, 400)
        )


def test_clear_clipping_via_text_line_reference():
    base_url, token = _require_env_and_fixture(CLIPPING_FIXTURE)[:2]

    with PDFDancer.open(
        _create_clipped_text_pdf(), token=token, base_url=base_url, timeout=30.0
    ) as pdf:
        line = pdf.page(1).select_text_line_starting_with(CLIPPED_TEXT)
        assert line is not None

        PDFAssertions(pdf).assert_textline_has_clipping(CLIPPED_TEXT)

        assert line.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_textline_has_no_clipping(CLIPPED_TEXT)
            .assert_textline_exists(CLIPPED_TEXT)
        )


def test_detects_clipping_across_multiple_content_streams():
    base_url, token = _require_env_and_fixture(CLIPPING_FIXTURE)[:2]

    with PDFDancer.open(
        _create_multi_stream_clipped_text_pdf(),
        token=token,
        base_url=base_url,
        timeout=30.0,
    ) as pdf:
        line = pdf.page(1).select_text_line_starting_with(MULTI_STREAM_CLIPPED_TEXT)
        assert line is not None

        PDFAssertions(pdf).assert_textline_has_clipping(MULTI_STREAM_CLIPPED_TEXT)

        assert line.clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_textline_has_no_clipping(MULTI_STREAM_CLIPPED_TEXT)
            .assert_textline_exists(MULTI_STREAM_CLIPPED_TEXT)
        )
