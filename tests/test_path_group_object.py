from types import SimpleNamespace
from unittest.mock import Mock

from pdfdancer.types import PathGroupObject


def test_clear_clipping_returns_backend_result():
    client = Mock()
    client._clear_path_group_clipping.return_value = False

    info = SimpleNamespace(
        group_id="group-1",
        path_count=1,
        bounding_box=None,
        x=0.0,
        y=0.0,
    )
    group = PathGroupObject(client, page_index=3, info=info)

    assert group.clear_clipping() is False
    client._clear_path_group_clipping.assert_called_once_with(4, "group-1")
