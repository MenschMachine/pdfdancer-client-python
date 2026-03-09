from unittest.mock import Mock

from pdfdancer.pdfdancer_v1 import PDFDancer


def test_clear_path_group_clipping_uses_zero_based_page_index_payload():
    pdf = PDFDancer.__new__(PDFDancer)
    pdf._make_request = Mock()
    pdf._invalidate_snapshots = Mock()

    response = Mock()
    response.json.return_value = True
    pdf._make_request.return_value = response

    assert pdf._clear_path_group_clipping(3, "group-1") is True

    pdf._make_request.assert_called_once_with(
        "PUT",
        "/pdf/path-group/clipping/clear",
        data={"pageIndex": 2, "groupId": "group-1"},
    )
    pdf._invalidate_snapshots.assert_called_once()
