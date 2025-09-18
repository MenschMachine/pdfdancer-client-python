#!/usr/bin/env python3
"""
Test script to verify error message extraction from API responses.
"""

import json
from unittest.mock import Mock

from pdfdancer.client_v1 import ClientV1


def test_error_extraction():
    """Test error message extraction with sample error response."""
    print("Testing error message extraction...")

    # Create a mock ClientV1 instance
    client = ClientV1.__new__(ClientV1)

    # Sample error response from the issue description
    sample_response_content = b'{"_links":{"self":[{"href":"/pdf/add","templated":false}]},"_embedded":{"errors":[{"message":"Position.x or Position.y is null"}]},"message":"Bad Request"}'

    # Create a mock response
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = sample_response_content.decode('utf-8')
    mock_response.json.return_value = json.loads(sample_response_content)

    # Test the error extraction
    error_message = client._extract_error_message(mock_response)

    expected_message = "Position.x or Position.y is null"
    assert error_message == expected_message, f"Expected '{expected_message}', got '{error_message}'"
    print(f"✓ Extracted error message: '{error_message}'")


def test_multiple_errors():
    """Test error message extraction with multiple errors."""
    print("Testing multiple error messages...")

    client = ClientV1.__new__(ClientV1)

    # Sample response with multiple errors
    sample_data = {
        "_embedded": {
            "errors": [
                {"message": "Position.x or Position.y is null"},
                {"message": "Font size must be positive"},
                {"message": "Text cannot be empty"}
            ]
        },
        "message": "Bad Request"
    }

    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = json.dumps(sample_data)
    mock_response.json.return_value = sample_data

    error_message = client._extract_error_message(mock_response)

    expected_message = "Position.x or Position.y is null; Font size must be positive; Text cannot be empty"
    assert error_message == expected_message, f"Expected '{expected_message}', got '{error_message}'"
    print(f"✓ Extracted multiple error messages: '{error_message}'")


def test_fallback_to_top_level_message():
    """Test fallback to top-level message when no embedded errors."""
    print("Testing fallback to top-level message...")

    client = ClientV1.__new__(ClientV1)

    # Sample response with only top-level message
    sample_data = {
        "message": "Internal Server Error"
    }

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = json.dumps(sample_data)
    mock_response.json.return_value = sample_data

    error_message = client._extract_error_message(mock_response)

    expected_message = "Internal Server Error"
    assert error_message == expected_message, f"Expected '{expected_message}', got '{error_message}'"
    print(f"✓ Fallback to top-level message: '{error_message}'")


def test_json_parse_failure():
    """Test handling of non-JSON responses."""
    print("Testing non-JSON response handling...")

    client = ClientV1.__new__(ClientV1)

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)

    error_message = client._extract_error_message(mock_response)

    expected_message = "Internal Server Error"
    assert error_message == expected_message, f"Expected '{expected_message}', got '{error_message}'"
    print(f"✓ Non-JSON response handled: '{error_message}'")


def test_no_response():
    """Test handling when no response is provided."""
    print("Testing no response handling...")

    client = ClientV1.__new__(ClientV1)

    error_message = client._extract_error_message(None)

    expected_message = "Unknown error"
    assert error_message == expected_message, f"Expected '{expected_message}', got '{error_message}'"
    print(f"✓ No response handled: '{error_message}'")
