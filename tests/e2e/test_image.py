from pathlib import Path

import pytest

from pdfdancer import ClientV1, Position, ObjectType, Image
from tests.e2e import _require_env_and_fixture


def test_find_images():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        images = client.find_images(None)
        assert len(images) == 3
        assert images[0].type == ObjectType.IMAGE

        images_page0 = client.find_images(Position.at_page(0))
        assert len(images_page0) == 2


def test_delete_images(tmp_path: Path):
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        images = client.find_images(None)
        for obj in images:
            assert client.delete(obj) is True
        assert client.find_images(None) == []

        out = tmp_path / 'deleteImage.pdf'
        client.save_pdf(out)
        assert out.exists() and out.stat().st_size > 0


def test_move_image():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        images = client.find_images(None)
        image_ref = images[2]
        position = image_ref.position
        assert position.bounding_rect.x == pytest.approx(54, rel=0, abs=0.5)
        assert position.bounding_rect.y == pytest.approx(300, rel=0, abs=1)

        assert client.move(image_ref, Position.at_page_coordinates(11, 50.1, 100.0)) is True

        images = client.find_images(None)
        image_ref = images[2]
        position = image_ref.position
        assert position.bounding_rect.x == pytest.approx(50.1, rel=0, abs=0.05)
        assert position.bounding_rect.y == pytest.approx(100.0, rel=0, abs=0.05)


def test_find_image_by_position():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        images = client.find_images(Position.at_page_coordinates(11, 0, 0))
        assert len(images) == 0
        images = client.find_images(Position.at_page_coordinates(11, 55, 310))
        assert len(images) == 1
        assert images[0].internal_id == 'IMAGE_000003'


def test_add_image():
    base_url, token, pdf_path = _require_env_and_fixture('ObviouslyAwesome.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        images = client.find_images(None)
        assert len(images) == 3

        # Prepare image bytes
        img_path = Path(__file__).resolve().parent.parent / 'fixtures' / 'logo-80.png'
        image = Image()
        image.data = img_path.read_bytes()
        pos = Position.at_page_coordinates(6, 50.1, 98.0)

        assert client.add_image(image, pos) is True

        images = client.find_images(None)
        assert len(images) == 4

        images_page6 = client.find_images(Position.at_page(6))
        assert len(images_page6) == 1
        new_image = images_page6[0]
        assert new_image.position.page_index == 6
        assert new_image.internal_id == 'IMAGE_000004'
        assert new_image.position.bounding_rect.x == pytest.approx(50.1, rel=0, abs=0.05)
        assert new_image.position.bounding_rect.y == pytest.approx(98.0, rel=0, abs=0.05)
