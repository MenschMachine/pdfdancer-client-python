"""
PDFDancer Python Client V1

A Python client that closely mirrors the Java Client class structure and functionality.
Provides session-based PDF manipulation operations with strict validation.
"""

from __future__ import annotations

import gzip
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version as get_package_version
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, List, Mapping, Optional, Union

import httpx
from dotenv import load_dotenv

from . import BezierBuilder, LineBuilder, ParagraphBuilder, PathBuilder
from .exceptions import (
    FontNotFoundException,
    HttpClientException,
    PdfDancerException,
    RateLimitException,
    SessionException,
    ValidationException,
)
from .fingerprint import Fingerprint
from .image_builder import ImageBuilder, ImageOnPageBuilder
from .models import (
    AddPageRequest,
    AddRequest,
    ChangeFormFieldRequest,
    Color,
    CommandResult,
    DeleteRequest,
    DocumentSnapshot,
    FindRequest,
    Font,
    FontRecommendation,
    FontType,
    FormFieldRef,
    Image,
    ModifyRequest,
    ModifyTextRequest,
    MoveRequest,
    ObjectRef,
    ObjectType,
    Orientation,
    PageMoveRequest,
    PageRef,
    PageSize,
    PageSnapshot,
    Paragraph,
    Position,
    PositionMode,
    RedactRequest,
    RedactResponse,
    RedactTarget,
    ShapeType,
    TextLine,
    TextObjectRef,
)
from .page_builder import PageBuilder
from .paragraph_builder import ParagraphPageBuilder
from .types import (
    FormFieldObject,
    FormObject,
    ImageObject,
    ParagraphObject,
    PathObject,
    PDFObjectBase,
    TextLineObject,
)

if TYPE_CHECKING:
    from .models import PathSegment
    from .path_builder import RectangleBuilder

load_dotenv()

# Client identifier header for all HTTP requests
# Always reads from installed package metadata (stays in sync with pyproject.toml)
try:
    CLIENT_HEADER_VALUE = f"python/{get_package_version('pdfdancer-client-python')}"
except Exception:
    # Fallback in case package metadata is not available
    CLIENT_HEADER_VALUE = "python/unknown"

# Global variable to disable SSL certificate verification
# Set to True to skip SSL verification (useful for testing with self-signed certificates)
# WARNING: Only use in development/testing environments
DISABLE_SSL_VERIFY = os.environ.get("PDFDANCER_CLIENT_DISABLE_SSL_VERIFY", False)

DEBUG = os.environ.get("PDFDANCER_CLIENT_DEBUG", False)
DEFAULT_TOLERANCE = 0.01

# Retry configuration for transient network errors
# These settings control automatic retry behavior when encountering transient network errors
# like "Server disconnected without sending a response", connection timeouts, etc.
# HTTP status errors (4xx, 5xx) are NOT retried as they are application-level errors.
#
# PDFDANCER_MAX_RETRIES: Maximum number of retry attempts (default: 3)
#   Example: With max_retries=3, the client will make up to 4 total attempts (1 initial + 3 retries)
#
# PDFDANCER_RETRY_BACKOFF_FACTOR: Base multiplier for exponential backoff delays (default: 1.0)
#   The actual delay for each retry is calculated as: backoff_factor * (2 ** attempt)
#   Examples:
#     - backoff_factor=1.0: delays are 1s, 2s, 4s, 8s, ...
#     - backoff_factor=2.0: delays are 2s, 4s, 8s, 16s, ...
#     - backoff_factor=0.5: delays are 0.5s, 1s, 2s, 4s, ...
DEFAULT_MAX_RETRIES = int(os.environ.get("PDFDANCER_MAX_RETRIES", "3"))
DEFAULT_RETRY_BACKOFF_FACTOR = float(
    os.environ.get("PDFDANCER_RETRY_BACKOFF_FACTOR", "2.0")
)


def _generate_timestamp() -> str:
    """
    Generate a timestamp string in the format expected by the API.
    Format: YYYY-MM-DDTHH:MM:SS.ffffffZ (with microseconds)

    Returns:
        Timestamp string with UTC timezone
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse timestamp string, handling both microseconds and nanoseconds precision.

    Args:
        timestamp_str: Timestamp string in format YYYY-MM-DDTHH:MM:SS.fffffffZ
                      (with 6 or 9 fractional digits)

    Returns:
        datetime object with UTC timezone
    """
    # Remove the 'Z' suffix
    ts = timestamp_str.rstrip("Z")

    # Handle nanoseconds (9 digits) by truncating to microseconds (6 digits)
    # Python's datetime only supports microseconds precision
    if "." in ts:
        date_part, frac_part = ts.rsplit(".", 1)
        if len(frac_part) > 6:
            # Truncate to 6 digits (microseconds)
            frac_part = frac_part[:6]
        ts = f"{date_part}.{frac_part}"

    return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)


def _log_generated_at_header(response: httpx.Response, method: str, path: str) -> None:
    """
    Check for X-Generated-At and X-Received-At headers and log timing information if DEBUG=True.

    Expected timestamp formats:
    - 2025-10-24T08:49:39.161945Z (microseconds - 6 digits)
    - 2025-10-24T08:58:45.468131265Z (nanoseconds - 9 digits)

    Args:
        response: The HTTP response object
        method: HTTP method used
        path: API path
    """
    if not DEBUG:
        return

    generated_at = response.headers.get("X-Generated-At")
    received_at = response.headers.get("X-Received-At")

    if generated_at or received_at:
        try:
            log_parts = []
            current_time = datetime.now(timezone.utc)

            # Parse and log X-Received-At
            received_time = None
            if received_at:
                received_time = _parse_timestamp(received_at)
                time_since_received = (current_time - received_time).total_seconds()
                log_parts.append(
                    f"X-Received-At: {received_at}, time since received: {time_since_received:.3f}s"
                )

            # Parse and log X-Generated-At
            generated_time = None
            if generated_at:
                generated_time = _parse_timestamp(generated_at)
                time_since_generated = (current_time - generated_time).total_seconds()
                log_parts.append(
                    f"X-Generated-At: {generated_at}, time since generated: {time_since_generated:.3f}s"
                )

            # Calculate processing time (X-Generated-At - X-Received-At)
            if received_time and generated_time:
                processing_time = (generated_time - received_time).total_seconds()
                log_parts.append(f"processing time: {processing_time:.3f}s")

            if log_parts:
                print(f"{time.time()}|{method} {path} - {', '.join(log_parts)}")

        except (ValueError, AttributeError) as e:
            print(f"{time.time()}|{method} {path} - Header parse error: {e}")


def _is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable (transient network error).

    Args:
        error: The exception to check

    Returns:
        True if the error is retryable, False otherwise
    """
    # Retryable errors include:
    # - RemoteProtocolError (server disconnected without response)
    # - ConnectError/ConnectTimeout (connection issues)
    # - ReadTimeout (server didn't respond in time)
    # - PoolTimeout (connection pool exhausted)
    error_msg = str(error).lower()

    if isinstance(error, httpx.RemoteProtocolError):
        return True
    if isinstance(error, httpx.ConnectError):
        return True
    if isinstance(error, httpx.ReadTimeout):
        return True
    if isinstance(error, httpx.PoolTimeout):
        return True
    if isinstance(error, httpx.WriteTimeout):
        return True

    # Check for specific error messages that indicate transient issues
    retryable_messages = [
        "server disconnected",
        "connection reset",
        "broken pipe",
        "connection refused",
        "temporarily unavailable",
    ]

    return any(msg in error_msg for msg in retryable_messages)


def _get_retry_after_delay(response: httpx.Response) -> Optional[int]:
    """
    Extract Retry-After delay from response headers.

    Args:
        response: HTTP response with potential Retry-After header

    Returns:
        Delay in seconds, or None if header not present or invalid
    """
    retry_after = response.headers.get("Retry-After")
    if not retry_after:
        return None

    try:
        # Retry-After can be either a number of seconds or an HTTP date
        # Try parsing as integer first (seconds)
        return int(retry_after)
    except ValueError:
        # If not a number, it might be an HTTP date - ignore for now
        # Most rate limiting APIs use seconds
        return None


class PageClient:
    def __init__(
        self,
        page_number: int,
        root: "PDFDancer",
        page_size: Optional[PageSize] = None,
        orientation: Optional[Union[Orientation, str]] = Orientation.PORTRAIT,
    ):
        self.page_number = page_number
        self.root = root
        self.object_type = ObjectType.PAGE
        self.position = Position.at_page(page_number)
        self.internal_id = f"PAGE-{page_number}"
        self.page_size = page_size
        if isinstance(orientation, str):
            normalized = orientation.strip().upper()
            try:
                self.orientation = Orientation(normalized)
            except ValueError:
                self.orientation = normalized
        else:
            self.orientation = orientation

    def select_paths_at(
        self, x: float, y: float, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[PathObject]:
        position = Position.at_page_coordinates(self.page_number, x, y)
        # noinspection PyProtectedMember
        return self.root._to_path_objects(self.root._find_paths(position, tolerance))

    def select_paragraphs(self) -> List[ParagraphObject]:
        # noinspection PyProtectedMember
        return self.root._to_paragraph_objects(
            self.root._find_paragraphs(Position.at_page(self.page_number))
        )

    def select_paragraphs_starting_with(self, text: str) -> List[ParagraphObject]:
        position = Position.at_page(self.page_number)
        position.with_text_starts(text)
        # noinspection PyProtectedMember
        return self.root._to_paragraph_objects(self.root._find_paragraphs(position))

    def select_paragraphs_matching(self, pattern):
        position = Position.at_page(self.page_number)
        position.text_pattern = pattern
        # noinspection PyProtectedMember
        return self.root._to_paragraph_objects(self.root._find_paragraphs(position))

    def select_text_lines_matching(self, pattern: str) -> List[TextLineObject]:
        position = Position.at_page(self.page_number)
        position.text_pattern = pattern
        # noinspection PyProtectedMember
        return self.root._to_textline_objects(self.root._find_text_lines(position))

    def select_paragraphs_at(
        self, x: float, y: float, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[ParagraphObject]:
        position = Position.at_page_coordinates(self.page_number, x, y)
        # noinspection PyProtectedMember
        return self.root._to_paragraph_objects(
            self.root._find_paragraphs(position, tolerance)
        )

    def select_text_lines(self) -> List[TextLineObject]:
        position = Position.at_page(self.page_number)
        # noinspection PyProtectedMember
        return self.root._to_textline_objects(self.root._find_text_lines(position))

    def select_text_lines_starting_with(self, text: str) -> List[TextLineObject]:
        position = Position.at_page(self.page_number)
        position.with_text_starts(text)
        # noinspection PyProtectedMember
        return self.root._to_textline_objects(self.root._find_text_lines(position))

    def select_text_lines_at(
        self, x, y, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[TextLineObject]:
        position = Position.at_page_coordinates(self.page_number, x, y)
        # noinspection PyProtectedMember
        return self.root._to_textline_objects(
            self.root._find_text_lines(position, tolerance)
        )

    def select_images(self) -> List[ImageObject]:
        # noinspection PyProtectedMember
        return self.root._to_image_objects(
            self.root._find_images(Position.at_page(self.page_number))
        )

    def select_images_at(
        self, x: float, y: float, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[ImageObject]:
        position = Position.at_page_coordinates(self.page_number, x, y)
        # noinspection PyProtectedMember
        return self.root._to_image_objects(self.root._find_images(position, tolerance))

    def select_forms(self) -> List[FormObject]:
        position = Position.at_page(self.page_number)
        # noinspection PyProtectedMember
        return self.root._to_form_objects(self.root._find_form_x_objects(position))

    def select_forms_at(
        self, x: float, y: float, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[FormObject]:
        position = Position.at_page_coordinates(self.page_number, x, y)
        # noinspection PyProtectedMember
        return self.root._to_form_objects(
            self.root._find_form_x_objects(position, tolerance)
        )

    def select_form_fields(self) -> List[FormFieldObject]:
        position = Position.at_page(self.page_number)
        # noinspection PyProtectedMember
        return self.root._to_form_field_objects(self.root._find_form_fields(position))

    def select_form_fields_by_name(self, field_name: str) -> List[FormFieldObject]:
        pos = Position.by_name(field_name)
        pos.page_number = self.page_number
        # noinspection PyProtectedMember
        return self.root._to_form_field_objects(self.root._find_form_fields(pos))

    def select_form_fields_at(
        self, x: float, y: float, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[FormFieldObject]:
        position = Position.at_page_coordinates(self.page_number, x, y)
        # noinspection PyProtectedMember
        return self.root._to_form_field_objects(
            self.root._find_form_fields(position, tolerance)
        )

    # Singular selection methods (convenience methods returning first match or None)

    def select_paragraph_at(
        self, x: float, y: float, tolerance: float = DEFAULT_TOLERANCE
    ) -> Optional[ParagraphObject]:
        """
        Select the first paragraph at the specified coordinates.

        Args:
            x: X coordinate in points
            y: Y coordinate in points
            tolerance: Tolerance in points for spatial matching (default: DEFAULT_TOLERANCE)

        Returns:
            First ParagraphObject at the coordinates, or None if no match
        """
        results = self.select_paragraphs_at(x, y, tolerance)
        return results[0] if results else None

    def select_paragraph_starting_with(self, text: str) -> Optional[ParagraphObject]:
        """
        Select the first paragraph starting with the specified text.

        Args:
            text: Text to search for at the start of paragraphs

        Returns:
            First ParagraphObject starting with the text, or None if no match
        """
        results = self.select_paragraphs_starting_with(text)
        return results[0] if results else None

    def select_paragraph_matching(self, pattern: str) -> Optional[ParagraphObject]:
        """
        Select the first paragraph matching the specified regex pattern.

        Args:
            pattern: Regex pattern to match against paragraph text

        Returns:
            First ParagraphObject matching the pattern, or None if no match
        """
        results = self.select_paragraphs_matching(pattern)
        return results[0] if results else None

    def select_text_line_at(
        self, x: float, y: float, tolerance: float = DEFAULT_TOLERANCE
    ) -> Optional[TextLineObject]:
        """
        Select the first text line at the specified coordinates.

        Args:
            x: X coordinate in points
            y: Y coordinate in points
            tolerance: Tolerance in points for spatial matching (default: DEFAULT_TOLERANCE)

        Returns:
            First TextLineObject at the coordinates, or None if no match
        """
        results = self.select_text_lines_at(x, y, tolerance)
        return results[0] if results else None

    def select_text_line_starting_with(self, text: str) -> Optional[TextLineObject]:
        """
        Select the first text line starting with the specified text.

        Args:
            text: Text to search for at the start of text lines

        Returns:
            First TextLineObject starting with the text, or None if no match
        """
        results = self.select_text_lines_starting_with(text)
        return results[0] if results else None

    def select_text_line_matching(self, pattern: str) -> Optional[TextLineObject]:
        """
        Select the first text line matching the specified regex pattern.

        Args:
            pattern: Regex pattern to match against text line text

        Returns:
            First TextLineObject matching the pattern, or None if no match
        """
        results = self.select_text_lines_matching(pattern)
        return results[0] if results else None

    def select_image_at(
        self, x: float, y: float, tolerance: float = DEFAULT_TOLERANCE
    ) -> Optional[ImageObject]:
        """
        Select the first image at the specified coordinates.

        Args:
            x: X coordinate in points
            y: Y coordinate in points
            tolerance: Tolerance in points for spatial matching (default: DEFAULT_TOLERANCE)

        Returns:
            First ImageObject at the coordinates, or None if no match
        """
        results = self.select_images_at(x, y, tolerance)
        return results[0] if results else None

    def select_form_at(
        self, x: float, y: float, tolerance: float = DEFAULT_TOLERANCE
    ) -> Optional[FormObject]:
        """
        Select the first form at the specified coordinates.

        Args:
            x: X coordinate in points
            y: Y coordinate in points
            tolerance: Tolerance in points for spatial matching (default: DEFAULT_TOLERANCE)

        Returns:
            First FormObject at the coordinates, or None if no match
        """
        results = self.select_forms_at(x, y, tolerance)
        return results[0] if results else None

    def select_form_field_at(
        self, x: float, y: float, tolerance: float = DEFAULT_TOLERANCE
    ) -> Optional[FormFieldObject]:
        """
        Select the first form field at the specified coordinates.

        Args:
            x: X coordinate in points
            y: Y coordinate in points
            tolerance: Tolerance in points for spatial matching (default: DEFAULT_TOLERANCE)

        Returns:
            First FormFieldObject at the coordinates, or None if no match
        """
        results = self.select_form_fields_at(x, y, tolerance)
        return results[0] if results else None

    def select_form_field_by_name(self, field_name: str) -> Optional[FormFieldObject]:
        """
        Select the first form field with the specified name.

        Args:
            field_name: Name of the form field to search for

        Returns:
            First FormFieldObject with the specified name, or None if no match
        """
        results = self.select_form_fields_by_name(field_name)
        return results[0] if results else None

    def select_path_at(
        self, x: float, y: float, tolerance: float = DEFAULT_TOLERANCE
    ) -> Optional[PathObject]:
        """
        Select the first path at the specified coordinates.

        Args:
            x: X coordinate in points
            y: Y coordinate in points
            tolerance: Tolerance in points for spatial matching (default: DEFAULT_TOLERANCE)

        Returns:
            First PathObject at the coordinates, or None if no match
        """
        results = self.select_paths_at(x, y, tolerance)
        return results[0] if results else None

    @classmethod
    def from_ref(cls, root: "PDFDancer", page_ref: PageRef) -> "PageClient":
        page_client = PageClient(
            page_number=page_ref.position.page_number,
            root=root,
            page_size=page_ref.page_size,
            orientation=page_ref.orientation,
        )
        page_client.internal_id = page_ref.internal_id
        if page_ref.position is not None:
            page_client.position = page_ref.position
            page_client.page_number = page_ref.position.page_number
        return page_client

    def delete(self) -> bool:
        # noinspection PyProtectedMember
        return self.root._delete_page(self._ref())

    def move_to(self, target_page_number: int) -> bool:
        """Move this page to a different index within the document."""
        if target_page_number is None or target_page_number < 0:
            raise ValidationException(
                f"Target page index must be >= 0, got {target_page_number}"
            )

        # noinspection PyProtectedMember
        moved = self.root._move_page(self.page_number, target_page_number)
        if moved:
            self.page_number = target_page_number
            self.position = Position.at_page(target_page_number)
        return moved

    def _ref(self):
        return ObjectRef(
            internal_id=self.internal_id, position=self.position, type=self.object_type
        )

    def new_paragraph(self) -> ParagraphBuilder:
        return ParagraphPageBuilder(self.root, self.page_number)

    def new_path(self) -> PathBuilder:
        return PathBuilder(self.root, self.page_number)

    def new_image(self) -> ImageOnPageBuilder:
        return ImageOnPageBuilder(self.root, self.page_number)

    def new_line(self) -> LineBuilder:
        return LineBuilder(self.root, self.page_number)

    def new_bezier(self) -> BezierBuilder:
        return BezierBuilder(self.root, self.page_number)

    def new_rectangle(self) -> "RectangleBuilder":
        from .path_builder import RectangleBuilder

        return RectangleBuilder(self.root, self.page_number)

    def select_paths(self):
        # noinspection PyProtectedMember
        return self.root._to_path_objects(
            self.root._find_paths(Position.at_page(self.page_number))
        )

    def select_elements(self):
        """
        Select all elements (paragraphs, images, paths, forms) on this page.

        Returns:
            List of all PDF objects on this page
        """
        result = []
        result.extend(self.select_paragraphs())
        result.extend(self.select_text_lines())
        result.extend(self.select_images())
        result.extend(self.select_paths())
        result.extend(self.select_forms())
        result.extend(self.select_form_fields())
        return result

    @property
    def size(self):
        """Property alias for page size."""
        return self.page_size

    @property
    def page_orientation(self):
        """Property alias for orientation."""
        return self.orientation


class PDFDancer:
    """
    REST API client for interacting with the PDFDancer PDF manipulation service.
    This client provides a convenient Python interface for performing PDF operations
    including session management, object searching, manipulation, and retrieval.
    Handles authentication, session lifecycle, and HTTP communication transparently.
    """

    # --------------------------------------------------------------
    # CLASS METHOD ENTRY POINT
    # --------------------------------------------------------------
    @classmethod
    def open(
        cls,
        pdf_data: Union[bytes, Path, str, BinaryIO],
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_factor: float = DEFAULT_RETRY_BACKOFF_FACTOR,
    ) -> "PDFDancer":
        """
        Create a client session, falling back to environment variables when needed.

        Authentication:
        - If token is provided, uses it
        - Otherwise, checks PDFDANCER_TOKEN environment variable
        - If no token is found, automatically obtains an anonymous token

        Args:
            pdf_data: PDF payload supplied directly or via filesystem handles.
            token: Override for the API token; falls back to `PDFDANCER_TOKEN` environment variable,
                then to anonymous token if not set.
            base_url: Override for the API base URL; falls back to `PDFDANCER_BASE_URL`
                or defaults to `https://api.pdfdancer.com`.
            timeout: HTTP read timeout in seconds.
            max_retries: Maximum number of retry attempts for transient network errors (default: 3).
                With max_retries=3, the client makes up to 4 total attempts (1 initial + 3 retries).
            retry_backoff_factor: Base multiplier for exponential backoff delays (default: 1.0).
                Delay calculation: backoff_factor * (2 ** attempt_number).
                Examples: 1.0 → delays of 1s, 2s, 4s; 2.0 → delays of 2s, 4s, 8s.

        Returns:
            A ready-to-use `PDFDancer` client instance.
        """
        resolved_token = cls._resolve_token(token)
        resolved_base_url = cls._resolve_base_url(base_url)

        # If no token found, obtain anonymous token
        if resolved_token is None:
            resolved_token = cls._obtain_anonymous_token(resolved_base_url, timeout)

        return PDFDancer(
            resolved_token,
            pdf_data,
            resolved_base_url,
            timeout,
            max_retries,
            retry_backoff_factor,
        )

    @classmethod
    def _resolve_base_url(cls, base_url: Optional[str]) -> Optional[str]:
        env_base_url = os.getenv("PDFDANCER_BASE_URL")
        resolved_base_url = base_url or (
            env_base_url.strip() if env_base_url and env_base_url.strip() else None
        )
        if resolved_base_url is None:
            resolved_base_url = "https://api.pdfdancer.com"
        return resolved_base_url

    @classmethod
    def _obtain_anonymous_token(cls, base_url: str, timeout: float = 30.0) -> str:
        """
        Obtain an anonymous token from the /keys/anon endpoint.

        Args:
            base_url: Base URL of the PDFDancer API server
            timeout: HTTP read timeout in seconds

        Returns:
            Anonymous token string

        Raises:
            HttpClientException: If token request fails
            RateLimitException: If rate limit is exceeded
        """
        # Create temporary client without authentication
        temp_client = httpx.Client(http2=True, verify=not DISABLE_SSL_VERIFY)
        max_retries = 3
        retry_backoff_factor = 1.0

        try:
            last_error: Optional[Exception] = None
            attempt = 0

            while attempt <= max_retries:
                try:
                    headers = {
                        "X-Fingerprint": Fingerprint.generate(),
                        "X-PDFDancer-Client": CLIENT_HEADER_VALUE,
                    }

                    response = temp_client.post(
                        cls._cleanup_url_path(base_url, "/keys/anon"),
                        headers=headers,
                        timeout=timeout if timeout > 0 else None,
                    )

                    response.raise_for_status()
                    token_data = response.json()

                    # Extract token from response (matches Java AnonTokenResponse structure)
                    if isinstance(token_data, dict) and "token" in token_data:
                        return token_data["token"]
                    else:
                        raise HttpClientException(
                            "Invalid anonymous token response format"
                        )

                except httpx.HTTPStatusError as e:
                    # Handle 429 (rate limit) with retry
                    if e.response.status_code == 429 and attempt < max_retries:
                        retry_after = _get_retry_after_delay(e.response)
                        if retry_after is not None:
                            delay = retry_after
                        else:
                            # Use exponential backoff if no Retry-After header
                            delay = retry_backoff_factor * (2**attempt)

                        # Always log 429 to stderr for visibility
                        print(
                            f"Rate limit (429) on POST /keys/anon - retrying in {delay}s "
                            f"(attempt {attempt + 1}/{max_retries})",
                            file=sys.stderr,
                        )
                        if DEBUG:
                            print(
                                f"{time.time()}|POST /keys/anon - Rate limit exceeded (429), "
                                f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                            )
                        time.sleep(delay)
                        attempt += 1
                        continue

                    # Raise RateLimitException for 429 after exhausting retries
                    if e.response.status_code == 429:
                        retry_after = _get_retry_after_delay(e.response)
                        print(
                            "Rate limit (429) on POST /keys/anon - max retries exhausted",
                            file=sys.stderr,
                        )
                        raise RateLimitException(
                            "Rate limit exceeded when obtaining anonymous token",
                            retry_after=retry_after,
                            response=e.response,
                        ) from None

                    # Other HTTP status errors
                    raise HttpClientException(
                        f"Failed to obtain anonymous token: HTTP {e.response.status_code}",
                        response=e.response,
                        cause=e,
                    ) from None
                except httpx.RequestError as e:
                    last_error = e
                    raise HttpClientException(
                        f"Failed to obtain anonymous token: {str(e)}",
                        response=None,
                        cause=e,
                    ) from None

            # Should not reach here, but handle just in case
            if last_error:
                raise HttpClientException(
                    f"Failed to obtain anonymous token after {max_retries + 1} attempts: {str(last_error)}",
                    response=None,
                    cause=last_error,
                ) from None
            else:
                raise HttpClientException(
                    f"Failed to obtain anonymous token after {max_retries + 1} attempts",
                    response=None,
                )
        finally:
            temp_client.close()

    @classmethod
    def _resolve_token(cls, token: Optional[str]) -> Optional[str]:
        """
        Resolve token from argument or environment variable.
        Returns None if no token is found (allowing fallback to anonymous token).
        """
        resolved_token = token.strip() if token and token.strip() else None
        if resolved_token is None:
            env_token = os.getenv("PDFDANCER_TOKEN")
            resolved_token = (
                env_token.strip() if env_token and env_token.strip() else None
            )
        return resolved_token

    @classmethod
    def new(
        cls,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        page_size: Optional[Union[PageSize, str, Mapping[str, Any]]] = None,
        orientation: Optional[Union[Orientation, str]] = None,
        initial_page_count: int = 1,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_factor: float = DEFAULT_RETRY_BACKOFF_FACTOR,
    ) -> "PDFDancer":
        """
        Create a new blank PDF document with optional configuration.

        Authentication:
        - If token is provided, uses it
        - Otherwise, checks PDFDANCER_TOKEN environment variable
        - If no token is found, automatically obtains an anonymous token

        Args:
            token: Override for the API token; falls back to `PDFDANCER_TOKEN` environment variable,
                then to anonymous token if not set.
            base_url: Override for the API base URL; falls back to `PDFDANCER_BASE_URL`
                or defaults to `https://api.pdfdancer.com`.
            timeout: HTTP read timeout in seconds.
            page_size: Page size for the PDF (default: A4). Accepts `PageSize`, a standard name string, or a
                mapping with `width`/`height` values.
            orientation: Page orientation (default: PORTRAIT). Can be Orientation enum or string.
            initial_page_count: Number of initial blank pages (default: 1).
            max_retries: Maximum number of retry attempts for transient network errors (default: 3).
                With max_retries=3, the client makes up to 4 total attempts (1 initial + 3 retries).
            retry_backoff_factor: Base multiplier for exponential backoff delays (default: 1.0).
                Delay calculation: backoff_factor * (2 ** attempt_number).
                Examples: 1.0 → delays of 1s, 2s, 4s; 2.0 → delays of 2s, 4s, 8s.

        Returns:
            A ready-to-use `PDFDancer` client instance with a blank PDF.
        """
        resolved_token = cls._resolve_token(token)
        resolved_base_url = cls._resolve_base_url(base_url)

        # If no token found, obtain anonymous token
        if resolved_token is None:
            resolved_token = cls._obtain_anonymous_token(resolved_base_url, timeout)

        # Create a new instance that will call _create_blank_pdf_session
        instance = object.__new__(cls)

        # Initialize instance variables
        if not resolved_token or not resolved_token.strip():
            raise ValidationException("Authentication token cannot be null or empty")

        instance._token = resolved_token.strip()
        instance._base_url = resolved_base_url.rstrip("/")
        instance._read_timeout = timeout
        instance._max_retries = max_retries
        instance._retry_backoff_factor = retry_backoff_factor

        # Create HTTP client for connection reuse with HTTP/2 support
        instance._client = httpx.Client(
            http2=True,
            headers={
                "Authorization": f"Bearer {instance._token}",
                "X-PDFDancer-Client": CLIENT_HEADER_VALUE,
            },
            verify=not DISABLE_SSL_VERIFY,
        )

        # Create blank PDF session
        instance._session_id = instance._create_blank_pdf_session(
            page_size=page_size,
            orientation=orientation,
            initial_page_count=initial_page_count,
        )

        # Set pdf_bytes to None since we don't have the PDF bytes yet
        instance._pdf_bytes = None

        # Initialize snapshot caches (lazy-loaded)
        instance._document_snapshot = None
        instance._page_snapshots = {}

        return instance

    def __init__(
        self,
        token: str,
        pdf_data: Union[bytes, Path, str, BinaryIO],
        base_url: str,
        read_timeout: float = 0,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_factor: float = DEFAULT_RETRY_BACKOFF_FACTOR,
    ):
        """
        Creates a new client with PDF data.
        This constructor initializes the client, uploads the PDF data to create
        a new session, and prepares the client for PDF manipulation operations.

        Args:
            token: Authentication token for API access
            pdf_data: PDF file data as bytes, Path, filename string, or file-like object
            base_url: Base URL of the PDFDancer API server
            read_timeout: Timeout in seconds for HTTP requests (default: 30.0)
            max_retries: Maximum number of retry attempts for transient network errors (default: 3).
                With max_retries=3, the client makes up to 4 total attempts (1 initial + 3 retries).
            retry_backoff_factor: Base multiplier for exponential backoff delays (default: 1.0).
                Delay calculation: backoff_factor * (2 ** attempt_number).
                Examples: 1.0 → delays of 1s, 2s, 4s; 2.0 → delays of 2s, 4s, 8s.

        Raises:
            ValidationException: If token is empty or PDF data is invalid
            SessionException: If session creation fails
            HttpClientException: If HTTP communication fails
        """
        # Strict validation like Java client
        if not token or not token.strip():
            raise ValidationException("Authentication token cannot be null or empty")

        self._token = token.strip()
        self._base_url = base_url.rstrip("/")
        self._read_timeout = read_timeout
        self._max_retries = max_retries
        self._retry_backoff_factor = retry_backoff_factor

        # Process PDF data with validation
        self._pdf_bytes = self._process_pdf_data(pdf_data)

        # Create HTTP client for connection reuse with HTTP/2 support
        self._client = httpx.Client(
            http2=True,
            headers={
                "Authorization": f"Bearer {self._token}",
                "X-PDFDancer-Client": CLIENT_HEADER_VALUE,
            },
            verify=not DISABLE_SSL_VERIFY,
        )

        # Create session - equivalent to Java constructor behavior
        self._session_id = self._create_session()

        # Initialize snapshot caches (lazy-loaded)
        self._document_snapshot: Optional[DocumentSnapshot] = None
        self._page_snapshots: dict[int, PageSnapshot] = {}

    @staticmethod
    def _process_pdf_data(pdf_data: Union[bytes, Path, str, BinaryIO]) -> bytes:
        """
        Process PDF data from various input types with strict validation.
        """
        if pdf_data is None:
            raise ValidationException("PDF data cannot be null")

        try:
            if isinstance(pdf_data, bytes):
                if len(pdf_data) == 0:
                    raise ValidationException("PDF data cannot be empty")
                return pdf_data

            elif isinstance(pdf_data, (Path, str)):
                file_path = Path(pdf_data)
                if not file_path.exists():
                    raise ValidationException(f"PDF file does not exist: {file_path}")
                if not file_path.is_file():
                    raise ValidationException(f"Path is not a file: {file_path}")
                if not file_path.stat().st_size > 0:
                    raise ValidationException(f"PDF file is empty: {file_path}")

                with open(file_path, "rb") as f:
                    return f.read()

            elif hasattr(pdf_data, "read"):
                # File-like object
                data = pdf_data.read()
                if isinstance(data, str):
                    data = data.encode("utf-8")
                if len(data) == 0:
                    raise ValidationException("PDF data from file-like object is empty")
                return data

            else:
                raise ValidationException(
                    f"Unsupported PDF data type: {type(pdf_data)}"
                )

        except (IOError, OSError) as e:
            raise PdfDancerException(f"Failed to read PDF data: {e}", cause=e)

    def _extract_error_message(self, response: Optional[httpx.Response]) -> str:
        """
        Extract meaningful error messages from API response.
        Parses JSON error responses with _embedded.errors structure.
        """
        if response is None:
            return "Unknown error"

        try:
            # Try to parse JSON response
            error_data = response.json()

            # Check for embedded errors structure
            if "_embedded" in error_data and "errors" in error_data["_embedded"]:
                errors = error_data["_embedded"]["errors"]
                if errors and isinstance(errors, list):
                    # Extract all error messages
                    messages = []
                    for error in errors:
                        if isinstance(error, dict) and "message" in error:
                            messages.append(error["message"])

                    if messages:
                        return "; ".join(messages)

            # Check for top-level message
            if "message" in error_data:
                return error_data["message"]

            # Fallback to response content
            return response.text or f"HTTP {response.status_code}"

        except (json.JSONDecodeError, KeyError, TypeError):
            # If JSON parsing fails, return response content or status
            return response.text or f"HTTP {response.status_code}"

    def _handle_authentication_error(self, response: Optional[httpx.Response]) -> None:
        """
        Translate authentication failures into a clear, actionable validation error.
        """
        if response is None:
            return

        if response.status_code in (401, 403):
            details = self._extract_error_message(response)
            raise ValidationException(
                "Authentication with the PDFDancer API failed. "
                "Confirm that your API token is valid, has not expired, and is supplied via "
                "the `token` argument or the PDFDANCER_TOKEN environment variable. "
                f"Server response: {details}"
            )

    @staticmethod
    def _cleanup_url_path(base_url: str, path: str) -> str:
        """
        Combine base_url and path, ensuring no double slashes.

        Args:
            base_url: Base URL (may or may not have trailing slash)
            path: Path segment (may or may not have leading slash)

        Returns:
            Combined URL with no double slashes
        """
        base = base_url.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}"

    def _create_session(self) -> str:
        """
        Creates a new PDF processing session by uploading the PDF data.
        """
        import uuid

        last_error: Optional[Exception] = None
        attempt = 0

        while attempt <= self._max_retries:
            try:
                # Build multipart body manually to avoid base64 encoding and enable compression
                # httpx by default may add Content-Transfer-Encoding: base64 which the server rejects
                boundary = uuid.uuid4().hex

                # Build multipart body with binary (not base64) encoding
                body_parts = []
                body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
                body_parts.append(
                    b'Content-Disposition: form-data; name="pdf"; filename="document.pdf"\r\n'
                )
                body_parts.append(b"Content-Type: application/pdf\r\n")
                body_parts.append(
                    b"\r\n"
                )  # End of headers, no Content-Transfer-Encoding
                body_parts.append(self._pdf_bytes)
                body_parts.append(b"\r\n")
                body_parts.append(f"--{boundary}--\r\n".encode("utf-8"))

                uncompressed_body = b"".join(body_parts)

                # Compress entire request body using gzip
                compressed_body = gzip.compress(uncompressed_body)

                original_size = len(uncompressed_body)
                compressed_size = len(compressed_body)
                compression_ratio = (
                    (1 - compressed_size / original_size) * 100
                    if original_size > 0
                    else 0
                )

                if DEBUG:
                    retry_info = (
                        f" (attempt {attempt + 1}/{self._max_retries + 1})"
                        if attempt > 0
                        else ""
                    )
                    print(
                        f"{time.time()}|POST /session/create{retry_info} - original size: {original_size} bytes, "
                        f"compressed size: {compressed_size} bytes, "
                        f"compression: {compression_ratio:.1f}%"
                    )

                headers = {
                    "X-Generated-At": _generate_timestamp(),
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Content-Encoding": "gzip",
                }

                response = self._client.post(
                    self._cleanup_url_path(self._base_url, "/session/create"),
                    content=compressed_body,
                    headers=headers,
                    timeout=self._read_timeout if self._read_timeout > 0 else None,
                )

                response_size = len(response.content)
                if DEBUG:
                    print(
                        f"{time.time()}|POST /session/create - response size: {response_size} bytes"
                    )

                _log_generated_at_header(response, "POST", "/session/create")
                self._handle_authentication_error(response)
                response.raise_for_status()
                session_id = response.text.strip()

                if not session_id:
                    raise SessionException("Server returned empty session ID")

                return session_id

            except httpx.HTTPStatusError as e:
                # Handle 429 (rate limit) with retry
                if e.response.status_code == 429 and attempt < self._max_retries:
                    retry_after = _get_retry_after_delay(e.response)
                    if retry_after is not None:
                        delay = retry_after
                    else:
                        # Use exponential backoff if no Retry-After header
                        delay = self._retry_backoff_factor * (2**attempt)

                    # Always log 429 to stderr for visibility
                    print(
                        f"Rate limit (429) on POST /session/create - retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self._max_retries})",
                        file=sys.stderr,
                    )
                    if DEBUG:
                        print(
                            f"{time.time()}|POST /session/create - Rate limit exceeded (429), "
                            f"retrying in {delay}s (attempt {attempt + 1}/{self._max_retries})"
                        )
                    time.sleep(delay)
                    attempt += 1
                    continue

                # Other HTTP status errors are not retried (these are application-level errors)
                self._handle_authentication_error(e.response)
                error_message = self._extract_error_message(e.response)

                # Raise RateLimitException for 429 after exhausting retries
                if e.response.status_code == 429:
                    retry_after = _get_retry_after_delay(e.response)
                    print(
                        "Rate limit (429) on POST /session/create - max retries exhausted",
                        file=sys.stderr,
                    )
                    raise RateLimitException(
                        f"Rate limit exceeded: {error_message}",
                        retry_after=retry_after,
                        response=e.response,
                    ) from None

                raise HttpClientException(
                    f"Failed to create session: {error_message}",
                    response=e.response,
                    cause=e,
                ) from None
            except httpx.RequestError as e:
                last_error = e

                # Check if this is a retryable error
                if _is_retryable_error(e) and attempt < self._max_retries:
                    # Calculate exponential backoff delay
                    delay = self._retry_backoff_factor * (2**attempt)
                    if DEBUG:
                        print(
                            f"{time.time()}|POST /session/create - Retryable error: {str(e)}, "
                            f"retrying in {delay}s (attempt {attempt + 1}/{self._max_retries})"
                        )
                    time.sleep(delay)
                    attempt += 1
                    continue
                else:
                    # Non-retryable error or exhausted retries
                    raise HttpClientException(
                        f"Failed to create session: {str(e)}", response=None, cause=e
                    ) from None

        # Should not reach here, but handle just in case
        if last_error:
            raise HttpClientException(
                f"Failed to create session after {self._max_retries + 1} attempts: {str(last_error)}",
                response=None,
                cause=last_error,
            ) from None
        else:
            raise HttpClientException(
                f"Failed to create session after {self._max_retries + 1} attempts",
                response=None,
            )

    def _create_blank_pdf_session(
        self,
        page_size: Optional[Union[PageSize, str, Mapping[str, Any]]] = None,
        orientation: Optional[Union[Orientation, str]] = None,
        initial_page_count: int = 1,
    ) -> str:
        """
        Creates a new PDF processing session with a blank PDF document.

        Args:
            page_size: Page size (default: A4). Accepts `PageSize`, a standard name string, or a
                mapping with `width`/`height` values.
            orientation: Page orientation (default: PORTRAIT). Can be Orientation enum or string.
            initial_page_count: Number of initial pages (default: 1)

        Returns:
            Session ID for the newly created blank PDF

        Raises:
            SessionException: If session creation fails
            HttpClientException: If HTTP communication fails
        """
        # Build request payload (outside retry loop since validation should only happen once)
        request_data = {}

        # Handle page_size - convert to type-safe object with dimensions
        if page_size is not None:
            try:
                request_data["pageSize"] = PageSize.coerce(page_size).to_dict()
            except ValueError as exc:
                raise ValidationException(str(exc)) from exc
            except TypeError:
                raise ValidationException(f"Invalid page_size type: {type(page_size)}")

        # Handle orientation
        if orientation is not None:
            if isinstance(orientation, Orientation):
                request_data["orientation"] = orientation.value
            elif isinstance(orientation, str):
                request_data["orientation"] = orientation
            else:
                raise ValidationException(
                    f"Invalid orientation type: {type(orientation)}"
                )

        # Handle initial_page_count with validation
        if initial_page_count < 1:
            raise ValidationException(
                f"Initial page count must be at least 1, got {initial_page_count}"
            )
        request_data["initialPageCount"] = initial_page_count

        last_error: Optional[Exception] = None
        attempt = 0

        while attempt <= self._max_retries:
            try:
                request_body = json.dumps(request_data)
                request_size = len(request_body.encode("utf-8"))
                if DEBUG:
                    retry_info = (
                        f" (attempt {attempt + 1}/{self._max_retries + 1})"
                        if attempt > 0
                        else ""
                    )
                    print(
                        f"{time.time()}|POST /session/new{retry_info} - request size: {request_size} bytes"
                    )

                headers = {
                    "Content-Type": "application/json",
                    "X-Generated-At": _generate_timestamp(),
                }
                response = self._client.post(
                    self._cleanup_url_path(self._base_url, "/session/new"),
                    json=request_data,
                    headers=headers,
                    timeout=self._read_timeout if self._read_timeout > 0 else None,
                )

                response_size = len(response.content)
                if DEBUG:
                    print(
                        f"{time.time()}|POST /session/new - response size: {response_size} bytes"
                    )

                _log_generated_at_header(response, "POST", "/session/new")
                self._handle_authentication_error(response)
                response.raise_for_status()
                session_id = response.text.strip()

                if not session_id:
                    raise SessionException("Server returned empty session ID")

                return session_id

            except httpx.HTTPStatusError as e:
                # Handle 429 (rate limit) with retry
                if e.response.status_code == 429 and attempt < self._max_retries:
                    retry_after = _get_retry_after_delay(e.response)
                    if retry_after is not None:
                        delay = retry_after
                    else:
                        # Use exponential backoff if no Retry-After header
                        delay = self._retry_backoff_factor * (2**attempt)

                    # Always log 429 to stderr for visibility
                    print(
                        f"Rate limit (429) on POST /session/new - retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self._max_retries})",
                        file=sys.stderr,
                    )
                    if DEBUG:
                        print(
                            f"{time.time()}|POST /session/new - Rate limit exceeded (429), "
                            f"retrying in {delay}s (attempt {attempt + 1}/{self._max_retries})"
                        )
                    time.sleep(delay)
                    attempt += 1
                    continue

                # Other HTTP status errors are not retried (these are application-level errors)
                self._handle_authentication_error(e.response)
                error_message = self._extract_error_message(e.response)

                # Raise RateLimitException for 429 after exhausting retries
                if e.response.status_code == 429:
                    retry_after = _get_retry_after_delay(e.response)
                    print(
                        "Rate limit (429) on POST /session/new - max retries exhausted",
                        file=sys.stderr,
                    )
                    raise RateLimitException(
                        f"Rate limit exceeded: {error_message}",
                        retry_after=retry_after,
                        response=e.response,
                    ) from None

                raise HttpClientException(
                    f"Failed to create blank PDF session: {error_message}",
                    response=e.response,
                    cause=e,
                ) from None
            except httpx.RequestError as e:
                last_error = e

                # Check if this is a retryable error
                if _is_retryable_error(e) and attempt < self._max_retries:
                    # Calculate exponential backoff delay
                    delay = self._retry_backoff_factor * (2**attempt)
                    if DEBUG:
                        print(
                            f"{time.time()}|POST /session/new - Retryable error: {str(e)}, "
                            f"retrying in {delay}s (attempt {attempt + 1}/{self._max_retries})"
                        )
                    time.sleep(delay)
                    attempt += 1
                    continue
                else:
                    # Non-retryable error or exhausted retries
                    raise HttpClientException(
                        f"Failed to create blank PDF session: {str(e)}",
                        response=None,
                        cause=e,
                    ) from None

        # Should not reach here, but handle just in case
        if last_error:
            raise HttpClientException(
                f"Failed to create blank PDF session after {self._max_retries + 1} attempts: {str(last_error)}",
                response=None,
                cause=last_error,
            ) from None
        else:
            raise HttpClientException(
                f"Failed to create blank PDF session after {self._max_retries + 1} attempts",
                response=None,
            )

    def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> httpx.Response:
        """
        Make HTTP request with session headers, error handling, and automatic retry for transient errors.
        """
        headers = {
            "X-Session-Id": self._session_id,
            "Content-Type": "application/json",
            "X-Generated-At": _generate_timestamp(),
            "X-Fingerprint": Fingerprint.generate(),
            "X-API-VERSION": "1",
        }

        last_error: Optional[Exception] = None
        attempt = 0

        while attempt <= self._max_retries:
            try:
                request_size = 0
                if data is not None:
                    request_body = json.dumps(data)
                    request_size = len(request_body.encode("utf-8"))
                if DEBUG:
                    retry_info = (
                        f" (attempt {attempt + 1}/{self._max_retries + 1})"
                        if attempt > 0
                        else ""
                    )
                    print(
                        f"{time.time()}|{method} {path}{retry_info} - request size: {request_size} bytes"
                    )

                response = self._client.request(
                    method=method,
                    url=self._cleanup_url_path(self._base_url, path),
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=self._read_timeout if self._read_timeout > 0 else None,
                )

                response_size = len(response.content)
                if DEBUG:
                    print(
                        f"{time.time()}|{method} {path} - response size: {response_size} bytes"
                    )

                _log_generated_at_header(response, method, path)

                # Handle FontNotFoundException
                if response.status_code == 404:
                    try:
                        error_data = response.json()
                        if error_data.get("error") == "FontNotFoundException":
                            raise FontNotFoundException(
                                error_data.get("message", "Font not found")
                            )
                    except (json.JSONDecodeError, KeyError):
                        pass

                self._handle_authentication_error(response)
                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                # Handle 429 (rate limit) with retry
                if e.response.status_code == 429 and attempt < self._max_retries:
                    retry_after = _get_retry_after_delay(e.response)
                    if retry_after is not None:
                        delay = retry_after
                    else:
                        # Use exponential backoff if no Retry-After header
                        delay = self._retry_backoff_factor * (2**attempt)

                    # Always log 429 to stderr for visibility
                    print(
                        f"Rate limit (429) on {method} {path} - retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self._max_retries})",
                        file=sys.stderr,
                    )
                    if DEBUG:
                        print(
                            f"{time.time()}|{method} {path} - Rate limit exceeded (429), "
                            f"retrying in {delay}s (attempt {attempt + 1}/{self._max_retries})"
                        )
                    time.sleep(delay)
                    attempt += 1
                    continue

                # Other HTTP status errors are not retried (these are application-level errors)
                self._handle_authentication_error(e.response)
                error_message = self._extract_error_message(e.response)

                # Raise RateLimitException for 429 after exhausting retries
                if e.response.status_code == 429:
                    retry_after = _get_retry_after_delay(e.response)
                    print(
                        f"Rate limit (429) on {method} {path} - max retries exhausted",
                        file=sys.stderr,
                    )
                    raise RateLimitException(
                        f"Rate limit exceeded: {error_message}",
                        retry_after=retry_after,
                        response=e.response,
                    ) from None

                raise HttpClientException(
                    f"API request failed: {error_message}", response=e.response, cause=e
                ) from None
            except httpx.RequestError as e:
                last_error = e

                # Check if this is a retryable error
                if _is_retryable_error(e) and attempt < self._max_retries:
                    # Calculate exponential backoff delay
                    delay = self._retry_backoff_factor * (2**attempt)
                    if DEBUG:
                        print(
                            f"{time.time()}|{method} {path} - Retryable error: {str(e)}, "
                            f"retrying in {delay}s (attempt {attempt + 1}/{self._max_retries})"
                        )
                    time.sleep(delay)
                    attempt += 1
                    continue
                else:
                    # Non-retryable error or exhausted retries
                    raise HttpClientException(
                        f"API request failed: {str(e)}", response=None, cause=e
                    ) from None

        # Should not reach here, but handle just in case
        if last_error:
            raise HttpClientException(
                f"API request failed after {self._max_retries + 1} attempts: {str(last_error)}",
                response=None,
                cause=last_error,
            ) from None
        else:
            raise HttpClientException(
                f"API request failed after {self._max_retries + 1} attempts",
                response=None,
            )

    def _find(
        self,
        object_type: Optional[ObjectType] = None,
        position: Optional[Position] = None,
        tolerance: float = DEFAULT_TOLERANCE,
    ) -> List[ObjectRef]:
        """
        Searches for PDF objects matching the specified criteria.
        Uses snapshot cache for all queries except paths at specific coordinates.

        Args:
            object_type: The type of objects to find (None for all types)
            position: Positional constraints for the search (None for all positions)
            tolerance: Tolerance in points for spatial matching (default: DEFAULT_TOLERANCE)

        Returns:
            List of object references matching the search criteria
        """
        # Special case: PATH queries with bounding_rect need API (full vector data)
        if object_type == ObjectType.PATH and position and position.bounding_rect:
            request_data = FindRequest(object_type, position).to_dict()
            response = self._make_request("POST", "/pdf/find", data=request_data)
            objects_data = response.json()
            return [self._parse_object_ref(obj_data) for obj_data in objects_data]

        # Use snapshot for all other queries
        if position and position.page_number is not None:
            snapshot = self._get_or_fetch_page_snapshot(position.page_number)
            return self._filter_snapshot_elements(
                snapshot.elements, object_type, position, tolerance
            )
        else:
            snapshot = self._get_or_fetch_document_snapshot()
            all_elements = []
            for page_snap in snapshot.pages:
                all_elements.extend(page_snap.elements)
            return self._filter_snapshot_elements(
                all_elements, object_type, position, tolerance
            )

    def select_paragraphs(self) -> List[ParagraphObject]:
        """
        Searches for paragraph objects returning ParagraphObject instances.
        """
        return self._to_paragraph_objects(self._find_paragraphs(None))

    def select_paragraphs_matching(self, pattern: str) -> List[ParagraphObject]:
        """
        Searches for paragraph objects matching a regex pattern.

        Args:
            pattern: Regex pattern to match against paragraph text

        Returns:
            List of ParagraphObject instances matching the pattern
        """
        position = Position()
        position.text_pattern = pattern
        return self._to_paragraph_objects(self._find_paragraphs(position))

    def select_paragraph_matching(self, pattern: str) -> Optional[ParagraphObject]:
        """
        Select the first paragraph matching the specified regex pattern.

        Args:
            pattern: Regex pattern to match against paragraph text

        Returns:
            First ParagraphObject matching the pattern, or None if no match
        """
        results = self.select_paragraphs_matching(pattern)
        return results[0] if results else None

    def _find_paragraphs(
        self, position: Optional[Position] = None, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[TextObjectRef]:
        """
        Searches for paragraph objects returning TextObjectRef with hierarchical structure.
        Uses snapshot cache for all queries.
        """
        # Use snapshot for all queries (including spatial)
        if position and position.page_number is not None:
            snapshot = self._get_or_fetch_page_snapshot(position.page_number)
            return self._filter_snapshot_elements(
                snapshot.elements, ObjectType.PARAGRAPH, position, tolerance
            )
        else:
            snapshot = self._get_or_fetch_document_snapshot()
            all_elements = []
            for page_snap in snapshot.pages:
                all_elements.extend(page_snap.elements)
            return self._filter_snapshot_elements(
                all_elements, ObjectType.PARAGRAPH, position, tolerance
            )

    def _find_images(
        self, position: Optional[Position] = None, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[ObjectRef]:
        """
        Searches for image objects at the specified position.
        Uses snapshot cache for all queries.
        """
        # Use snapshot for all queries (including spatial)
        if position and position.page_number is not None:
            snapshot = self._get_or_fetch_page_snapshot(position.page_number)
            return self._filter_snapshot_elements(
                snapshot.elements, ObjectType.IMAGE, position, tolerance
            )
        else:
            snapshot = self._get_or_fetch_document_snapshot()
            all_elements = []
            for page_snap in snapshot.pages:
                all_elements.extend(page_snap.elements)
            return self._filter_snapshot_elements(
                all_elements, ObjectType.IMAGE, position, tolerance
            )

    def select_images(self) -> List[ImageObject]:
        """
        Searches for image objects in the whole document
        """
        return self._to_image_objects(self._find(ObjectType.IMAGE, None))

    def select_forms(self) -> List[FormObject]:
        """
        Searches for form field objects in the whole document.
        """
        return self._to_form_objects(self._find(ObjectType.FORM_X_OBJECT, None))

    def _find_form_x_objects(
        self, position: Optional[Position] = None, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[ObjectRef]:
        """
        Searches for form X objects at the specified position.
        Uses snapshot cache for all queries.
        """
        # Use snapshot for all queries (including spatial)
        if position and position.page_number is not None:
            snapshot = self._get_or_fetch_page_snapshot(position.page_number)
            return self._filter_snapshot_elements(
                snapshot.elements, ObjectType.FORM_X_OBJECT, position, tolerance
            )
        else:
            snapshot = self._get_or_fetch_document_snapshot()
            all_elements = []
            for page_snap in snapshot.pages:
                all_elements.extend(page_snap.elements)
            return self._filter_snapshot_elements(
                all_elements, ObjectType.FORM_X_OBJECT, position, tolerance
            )

    def select_form_fields(self) -> List[FormFieldObject]:
        """
        Searches for form field objects in the whole document.
        """
        return self._to_form_field_objects(self._find_form_fields(None))

    def select_form_fields_by_name(self, field_name: str) -> List[FormFieldObject]:
        """
        Searches for form field objects in the whole document.
        """
        return self._to_form_field_objects(
            self._find_form_fields(Position.by_name(field_name))
        )

    def select_form_field_by_name(self, field_name: str) -> Optional[FormFieldObject]:
        """
        Select the first form field with the specified name.

        Args:
            field_name: Name of the form field to search for

        Returns:
            First FormFieldObject with the specified name, or None if no match
        """
        results = self.select_form_fields_by_name(field_name)
        return results[0] if results else None

    def _find_form_fields(
        self, position: Optional[Position] = None, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[FormFieldRef]:
        """
        Searches for form fields at the specified position.
        Returns FormFieldRef objects with name and value properties.
        Uses snapshot cache for all queries (including name and spatial filtering).
        """
        # Use snapshot for all queries (including name and spatial)
        if position and position.page_number is not None:
            snapshot = self._get_or_fetch_page_snapshot(position.page_number)
            return self._filter_snapshot_elements(
                snapshot.elements, ObjectType.FORM_FIELD, position, tolerance
            )
        else:
            snapshot = self._get_or_fetch_document_snapshot()
            all_elements = []
            for page_snap in snapshot.pages:
                all_elements.extend(page_snap.elements)
            return self._filter_snapshot_elements(
                all_elements, ObjectType.FORM_FIELD, position, tolerance
            )

    def _change_form_field(self, form_field_ref: FormFieldRef, new_value: str) -> bool:
        """
        Changes the value of a form field.
        """
        if form_field_ref is None:
            raise ValidationException("Form field reference cannot be null")

        try:
            request_data = ChangeFormFieldRequest(form_field_ref, new_value).to_dict()
            response = self._make_request(
                "PUT", "/pdf/modify/formField", data=request_data
            )
            return response.json()
        finally:
            self._invalidate_snapshots()

    def select_paths(self) -> List[ObjectRef]:
        """
        Searches for vector path objects at the specified position.
        """
        return self._find(ObjectType.PATH, None)

    def _find_paths(
        self, position: Optional[Position] = None, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[ObjectRef]:
        """
        Searches for vector path objects at the specified position.
        Note: Spatial queries (with bounding_rect) fall back to API since snapshots
        don't include full vector path data needed for precise intersection tests.
        """
        # Special case: paths at specific coordinates need full vector data
        # which is not available in snapshots, so pass through to API
        if position and position.bounding_rect:
            return self._find(ObjectType.PATH, position, tolerance)

        # For simple page-level "all paths" queries, use snapshot
        if position and position.page_number is not None:
            snapshot = self._get_or_fetch_page_snapshot(position.page_number)
            return self._filter_snapshot_elements(
                snapshot.elements, ObjectType.PATH, position, tolerance
            )
        else:
            # Document-level query - use document snapshot
            snapshot = self._get_or_fetch_document_snapshot()
            all_elements = []
            for page_snap in snapshot.pages:
                all_elements.extend(page_snap.elements)
            return self._filter_snapshot_elements(
                all_elements, ObjectType.PATH, position, tolerance
            )

    def _find_text_lines(
        self, position: Optional[Position] = None, tolerance: float = DEFAULT_TOLERANCE
    ) -> List[TextObjectRef]:
        """
        Searches for text line objects returning TextObjectRef with hierarchical structure.
        Uses snapshot cache for all queries.
        """
        # Use snapshot for all queries (including spatial)
        if position and position.page_number is not None:
            snapshot = self._get_or_fetch_page_snapshot(position.page_number)
            return self._filter_snapshot_elements(
                snapshot.elements, ObjectType.TEXT_LINE, position, tolerance
            )
        else:
            snapshot = self._get_or_fetch_document_snapshot()
            all_elements = []
            for page_snap in snapshot.pages:
                all_elements.extend(page_snap.elements)
            return self._filter_snapshot_elements(
                all_elements, ObjectType.TEXT_LINE, position, tolerance
            )

    def select_text_lines(self) -> List[TextLineObject]:
        """
        Searches for text line objects returning TextLineObject wrappers.
        """
        return self._to_textline_objects(self._find_text_lines(None))

    def select_text_lines_matching(self, pattern: str) -> List[TextLineObject]:
        """
        Searches for text line objects matching a regex pattern.

        Args:
            pattern: Regex pattern to match against text line text

        Returns:
            List of TextLineObject instances matching the pattern
        """
        position = Position()
        position.text_pattern = pattern
        return self._to_textline_objects(self._find_text_lines(position))

    def select_text_line_matching(self, pattern: str) -> Optional[TextLineObject]:
        """
        Select the first text line matching the specified regex pattern.

        Args:
            pattern: Regex pattern to match against text line text

        Returns:
            First TextLineObject matching the pattern, or None if no match
        """
        results = self.select_text_lines_matching(pattern)
        return results[0] if results else None

    def page(self, page_number: int) -> PageClient:
        """
        Get a specific page by page number, using snapshot cache when available.

        Args:
            page_number: The 1-based page number (page 1 is the first page)

        Returns:
            PageClient with page properties populated

        Raises:
            ValidationException: If page_number is less than 1
        """
        if page_number < 1:
            raise ValidationException(
                f"Page number must be >= 1 (1-based indexing), got {page_number}"
            )

        # Try to get page ref from snapshot first (avoids API call)
        page_snapshot = self._get_or_fetch_page_snapshot(page_number)
        if page_snapshot and page_snapshot.page_ref:
            return PageClient.from_ref(self, page_snapshot.page_ref)

        # Fallback to API if snapshot doesn't have page ref
        page_ref = self._get_page(page_number)
        if page_ref:
            return PageClient.from_ref(self, page_ref)
        else:
            return PageClient(page_number, self)

    # Page Operations

    def pages(self) -> List[PageClient]:
        return self._to_page_objects(self._get_pages())

    def _get_pages(self) -> List[PageRef]:
        """
        Retrieves references to all pages in the PDF document using snapshot cache.
        """
        # Use document snapshot which includes all pages (avoids API call)
        doc_snapshot = self._get_or_fetch_document_snapshot()
        return [page_snap.page_ref for page_snap in doc_snapshot.pages]

    def _get_page(self, page_number: int) -> Optional[PageRef]:
        """
        Retrieves a reference to a specific page by its page number.

        Args:
            page_number: The page number to retrieve (1-based indexing)

        Returns:
            Page reference for the specified page, or None if not found
        """
        if page_number < 1:
            raise ValidationException(
                f"Page number must be >= 1 (1-based indexing), got {page_number}"
            )

        params = {"pageNumber": page_number}
        response = self._make_request("POST", "/pdf/page/find", params=params)

        pages_data = response.json()
        if not pages_data:
            return None

        return self._parse_page_ref(pages_data[0])

    def _delete_page(self, page_ref: ObjectRef) -> bool:
        """
        Deletes a page from the PDF document.

        Args:
            page_ref: Reference to the page to be deleted

        Returns:
            True if the page was successfully deleted
        """
        if page_ref is None:
            raise ValidationException("Page reference cannot be null")

        request_data = page_ref.to_dict()

        response = self._make_request("DELETE", "/pdf/page/delete", data=request_data)
        result = response.json()

        # Invalidate snapshot caches after mutation
        if result:
            self._invalidate_snapshots()

        return result

    def move_page(self, from_page: int, to_page: int) -> bool:
        """
        Move a page to a different position within the document.

        Args:
            from_page: The source page number (1-based, page 1 is first page)
            to_page: The target page number (1-based)

        Returns:
            True if the page was successfully moved

        Raises:
            ValidationException: If from_page or to_page is less than 1
        """
        return self._move_page(from_page, to_page)

    def _move_page(self, from_page: int, to_page: int) -> bool:
        """Internal helper to perform the page move operation."""
        for value, label in (
            (from_page, "from_page"),
            (to_page, "to_page"),
        ):
            if value is None:
                raise ValidationException(f"{label} cannot be null")
            if not isinstance(value, int):
                raise ValidationException(
                    f"{label} must be an integer, got {type(value)}"
                )
            if value < 1:
                raise ValidationException(
                    f"{label} must be >= 1 (1-based indexing), got {value}"
                )

        request_data = PageMoveRequest(from_page, to_page).to_dict()
        response = self._make_request("PUT", "/pdf/page/move", data=request_data)
        result = response.json()

        # Invalidate snapshot caches after mutation
        if result:
            self._invalidate_snapshots()

        return bool(result)

    # Manipulation Operations

    def _delete(self, object_ref: ObjectRef) -> bool:
        """
        Deletes the specified PDF object from the document.

        Args:
            object_ref: Reference to the object to be deleted

        Returns:
            True if the object was successfully deleted
        """
        if object_ref is None:
            raise ValidationException("Object reference cannot be null")

        request_data = DeleteRequest(object_ref).to_dict()
        response = self._make_request("DELETE", "/pdf/delete", data=request_data)
        result = response.json()

        # Invalidate snapshot caches after mutation
        if result:
            self._invalidate_snapshots()

        return result

    def _move(self, object_ref: ObjectRef, position: Position) -> bool:
        """
        Moves a PDF object to a new position within the document.

        Args:
            object_ref: Reference to the object to be moved
            position: New position for the object

        Returns:
            True if the object was successfully moved
        """
        if object_ref is None:
            raise ValidationException("Object reference cannot be null")
        if position is None:
            raise ValidationException("Position cannot be null")

        request_data = MoveRequest(object_ref, position).to_dict()
        response = self._make_request("PUT", "/pdf/move", data=request_data)
        result = response.json()

        # Invalidate snapshot caches after mutation
        if result:
            self._invalidate_snapshots()

        return result

    def _redact(
        self,
        targets: List["RedactTarget"],
        default_replacement: str = "[REDACTED]",
        placeholder_color: Optional[Color] = None,
    ) -> "RedactResponse":
        """
        Redacts specified objects from the PDF document.

        Args:
            targets: List of RedactTarget objects identifying what to redact
            default_replacement: Default replacement text for redacted content
            placeholder_color: Color for image/path placeholder rectangles

        Returns:
            RedactResponse with count, success status, and any warnings
        """
        if not targets:
            raise ValidationException("At least one redaction target is required")

        if placeholder_color is None:
            placeholder_color = Color(0, 0, 0)

        request = RedactRequest(targets, default_replacement, placeholder_color)
        response = self._make_request("POST", "/pdf/redact", data=request.to_dict())
        result = RedactResponse.from_dict(response.json())

        if result.success:
            self._invalidate_snapshots()

        return result

    def redact(
        self,
        objects: List["PDFObjectBase"],
        replacement: str = "[REDACTED]",
        placeholder_color: Optional[Color] = None,
    ) -> "RedactResponse":
        """
        Redacts multiple objects from the PDF document.

        Args:
            objects: List of PDF objects to redact
            replacement: Replacement text for all redacted content
            placeholder_color: Color for image/path placeholder rectangles

        Returns:
            RedactResponse with count, success status, and any warnings
        """
        targets = [RedactTarget(obj.internal_id, replacement) for obj in objects]
        return self._redact(targets, replacement, placeholder_color)

    # Add Operations

    def _add_image(self, image: Image, position: Optional[Position] = None) -> bool:
        """
        Adds an image to the PDF document.

        Args:
            image: The image object to add
            position: Optional position override

        Returns:
            True if the image was successfully added
        """
        if image is None:
            raise ValidationException("Image cannot be null")

        if position is not None:
            image.set_position(position)

        if image.get_position() is None:
            raise ValidationException("Image position is null")

        return self._add_object(image)

    def _add_paragraph(self, paragraph: Paragraph) -> bool:
        """
        Adds a paragraph to the PDF document.

        Args:
            paragraph: The paragraph object to add

        Returns:
            True if the paragraph was successfully added
        """
        if paragraph is None:
            raise ValidationException("Paragraph cannot be null")
        if paragraph.get_position() is None:
            raise ValidationException("Paragraph position is null")
        if paragraph.get_position().page_number is None:
            raise ValidationException("Paragraph position page number is null")
        if paragraph.get_position().page_number < 1:
            raise ValidationException("Paragraph position page number is less than 1")

        return self._add_object(paragraph)

    def _add_path(self, path: "Path") -> bool:
        """
        Internal method to add a path to the document after validation.
        """

        if path is None:
            raise ValidationException("Path cannot be null")
        if path.get_position() is None:
            raise ValidationException("Path position is null")
        if path.get_position().page_number is None:
            raise ValidationException("Path position page number is null")
        if path.get_position().page_number < 1:
            raise ValidationException("Path position page number is less than 1")
        if not path.get_path_segments() or len(path.get_path_segments()) == 0:
            raise ValidationException("Path must have at least one segment")

        return self._add_object(path)

    def _add_object(self, pdf_object) -> bool:
        """
        Internal method to add any PDF object.
        """
        request_data = AddRequest(pdf_object).to_dict()
        response = self._make_request("POST", "/pdf/add", data=request_data)
        result = response.json()

        # Invalidate snapshot caches after mutation
        if result:
            self._invalidate_snapshots()

        return result

    def _add_page(self, request: Optional[AddPageRequest]) -> PageRef:
        """
        Internal helper to add a page with optional parameters.
        """
        request_data = None
        if request is not None:
            payload = request.to_dict()
            request_data = payload or None

        response = self._make_request("POST", "/pdf/page/add", data=request_data)
        result = self._parse_page_ref(response.json())

        # Invalidate snapshot caches after adding page
        self._invalidate_snapshots()

        return result

    def new_paragraph(self) -> ParagraphBuilder:
        return ParagraphBuilder(self)

    def new_page(
        self, orientation=Orientation.PORTRAIT, size=PageSize.A4
    ) -> PageBuilder:
        builder = PageBuilder(self)
        if orientation is not None:
            builder.orientation(orientation)
        if size is not None:
            builder.page_size(size)
        return builder

    def new_image(self) -> ImageBuilder:
        return ImageBuilder(self)

    def new_path(self) -> "PathBuilder":
        from .path_builder import PathBuilder

        return PathBuilder(self)

    # Modify Operations
    def _modify_paragraph(
        self, object_ref: ObjectRef, new_paragraph: Union[Paragraph, str]
    ) -> CommandResult:
        """
        Modifies a paragraph object or its text content.

        Args:
            object_ref: Reference to the paragraph to modify
            new_paragraph: New paragraph object or text string

        Returns:
            True if the paragraph was successfully modified
        """
        if object_ref is None:
            raise ValidationException("Object reference cannot be null")
        if new_paragraph is None:
            return CommandResult.empty("ModifyParagraph", object_ref.internal_id)

        if isinstance(new_paragraph, str):
            # Text modification - returns CommandResult
            request_data = ModifyTextRequest(object_ref, new_paragraph).to_dict()
            response = self._make_request(
                "PUT", "/pdf/text/paragraph", data=request_data
            )
            result = CommandResult.from_dict(response.json())
        else:
            # Object modification
            request_data = ModifyRequest(object_ref, new_paragraph).to_dict()
            response = self._make_request("PUT", "/pdf/modify", data=request_data)
            result = CommandResult.from_dict(response.json())

        # Invalidate snapshot caches after mutation
        self._invalidate_snapshots()
        return result

    def _modify_text_line(self, object_ref: ObjectRef, new_text: str) -> CommandResult:
        """
        Modifies a text line object.

        Args:
            object_ref: Reference to the text line to modify
            new_text: New text content

        Returns:
            True if the text line was successfully modified
        """
        if object_ref is None:
            raise ValidationException("Object reference cannot be null")
        if new_text is None:
            raise ValidationException("New text cannot be null")

        request_data = ModifyTextRequest(object_ref, new_text).to_dict()
        response = self._make_request("PUT", "/pdf/text/line", data=request_data)
        result = CommandResult.from_dict(response.json())

        # Invalidate snapshot caches after mutation
        self._invalidate_snapshots()
        return result

    def _modify_text_line_full(
        self, object_ref: ObjectRef, new_text_line: TextLine
    ) -> CommandResult:
        """
        Modifies a text line object with full styling (font, color, position).

        Args:
            object_ref: Reference to the text line to modify
            new_text_line: New text line object with styling

        Returns:
            CommandResult indicating success or failure
        """
        if object_ref is None:
            raise ValidationException("Object reference cannot be null")
        if new_text_line is None:
            raise ValidationException("New text line cannot be null")

        # Use /pdf/modify endpoint for full object modification
        request_data = ModifyRequest(object_ref, new_text_line).to_dict()
        response = self._make_request("PUT", "/pdf/modify", data=request_data)
        result = CommandResult.from_dict(response.json())

        # Invalidate snapshot caches after mutation
        self._invalidate_snapshots()
        return result

    # Font Operations

    def find_fonts(self, font_name: str, font_size: int) -> List[Font]:
        """
        Finds available fonts matching the specified name and size.

        Args:
            font_name: Name of the font to search for
            font_size: Size of the font

        Returns:
            List of matching Font objects
        """
        if not font_name or not font_name.strip():
            raise ValidationException("Font name cannot be null or empty")
        if font_size <= 0:
            raise ValidationException(f"Font size must be positive, got {font_size}")

        params = {"fontName": font_name.strip()}
        response = self._make_request("GET", "/font/find", params=params)

        font_names = response.json()
        return [Font(name, font_size) for name in font_names]

    def register_font(self, ttf_file: Union[Path, str, bytes, BinaryIO]) -> str:
        """
        Registers a custom font for use in PDF operations.

        Args:
            ttf_file: TTF font file as Path, filename, bytes, or file-like object

        Returns:
            Font registration result

        Raises:
            ValidationException: If font file is invalid
            HttpClientException: If registration fails
        """
        if ttf_file is None:
            raise ValidationException("TTF file cannot be null")

        # Process font file with validation similar to PDF processing
        try:
            if isinstance(ttf_file, bytes):
                if len(ttf_file) == 0:
                    raise ValidationException("Font data cannot be empty")
                font_data = ttf_file
                filename = "font.ttf"

            elif isinstance(ttf_file, (Path, str)):
                font_path = Path(ttf_file)
                if not font_path.exists():
                    raise ValidationException(f"TTF file does not exist: {font_path}")
                if not font_path.is_file():
                    raise ValidationException(f"TTF file is not a file: {font_path}")
                if not font_path.stat().st_size > 0:
                    raise ValidationException(f"TTF file is empty: {font_path}")

                with open(font_path, "rb") as f:
                    font_data = f.read()
                filename = font_path.name

            elif hasattr(ttf_file, "read"):
                font_data = ttf_file.read()
                if isinstance(font_data, str):
                    font_data = font_data.encode("utf-8")
                if len(font_data) == 0:
                    raise ValidationException(
                        "Font data from file-like object is empty"
                    )
                filename = getattr(ttf_file, "name", "font.ttf")

            else:
                raise ValidationException(
                    f"Unsupported font file type: {type(ttf_file)}"
                )

            # Upload font file
            files = {"ttfFile": (filename, font_data, "font/ttf")}

            request_size = len(font_data)
            if DEBUG:
                print(
                    f"{time.time()}|POST /font/register - request size: {request_size} bytes"
                )

            headers = {
                "X-Session-Id": self._session_id,
                "X-Generated-At": _generate_timestamp(),
            }
            response = self._client.post(
                self._cleanup_url_path(self._base_url, "/font/register"),
                files=files,
                headers=headers,
                timeout=30,
            )

            response_size = len(response.content)
            if DEBUG:
                print(
                    f"{time.time()}|POST /font/register - response size: {response_size} bytes"
                )

            _log_generated_at_header(response, "POST", "/font/register")
            response.raise_for_status()
            return response.text.strip()

        except (IOError, OSError) as e:
            raise PdfDancerException(f"Failed to read font file: {e}", cause=e)
        except httpx.HTTPStatusError as e:
            error_message = self._extract_error_message(e.response)
            raise HttpClientException(
                f"Font registration failed: {error_message}",
                response=e.response,
                cause=e,
            ) from None
        except httpx.RequestError as e:
            raise HttpClientException(
                f"Font registration failed: {str(e)}", response=None, cause=e
            ) from None

    # Document Operations

    # Snapshot Operations

    def get_document_snapshot(self, types: Optional[str] = None) -> DocumentSnapshot:
        """
        Retrieve a snapshot of the entire document with all pages and elements.

        Args:
            types: Optional comma-separated string of object types to filter (e.g., "PARAGRAPH,IMAGE")

        Returns:
            DocumentSnapshot containing page count, fonts, and all page snapshots
        """
        params = {}
        if types:
            params["types"] = types

        response = self._make_request("GET", "/pdf/document/snapshot", params=params)
        data = response.json()

        return self._parse_document_snapshot(data)

    def get_page_snapshot(
        self, page_number: int, types: Optional[str] = None
    ) -> PageSnapshot:
        """
        Retrieve a snapshot of a specific page with all its elements.

        Args:
            page_number: The page number to snapshot (1-based, page 1 is first page)
            types: Optional comma-separated string of object types to filter (e.g., "PARAGRAPH,IMAGE")

        Returns:
            PageSnapshot containing page reference and all elements on that page

        Raises:
            ValidationException: If page_number is less than 1
        """
        if page_number < 1:
            raise ValidationException(
                f"Page number must be >= 1 (1-based indexing), got {page_number}"
            )

        params = {}
        if types:
            params["types"] = types

        response = self._make_request(
            "GET", f"/pdf/page/{page_number}/snapshot", params=params
        )
        data = response.json()

        return self._parse_page_snapshot(data)

    def _get_or_fetch_document_snapshot(self) -> DocumentSnapshot:
        """
        Get document snapshot from cache or fetch if not cached.
        This is used internally by select_* methods for optimization.
        Also caches individual page snapshots from the document snapshot.
        """
        if self._document_snapshot is None:
            self._document_snapshot = self.get_document_snapshot()
            # Cache individual page snapshots from document snapshot
            for i, page_snapshot in enumerate(self._document_snapshot.pages):
                if i not in self._page_snapshots:
                    self._page_snapshots[i + 1] = page_snapshot
        return self._document_snapshot

    def _get_or_fetch_page_snapshot(self, page_number: int) -> PageSnapshot:
        """
        Get page snapshot from cache or fetch if not cached.
        This is used internally by select_* methods for optimization.
        If document snapshot exists, uses page from it instead of making separate API call.

        Args:
            page_number: 1-based page number
        """
        # Check if already cached
        if page_number in self._page_snapshots:
            return self._page_snapshots[page_number]

        # If document snapshot exists, get page from it (no API call needed)
        # Convert 1-based page number to 0-based index for array access
        if self._document_snapshot is not None:
            if 0 < page_number <= len(self._document_snapshot.pages):
                page_snapshot = self._document_snapshot.pages[page_number - 1]
                self._page_snapshots[page_number] = page_snapshot
                return page_snapshot

        # Otherwise fetch page snapshot individually
        self._page_snapshots[page_number] = self.get_page_snapshot(page_number)
        return self._page_snapshots[page_number]

    def _invalidate_snapshots(self) -> None:
        """
        Clear all snapshot caches.
        Called after mutations (delete, move, modify) to ensure fresh data on next select.
        """
        self._document_snapshot = None
        self._page_snapshots.clear()

    def _filter_snapshot_elements(
        self,
        elements: List,
        object_type: ObjectType,
        position: Optional[Position] = None,
        tolerance: float = DEFAULT_TOLERANCE,
    ) -> List:
        """
        Filter snapshot elements client-side based on object type and position criteria.

        Args:
            elements: List of elements from snapshot (ObjectRef, TextObjectRef, etc.)
            object_type: Type to filter for
            position: Optional position filter with text matching, bounding rect, etc.
            tolerance: Tolerance in points for spatial matching (default: 10.0)

        Returns:
            Filtered list of elements matching the criteria
        """
        import re

        # Filter by object type (handle form field subtypes)
        if object_type == ObjectType.FORM_FIELD:
            # Form fields include TEXT_FIELD, CHECK_BOX, RADIO_BUTTON, BUTTON, DROPDOWN
            form_field_types = {
                ObjectType.FORM_FIELD,
                ObjectType.TEXT_FIELD,
                ObjectType.CHECK_BOX,
                ObjectType.RADIO_BUTTON,
                ObjectType.BUTTON,
                ObjectType.DROPDOWN,
            }
            filtered = [e for e in elements if e.type in form_field_types]
        else:
            filtered = [e for e in elements if e.type == object_type]

        if position is None:
            return filtered

        # Apply position filters
        result = filtered

        # Text starts with filter (case-insensitive to match API behavior)
        if position.text_starts_with:
            search_text = position.text_starts_with.lower()
            result = [
                e
                for e in result
                if isinstance(e, TextObjectRef)
                and e.text
                and e.text.lower().startswith(search_text)
            ]

        # Regex pattern filter
        if position.text_pattern:
            pattern = re.compile(position.text_pattern)
            result = [
                e
                for e in result
                if isinstance(e, TextObjectRef) and e.text and pattern.search(e.text)
            ]

        # Bounding rect filter (spatial queries like at(x, y))
        if position.bounding_rect:
            rect = position.bounding_rect
            result = [
                e
                for e in result
                if e.position
                and e.position.bounding_rect
                and self._rects_intersect(e.position.bounding_rect, rect, tolerance)
            ]

        # Name filter (for form fields)
        if position.name:
            from .models import FormFieldRef

            result = [
                e
                for e in result
                if isinstance(e, FormFieldRef) and e.name == position.name
            ]

        return result

    @staticmethod
    def _rects_intersect(rect1, rect2, tolerance: float = DEFAULT_TOLERANCE) -> bool:
        """
        Check if two bounding rectangles intersect or are very close.
        Handles point queries (width/height = 0) with tolerance.

        Args:
            rect1: First bounding rectangle
            rect2: Second bounding rectangle
            tolerance: Tolerance in points for position matching (default: 10.0)
        """
        # Get effective bounds with tolerance
        r1_left = rect1.x - tolerance
        r1_right = rect1.x + rect1.width + tolerance
        r1_top = rect1.y - tolerance
        r1_bottom = rect1.y + rect1.height + tolerance

        r2_left = rect2.x - tolerance
        r2_right = rect2.x + rect2.width + tolerance
        r2_top = rect2.y - tolerance
        r2_bottom = rect2.y + rect2.height + tolerance

        # Check if rectangles overlap
        if r1_right < r2_left or r2_right < r1_left:
            return False
        if r1_bottom < r2_top or r2_bottom < r1_top:
            return False
        return True

    def get_bytes(self) -> bytes:
        """
        Downloads the current state of the PDF document with all modifications applied.

        Returns:
            PDF file data as bytes with all session modifications applied
        """
        response = self._make_request("GET", f"/session/{self._session_id}/pdf")
        return response.content

    def save(self, file_path: Union[str, Path]) -> None:
        """
        Saves the current PDF to a file.

        Args:
            file_path: Path where to save the PDF file

        Raises:
            ValidationException: If file path is invalid
            PdfDancerException: If file writing fails
        """
        if not file_path:
            raise ValidationException("File path cannot be null or empty")

        try:
            pdf_data = self.get_bytes()
            output_path = Path(file_path)

            # Create parent directories if they don't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(pdf_data)

        except (IOError, OSError) as e:
            raise PdfDancerException(f"Failed to save PDF file: {e}", cause=e)

    # Utility Methods

    def _parse_object_ref(self, obj_data: dict) -> ObjectRef:
        """Parse JSON object data into ObjectRef instance."""
        position_data = obj_data.get("position", {})
        position = self._parse_position(position_data) if position_data else None

        object_type = ObjectType(obj_data["type"])

        return ObjectRef(
            internal_id=obj_data["internalId"] if "internalId" in obj_data else None,
            position=position,
            type=object_type,
        )

    def _parse_form_field_ref(self, obj_data: dict) -> FormFieldRef:
        """Parse JSON object data into ObjectRef instance."""
        position_data = obj_data.get("position", {})
        position = self._parse_position(position_data) if position_data else None

        object_type = ObjectType(obj_data["type"])

        return FormFieldRef(
            internal_id=obj_data["internalId"] if "internalId" in obj_data else None,
            position=position,
            type=object_type,
            name=obj_data["name"] if "name" in obj_data else None,
            value=obj_data["value"] if "value" in obj_data else None,
        )

    @staticmethod
    def _parse_position(pos_data: dict) -> Position:
        """Parse JSON position data into Position instance."""
        position = Position()
        position.page_number = pos_data.get("pageNumber")
        position.text_starts_with = pos_data.get("textStartsWith")

        if "shape" in pos_data:
            position.shape = ShapeType(pos_data["shape"])
        if "mode" in pos_data:
            position.mode = PositionMode(pos_data["mode"])

        if "boundingRect" in pos_data:
            rect_data = pos_data["boundingRect"]
            from .models import BoundingRect

            position.bounding_rect = BoundingRect(
                x=rect_data["x"],
                y=rect_data["y"],
                width=rect_data["width"],
                height=rect_data["height"],
            )

        return position

    def _parse_text_object_ref(
        self, obj_data: dict, fallback_id: Optional[str] = None
    ) -> TextObjectRef:
        """Parse JSON object data into TextObjectRef instance with hierarchical structure."""
        position_data = obj_data.get("position", {})
        position = self._parse_position(position_data) if position_data else Position()

        object_type = ObjectType(obj_data.get("type", "TEXT_LINE"))
        line_spacings = (
            obj_data.get("lineSpacings")
            if isinstance(obj_data.get("lineSpacings"), list)
            else None
        )
        internal_id = obj_data.get("internalId", fallback_id or "")

        color = None
        color_data = obj_data.get("color")
        if isinstance(color_data, dict):
            from .models import Color

            red = color_data.get("red")
            green = color_data.get("green")
            blue = color_data.get("blue")
            alpha = color_data.get("alpha", 255)
            if all(isinstance(v, int) for v in [red, green, blue]):
                color = Color(red, green, blue, alpha)

        # Parse status if present
        status = None
        status_data = obj_data.get("status")
        if isinstance(status_data, dict):
            from .models import FontRecommendation, FontType, TextStatus

            # Parse font recommendation
            font_rec_data = status_data.get("fontRecommendation")
            font_rec = None
            if isinstance(font_rec_data, dict):
                font_rec = FontRecommendation(
                    font_name=font_rec_data.get("fontName", ""),
                    font_type=FontType(font_rec_data.get("fontType", "SYSTEM")),
                    similarity_score=font_rec_data.get("similarityScore", 0.0),
                )

            status = TextStatus(
                modified=status_data.get("modified", False),
                encodable=status_data.get("encodable", True),
                font_type=FontType(status_data.get("fontType", "UNKNOWN")),
                font_recommendation=font_rec,
            )

        text_object = TextObjectRef(
            internal_id=internal_id,
            position=position,
            object_type=object_type,
            text=(
                obj_data.get("text") if isinstance(obj_data.get("text"), str) else None
            ),
            font_name=(
                obj_data.get("fontName")
                if isinstance(obj_data.get("fontName"), str)
                else None
            ),
            font_size=(
                obj_data.get("fontSize")
                if isinstance(obj_data.get("fontSize"), (int, float))
                else None
            ),
            line_spacings=line_spacings,
            color=color,
            status=status,
        )

        try:
            if (
                isinstance(obj_data.get("children"), list)
                and len(obj_data["children"]) > 0
            ):
                text_object.children = [
                    self._parse_text_object_ref(
                        child_data, f"{internal_id or 'child'}-{index}"
                    )
                    for index, child_data in enumerate(obj_data["children"])
                ]
        except ValueError as e:
            logging.exception(f"Failed to parse children of {internal_id}", e)

        return text_object

    def _parse_page_ref(self, obj_data: dict) -> PageRef:
        """Parse JSON object data into PageRef instance with page-specific properties."""
        position_data = obj_data.get("position", {})
        position = self._parse_position(position_data) if position_data else None

        object_type = ObjectType(obj_data["type"])

        # Parse page size if present
        page_size = None
        if "pageSize" in obj_data and isinstance(obj_data["pageSize"], dict):
            page_size_data = obj_data["pageSize"]
            try:
                page_size = PageSize.from_dict(page_size_data)
            except ValueError:
                page_size = None

        # Parse orientation if present
        orientation_value = obj_data.get("orientation")
        orientation = None
        if isinstance(orientation_value, str):
            normalized = orientation_value.strip().upper()
            try:
                orientation = Orientation(normalized)
            except ValueError:
                orientation = None
        elif isinstance(orientation_value, Orientation):
            orientation = orientation_value

        return PageRef(
            internal_id=obj_data.get("internalId"),
            position=position,
            type=object_type,
            page_size=page_size,
            orientation=orientation,
        )

    def _parse_path_segment(self, segment_data: dict) -> "PathSegment":
        """Parse JSON data into PathSegment instance (Line or Bezier)."""
        from .models import Bezier, Color, Line, PathSegment, Point

        segment_type = segment_data.get(
            "segmentType", segment_data.get("type", "")
        ).upper()

        # Parse common properties
        stroke_color = None
        stroke_color_data = segment_data.get("strokeColor")
        if isinstance(stroke_color_data, dict):
            r = stroke_color_data.get("red", 0)
            g = stroke_color_data.get("green", 0)
            b = stroke_color_data.get("blue", 0)
            a = stroke_color_data.get("alpha", 255)
            if all(isinstance(v, int) for v in [r, g, b]):
                stroke_color = Color(r, g, b, a)

        fill_color = None
        fill_color_data = segment_data.get("fillColor")
        if isinstance(fill_color_data, dict):
            r = fill_color_data.get("red", 0)
            g = fill_color_data.get("green", 0)
            b = fill_color_data.get("blue", 0)
            a = fill_color_data.get("alpha", 255)
            if all(isinstance(v, int) for v in [r, g, b]):
                fill_color = Color(r, g, b, a)

        stroke_width = segment_data.get("strokeWidth")
        dash_array = segment_data.get("dashArray")
        dash_phase = segment_data.get("dashPhase")

        # Parse specific segment type
        if segment_type == "LINE":
            p0_data = segment_data.get("p0", {})
            p1_data = segment_data.get("p1", {})

            p0 = (
                Point(p0_data.get("x", 0.0), p0_data.get("y", 0.0)) if p0_data else None
            )
            p1 = (
                Point(p1_data.get("x", 0.0), p1_data.get("y", 0.0)) if p1_data else None
            )

            return Line(
                stroke_color=stroke_color,
                fill_color=fill_color,
                stroke_width=stroke_width,
                dash_array=dash_array,
                dash_phase=dash_phase,
                p0=p0,
                p1=p1,
            )
        elif segment_type == "BEZIER":
            p0_data = segment_data.get("p0", {})
            p1_data = segment_data.get("p1", {})
            p2_data = segment_data.get("p2", {})
            p3_data = segment_data.get("p3", {})

            p0 = (
                Point(p0_data.get("x", 0.0), p0_data.get("y", 0.0)) if p0_data else None
            )
            p1 = (
                Point(p1_data.get("x", 0.0), p1_data.get("y", 0.0)) if p1_data else None
            )
            p2 = (
                Point(p2_data.get("x", 0.0), p2_data.get("y", 0.0)) if p2_data else None
            )
            p3 = (
                Point(p3_data.get("x", 0.0), p3_data.get("y", 0.0)) if p3_data else None
            )

            return Bezier(
                stroke_color=stroke_color,
                fill_color=fill_color,
                stroke_width=stroke_width,
                dash_array=dash_array,
                dash_phase=dash_phase,
                p0=p0,
                p1=p1,
                p2=p2,
                p3=p3,
            )
        else:
            # Fallback to base PathSegment for unknown types
            return PathSegment(
                stroke_color=stroke_color,
                fill_color=fill_color,
                stroke_width=stroke_width,
                dash_array=dash_array,
                dash_phase=dash_phase,
            )

    def _parse_path(self, obj_data: dict) -> "Path":
        """Parse JSON data into Path instance with path segments."""
        from .models import Path

        position_data = obj_data.get("position", {})
        position = self._parse_position(position_data) if position_data else None

        # Parse path segments
        path_segments = []
        segments_data = obj_data.get("pathSegments", [])
        if isinstance(segments_data, list):
            for segment_data in segments_data:
                if isinstance(segment_data, dict):
                    path_segments.append(self._parse_path_segment(segment_data))

        even_odd_fill = obj_data.get("evenOddFill")

        return Path(
            position=position,
            path_segments=path_segments if path_segments else None,
            even_odd_fill=even_odd_fill,
        )

    def _parse_document_font_info(self, data: dict) -> FontRecommendation:
        """Parse JSON data into FontRecommendation instance."""
        font_type_str = data.get("fontType", "SYSTEM")
        font_type = FontType(font_type_str)

        return FontRecommendation(
            font_name=data.get("fontName", ""),
            font_type=font_type,
            similarity_score=data.get("similarityScore", 0.0),
        )

    def _parse_page_snapshot(self, data: dict) -> PageSnapshot:
        """Parse JSON data into PageSnapshot instance with proper type handling."""
        page_ref = self._parse_page_ref(data.get("pageRef", {}))

        # Parse elements using appropriate parser based on type
        elements = []
        for elem_data in data.get("elements", []):
            elem_type_str = elem_data.get("type")
            if not elem_type_str:
                continue

            try:
                # Normalize type string (API returns "CHECKBOX" but enum is "CHECK_BOX")
                if elem_type_str == "CHECKBOX":
                    elem_type_str = "CHECK_BOX"
                    # Deep copy to avoid modifying original
                    import copy

                    elem_data = copy.deepcopy(elem_data)
                    elem_data["type"] = elem_type_str  # Update type in data

                elem_type = ObjectType(elem_type_str)

                # Use appropriate parser based on element type
                if elem_type in (ObjectType.PARAGRAPH, ObjectType.TEXT_LINE):
                    # Parse as TextObjectRef to capture text, font, color, children
                    elements.append(self._parse_text_object_ref(elem_data))
                elif elem_type in (
                    ObjectType.FORM_FIELD,
                    ObjectType.TEXT_FIELD,
                    ObjectType.CHECK_BOX,
                    ObjectType.RADIO_BUTTON,
                    ObjectType.BUTTON,
                    ObjectType.DROPDOWN,
                ):
                    # Parse as FormFieldRef to capture name and value
                    elements.append(self._parse_form_field_ref(elem_data))
                else:
                    # Parse as basic ObjectRef
                    elements.append(self._parse_object_ref(elem_data))
            except (ValueError, KeyError):
                # Skip elements with invalid types
                continue

        return PageSnapshot(page_ref=page_ref, elements=elements)

    def _parse_document_snapshot(self, data: dict) -> DocumentSnapshot:
        """Parse JSON data into DocumentSnapshot instance."""
        page_count = data.get("pageCount", 0)
        fonts = [
            self._parse_document_font_info(font_data)
            for font_data in data.get("fonts", [])
        ]
        pages = [
            self._parse_page_snapshot(page_data) for page_data in data.get("pages", [])
        ]

        return DocumentSnapshot(page_count=page_count, fonts=fonts, pages=pages)

    # Builder Pattern Support

    def _paragraph_builder(self) -> "ParagraphBuilder":
        """
        Creates a new ParagraphBuilder for fluent paragraph construction.
        Returns:
            A new ParagraphBuilder instance
        """
        from .paragraph_builder import ParagraphBuilder

        return ParagraphBuilder(self)

    # Context Manager Support (Python enhancement)
    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup if needed."""
        # Close the HTTP client to free resources
        if hasattr(self, "_client"):
            self._client.close()
        # TODO Could add session cleanup here if API supports it. Cleanup on the server
        pass

    def close(self):
        """Close the HTTP client and free resources."""
        if hasattr(self, "_client"):
            self._client.close()

    def _to_path_objects(self, refs: List[ObjectRef]) -> List[PathObject]:
        return [
            PathObject(self, ref.internal_id, ref.type, ref.position) for ref in refs
        ]

    def _to_paragraph_objects(self, refs: List[TextObjectRef]) -> List[ParagraphObject]:
        return [ParagraphObject(self, ref) for ref in refs]

    def _to_textline_objects(self, refs: List[TextObjectRef]) -> List[TextLineObject]:
        return [TextLineObject(self, ref) for ref in refs]

    def _to_image_objects(self, refs: List[ObjectRef]) -> List[ImageObject]:
        return [
            ImageObject(self, ref.internal_id, ref.type, ref.position) for ref in refs
        ]

    def _to_form_objects(self, refs: List[ObjectRef]) -> List[FormObject]:
        return [
            FormObject(self, ref.internal_id, ref.type, ref.position) for ref in refs
        ]

    def _to_form_field_objects(self, refs: List[FormFieldRef]) -> List[FormFieldObject]:
        return [
            FormFieldObject(
                self, ref.internal_id, ref.type, ref.position, ref.name, ref.value
            )
            for ref in refs
        ]

    def _to_page_objects(self, refs: List[PageRef]) -> List[PageClient]:
        return [PageClient.from_ref(self, ref) for ref in refs]

    def _to_page_object(self, ref: PageRef) -> PageClient:
        return PageClient.from_ref(self, ref)

    def _to_mixed_objects(self, refs: List[ObjectRef]) -> List:
        """
        Convert a list of ObjectRefs to their appropriate object types.
        Handles mixed object types by checking the type of each ref.
        """
        result = []
        for ref in refs:
            if ref.type == ObjectType.PARAGRAPH:
                # Need to convert to TextObjectRef first
                if isinstance(ref, TextObjectRef):
                    result.append(ParagraphObject(self, ref))
                else:
                    # Re-fetch with proper type
                    text_refs = self._find_paragraphs(ref.position)
                    result.extend(self._to_paragraph_objects(text_refs))
            elif ref.type == ObjectType.TEXT_LINE:
                if isinstance(ref, TextObjectRef):
                    result.append(TextLineObject(self, ref))
                else:
                    text_refs = self._find_text_lines(ref.position)
                    result.extend(self._to_textline_objects(text_refs))
            elif ref.type == ObjectType.IMAGE:
                result.append(
                    ImageObject(self, ref.internal_id, ref.type, ref.position)
                )
            elif ref.type == ObjectType.PATH:
                result.append(PathObject(self, ref.internal_id, ref.type, ref.position))
            elif ref.type == ObjectType.FORM_X_OBJECT:
                result.append(FormObject(self, ref.internal_id, ref.type, ref.position))
            elif ref.type == ObjectType.FORM_FIELD:
                if isinstance(ref, FormFieldRef):
                    result.append(
                        FormFieldObject(
                            self,
                            ref.internal_id,
                            ref.type,
                            ref.position,
                            ref.name,
                            ref.value,
                        )
                    )
                else:
                    form_refs = self._find_form_fields(ref.position)
                    result.extend(self._to_form_field_objects(form_refs))
        return result

    def select_elements(self):
        """
        Select all elements (paragraphs, images, paths, forms) in the document.

        Returns:
            List of all PDF objects in the document
        """
        result = []
        result.extend(self.select_paragraphs())
        result.extend(self.select_text_lines())
        result.extend(self.select_images())
        result.extend(self.select_paths())
        result.extend(self.select_forms())
        result.extend(self.select_form_fields())
        return result
