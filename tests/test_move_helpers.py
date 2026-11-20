"""
Unit tests for move_to / move_x / move_y on selectable objects (no server needed).
"""

from unittest.mock import Mock

import pytest

from pdfdancer import ObjectRef, ObjectType, Position
from pdfdancer.exceptions import ValidationException
from pdfdancer.models import PathGroupInfo, TextObjectRef
from pdfdancer.types import ImageObject, PathGroupObject, TextLineObject


def _image(client, x=100.0, y=200.0, page=3):
    return ImageObject(
        client, "IMAGE_1", ObjectType.IMAGE, Position.at_page_coordinates(page, x, y)
    )


def _sent_position(client) -> Position:
    return client._move.call_args.args[1]


class TestMoveHelpers:
    def test_move_to_sends_target_with_object_page(self):
        client = Mock()
        client._move.return_value = True
        image = _image(client, page=3)

        assert image.move_to(10, 20) is True

        sent = _sent_position(client)
        assert (sent.page_number, sent.x(), sent.y()) == (3, 10, 20)

    def test_move_x_is_relative_to_current_position(self):
        client = Mock()
        client._move.return_value = True
        image = _image(client, x=100, y=200)

        image.move_x(5)

        sent = _sent_position(client)
        assert (sent.x(), sent.y()) == (105, 200)

    def test_move_y_is_relative_to_current_position(self):
        client = Mock()
        client._move.return_value = True
        image = _image(client, x=100, y=200)

        image.move_y(-15)

        sent = _sent_position(client)
        assert (sent.x(), sent.y()) == (100, 185)

    def test_successive_relative_moves_compose(self):
        client = Mock()
        client._move.return_value = True
        image = _image(client, x=100, y=200)

        image.move_x(20)
        image.move_y(-15)

        sent = _sent_position(client)
        assert (sent.x(), sent.y()) == (120, 185)
        assert (image.position.x(), image.position.y()) == (120, 185)

    def test_failed_move_keeps_local_position(self):
        client = Mock()
        client._move.return_value = False
        image = _image(client, x=100, y=200)

        assert image.move_x(20) is False

        assert (image.position.x(), image.position.y()) == (100, 200)

    def test_move_does_not_mutate_a_position_already_handed_out(self):
        client = Mock()
        client._move.return_value = True
        image = _image(client, x=100, y=200)
        before = image.position

        image.move_x(20)

        assert (before.x(), before.y()) == (100, 200)
        assert (image.position.x(), image.position.y()) == (120, 200)

    def test_move_x_without_position_raises(self):
        client = Mock()
        image = ImageObject(client, "IMAGE_1", ObjectType.IMAGE, Position.at_page(1))

        with pytest.raises(ValidationException, match="has no position"):
            image.move_x(5)
        client._move.assert_not_called()


class TestTextLineObject:
    def test_exposes_text_and_moves(self):
        client = Mock()
        client._move.return_value = True
        ref = TextObjectRef(
            "TEXT_LINE_1",
            Position.at_page_coordinates(1, 72, 700),
            ObjectType.TEXT_LINE,
            text="Hello",
        )

        line = TextLineObject(client, ref)
        line.move_x(10)

        assert line.text == "Hello"
        sent = _sent_position(client)
        assert (sent.x(), sent.y()) == (82, 700)

    def test_plain_object_ref_has_no_text(self):
        line = TextLineObject(
            Mock(),
            ObjectRef("TEXT_LINE_1", Position.at_page(1), ObjectType.TEXT_LINE),
        )

        assert line.text is None


class TestPathGroupMove:
    def _group(self, client):
        info = PathGroupInfo(
            group_id="g1", path_count=2, bounding_box=None, x=50.0, y=60.0
        )
        return PathGroupObject(client, 0, info)

    def test_move_x_and_y_compose(self):
        client = Mock()
        client._move_path_group.return_value = True
        group = self._group(client)

        group.move_x(20)
        group.move_y(-15)

        assert client._move_path_group.call_args_list[0].args == (0, "g1", 70.0, 60.0)
        assert client._move_path_group.call_args_list[1].args == (0, "g1", 70.0, 45.0)
        assert (group.x, group.y) == (70.0, 45.0)

    def test_failed_move_keeps_local_position(self):
        client = Mock()
        client._move_path_group.return_value = False
        group = self._group(client)

        group.move_x(20)

        assert (group.x, group.y) == (50.0, 60.0)
