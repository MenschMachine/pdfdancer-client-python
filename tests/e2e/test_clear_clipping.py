from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture
from tests.e2e.pdf_assertions import PDFAssertions


def test_clear_clipping_on_text_line_reveals_full_rendered_text():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            PDFAssertions(pdf)
            .assert_rendered_page_has_line(page=2, expected_line="CLIPP")
            .assert_rendered_page_not_has_line(page=2, unexpected_line="CLIPPED")
        )

        clipped_line = pdf.page(2).select_text_lines_matching("^CLIPPED$")
        assert len(clipped_line) == 1
        assert clipped_line[0].clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_rendered_page_has_line(page=2, expected_line="CLIPPED")
            .assert_rendered_page_not_has_line(page=2, unexpected_line="CLIPP")
        )


def test_clear_clipping_on_paragraph_reveals_full_rendered_text():
    base_url, token, pdf_path = _require_env_and_fixture("Showcase.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        (
            PDFAssertions(pdf)
            .assert_rendered_page_has_line(page=2, expected_line="CLIPP")
            .assert_rendered_page_not_has_line(page=2, unexpected_line="CLIPPED")
        )

        clipped_paragraphs = pdf.page(2).select_paragraphs_matching(".*Non-Zero Rule.*")
        assert len(clipped_paragraphs) == 1
        assert clipped_paragraphs[0].clear_clipping() is True

        (
            PDFAssertions(pdf)
            .assert_rendered_page_has_line(page=2, expected_line="CLIPPED")
            .assert_rendered_page_not_has_line(page=2, unexpected_line="CLIPP")
        )


def test_clear_clipping_on_path_group_is_supported():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(1).select_paths()
        path_ids = [paths[0].internal_id, paths[1].internal_id]
        group = pdf.page(1).group_paths(path_ids)

        assert group.clear_clipping() is True

        groups = pdf.page(1).get_path_groups()
        assert len(groups) == 1
        assert groups[0].group_id == group.group_id
        (
            PDFAssertions(pdf)
            .assert_number_of_paths(9)
            .assert_path_is_at("PATH_0_000001", 80, 720)
        )
