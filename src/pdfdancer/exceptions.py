"""
Exception classes for the PDFDancer Python client.
Mirrors the Java client exception hierarchy.
"""

from typing import Optional

import requests


class PdfDancerException(Exception):
    """
    Base exception for all PDFDancer client errors.
    Equivalent to runtime exceptions in the Java client.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause


class FontNotFoundException(PdfDancerException):
    """
    Exception raised when a required font is not found or available.
    Equivalent to FontNotFoundException in the Java client.
    """

    def __init__(self, message: str):
        super().__init__(f"Font not found: {message}")


class HttpClientException(PdfDancerException):
    """
    Exception raised for HTTP client errors during API communication.
    Wraps requests exceptions and HTTP errors from the API.
    """

    def __init__(self, message: str, response: Optional[requests.Response] = None, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.response = response
        self.status_code = response.status_code if response else None


class SessionException(PdfDancerException):
    """
    Exception raised for session-related errors.
    Occurs when session creation fails or session is invalid.
    """
    pass


class ValidationException(PdfDancerException):
    """
    Exception raised for input validation errors.
    Equivalent to IllegalArgumentException in the Java client.
    """
    pass
