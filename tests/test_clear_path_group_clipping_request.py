from unittest.mock import Mock

from pdfdancer.pdfdancer_v1 import PDFDancer


def test_clear_path_group_clipping_uses_one_based_page_number_payload():
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
        data={"pageNumber": 3, "groupId": "group-1"},
    )
    pdf._invalidate_snapshots.assert_called_once()


def test_clear_path_group_clipping_does_not_invalidate_snapshots_when_backend_returns_false():
    pdf = PDFDancer.__new__(PDFDancer)
    pdf._make_request = Mock()
    pdf._invalidate_snapshots = Mock()

    response = Mock()
    response.json.return_value = False
    pdf._make_request.return_value = response

    assert pdf._clear_path_group_clipping(1, "group-1") is False

    pdf._make_request.assert_called_once_with(
        "PUT",
        "/pdf/path-group/clipping/clear",
        data={"pageNumber": 1, "groupId": "group-1"},
    )
    pdf._invalidate_snapshots.assert_not_called()
