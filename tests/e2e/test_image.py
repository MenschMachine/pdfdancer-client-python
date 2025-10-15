from pathlib import Path

import pytest

from pdfdancer import ObjectType
from pdfdancer.pdfdancer_v1 import PDFDancer
from tests.e2e import _require_env_and_fixture


def test_find_images():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        images = pdf.select_images()
        assert len(images) == 3
        assert images[0].object_type == ObjectType.IMAGE

        images_page0 = pdf.page(0).select_images()
        assert len(images_page0) == 2


def test_delete_images(tmp_path: Path):
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        images = pdf.select_images()
        for img in images:
            img.delete()

        assert pdf.select_images() == []

        out = tmp_path / "deleteImage.pdf"
        pdf.save(out)
        assert out.exists() and out.stat().st_size > 0


def test_move_image():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        images = pdf.select_images()
        img = images[2]
        pos = img.position

        assert pytest.approx(pos.x(), rel=0, abs=0.5) == 54
        assert pytest.approx(pos.y(), rel=0, abs=1) == 300

        img.move_to(50.1, 100.0)

        moved = pdf.page(11).select_images_at(50.1, 100.0)[0]
        assert pytest.approx(moved.position.x(), rel=0, abs=0.05) == 50.1
        assert pytest.approx(moved.position.y(), rel=0, abs=0.05) == 100.0


def test_find_image_by_position():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        images_none = pdf.page(11).select_images_at(0, 0)
        assert len(images_none) == 0

        images_found = pdf.page(11).select_images_at(55, 310)
        assert len(images_found) == 1
        assert images_found[0].internal_id == "IMAGE_000003"


def test_add_image():
    base_url, token, pdf_path = _require_env_and_fixture("ObviouslyAwesome.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        images = pdf.select_images()
        assert len(images) == 3

        img_path = Path(__file__).resolve().parent.parent / "fixtures" / "logo-80.png"

        pdf.new_image() \
            .from_file(img_path) \
            .at(page=6, x=50.1, y=98.0) \
            .add()

        images_after = pdf.select_images()
        assert len(images_after) == 4

        images_page6 = pdf.page(6).select_images()
        assert len(images_page6) == 1

        new_image = images_page6[0]
        assert new_image.position.page_index == 6
        assert new_image.internal_id == "IMAGE_000004"
        assert pytest.approx(new_image.position.x(), rel=0, abs=0.05) == 50.1
        assert pytest.approx(new_image.position.y(), rel=0, abs=0.05) == 98.0
