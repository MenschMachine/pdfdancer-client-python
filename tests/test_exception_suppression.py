#!/usr/bin/env python3
"""
Test script to verify that exception suppression works correctly.
"""

import traceback

from pdfdancer.client_v1 import ClientV1


def test_exception_suppression():
    """Test that exceptions are properly suppressed and only show the final HttpClientException."""
    print("Testing exception suppression...")

    # Create a mock PDF data
    mock_pdf_data = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<< /Size 1 /Root 1 0 R >>\nstartxref\n0\n%%EOF"

    try:
        # Try to create a client with invalid server URL to trigger exception
        client = ClientV1(
            token="invalid-token",
            pdf_data=mock_pdf_data,
            base_url="http://invalid-server:9999"
        )
        assert False, "Expected exception but got none"

    except Exception as e:
        # Capture the full traceback
        tb_str = traceback.format_exc()

        print("Exception occurred (this is expected):")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print()

        # Check if the traceback contains the suppression indicator
        if "During handling of the above exception, another exception occurred:" in tb_str:
            print("❌ Exception chain was NOT suppressed - still showing nested exceptions")
            print("Full traceback:")
            print(tb_str)
            assert False, "Exception chain was NOT suppressed - still showing nested exceptions"
        else:
            print("✅ Exception chain was successfully suppressed - showing only final exception")

            # Verify we still have the meaningful error message
            if "HttpClientException" in tb_str and (
                    "Failed to create session:" in str(e) or "API request failed:" in str(e)):
                print("✅ Error message preserved correctly")
            else:
                print("❌ Error message not preserved correctly")
                print("Full traceback:")
                print(tb_str)
                assert False, "Error message not preserved correctly"
