import pytest

from pdfdancer import ObjectType
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture


def test_find_paths():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.select_paths()
        assert len(paths) == 9
        assert paths[0].type == ObjectType.PATH

        p1 = paths[0]
        assert p1 is not None
        assert p1.internal_id == "PATH_000001"
        assert pytest.approx(p1.position.x(), rel=0, abs=1) == 80
        assert pytest.approx(p1.position.y(), rel=0, abs=1) == 720


def test_find_paths_by_position():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(0).select_paths_at(80, 720)
        assert len(paths) == 1
        assert paths[0].internal_id == "PATH_000001"


def test_delete_path():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        paths = pdf.page(0).select_paths_at(80, 720)
        assert len(paths) == 1
        path = paths[0]
        assert path.internal_id == "PATH_000001"

        path.delete()

        # Should no longer exist at that position
        assert pdf.page(0).select_paths_at(80, 720) == []

        # Remaining paths should be 8 total
        assert len(pdf.select_paths()) == 8


def test_move_path():
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        path = pdf.page(0).select_paths_at(80, 720)[0]
        pos = path.position

        assert pytest.approx(pos.x(), rel=0, abs=1) == 80
        assert pytest.approx(pos.y(), rel=0, abs=1) == 720

        path.move_to(50.1, 100)

        # Should be gone from old location
        assert pdf.page(0).select_paths_at(80, 720) == []

        # Should now exist at new location
        new_path = pdf.page(0).select_paths_at(50.1, 100)[0]
        new_pos = new_path.position
        assert pytest.approx(new_pos.x(), rel=0, abs=0.05) == 50.1
        assert pytest.approx(new_pos.y(), rel=0, abs=0.05) == 100
