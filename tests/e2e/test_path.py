import pytest

from pdfdancer import ClientV1, Position, ObjectType
from tests.e2e import _require_env_and_fixture


def test_find_paths():
    base_url, token, pdf_path = _require_env_and_fixture('basic-paths.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        paths = client.find_paths(None)
        assert len(paths) == 9
        assert paths[0].type == ObjectType.PATH

        p1 = paths[0]
        assert p1 is not None
        assert p1.internal_id == 'PATH_000001'
        assert p1.position.bounding_rect.x == pytest.approx(80, rel=0, abs=1)
        assert p1.position.bounding_rect.y == pytest.approx(720, rel=0, abs=1)


def test_find_paths_by_position():
    base_url, token, pdf_path = _require_env_and_fixture('basic-paths.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        paths = client.find_paths(Position.at_page_coordinates(0, 80, 720))
        assert len(paths) == 1
        assert paths[0].internal_id == 'PATH_000001'


def test_delete_path():
    base_url, token, pdf_path = _require_env_and_fixture('basic-paths.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        paths = client.find_paths(Position.at_page_coordinates(0, 80, 720))
        assert len(paths) == 1
        assert paths[0].internal_id == 'PATH_000001'
        assert client.delete(paths[0]) is True
        assert client.find_paths(Position.at_page_coordinates(0, 80, 720)) == []
        assert len(client.find_paths(None)) == 8


def test_move_path():
    base_url, token, pdf_path = _require_env_and_fixture('basic-paths.pdf')
    with ClientV1(token=token, pdf_data=str(pdf_path), base_url=base_url, read_timeout=30.0) as client:
        paths = client.find_paths(Position.at_page_coordinates(0, 80, 720))
        ref = paths[0]
        pos = ref.position
        assert pos.bounding_rect.x == pytest.approx(80, rel=0, abs=1)
        assert pos.bounding_rect.y == pytest.approx(720, rel=0, abs=1)

        assert client.move(ref, Position.at_page_coordinates(0, 50.1, 100)) is True

        assert client.find_paths(Position.at_page_coordinates(0, 80, 720)) == []
        paths = client.find_paths(Position.at_page_coordinates(0, 50.1, 100))
        ref = paths[0]
        pos = ref.position
        assert pos.bounding_rect.x == pytest.approx(50.1, rel=0, abs=0.05)
        assert pos.bounding_rect.y == pytest.approx(100, rel=0, abs=0.05)
