from unittest.mock import Mock

import pytest

from pdfdancer.exceptions import HttpClientException
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


def test_clear_path_group_clipping_falls_back_to_one_based_when_backend_requires_it():
    pdf = PDFDancer.__new__(PDFDancer)
    pdf._make_request = Mock()
    pdf._invalidate_snapshots = Mock()

    error_response = Mock()
    error_response.status_code = 400
    error_response.json.return_value = {
        "message": "Page number must be >= 1 (1-based indexing)"
    }
    error_response.text = "Page number must be >= 1 (1-based indexing)"

    success_response = Mock()
    success_response.json.return_value = True

    pdf._make_request.side_effect = [
        HttpClientException("API request failed", response=error_response),
        success_response,
    ]

    assert pdf._clear_path_group_clipping(1, "group-1") is True

    assert pdf._make_request.call_count == 2
    first_call = pdf._make_request.call_args_list[0]
    second_call = pdf._make_request.call_args_list[1]
    assert first_call.kwargs["data"] == {"pageIndex": 0, "groupId": "group-1"}
    assert second_call.kwargs["data"] == {"pageNumber": 1, "groupId": "group-1"}
    assert pdf._clear_path_group_clipping_compat_mode == "page_number_field"

    # Once compatibility mode is detected, subsequent calls use the adjusted payload directly.
    pdf._make_request.reset_mock()
    pdf._make_request.side_effect = None
    pdf._make_request.return_value = success_response
    assert pdf._clear_path_group_clipping(3, "group-1") is True
    pdf._make_request.assert_called_once_with(
        "PUT",
        "/pdf/path-group/clipping/clear",
        data={"pageNumber": 3, "groupId": "group-1"},
    )


def test_clear_path_group_clipping_does_not_fallback_for_unrelated_errors():
    pdf = PDFDancer.__new__(PDFDancer)
    pdf._make_request = Mock()
    pdf._invalidate_snapshots = Mock()

    error_response = Mock()
    error_response.status_code = 400
    error_response.json.return_value = {"message": "Group not found"}
    error_response.text = "Group not found"

    pdf._make_request.side_effect = HttpClientException(
        "API request failed", response=error_response
    )

    with pytest.raises(HttpClientException):
        pdf._clear_path_group_clipping(1, "group-1")

    pdf._make_request.assert_called_once_with(
        "PUT",
        "/pdf/path-group/clipping/clear",
        data={"pageIndex": 0, "groupId": "group-1"},
    )
