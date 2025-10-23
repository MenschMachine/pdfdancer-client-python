"""
PDFDancer Python Client V1

A Python client that closely mirrors the Java Client class structure and functionality.
Provides session-based PDF manipulation operations with strict validation.
"""

import json
import os
import time
from pathlib import Path
from typing import List, Optional, Union, BinaryIO, Mapping, Any

import requests
from dotenv import load_dotenv

load_dotenv()

# Global variable to disable SSL certificate verification
# Set to True to skip SSL verification (useful for testing with self-signed certificates)
# WARNING: Only use in development/testing environments
DISABLE_SSL_VERIFY = False

DEBUG = False

from . import ParagraphBuilder
from .exceptions import (
    PdfDancerException,
    FontNotFoundException,
    HttpClientException,
    SessionException,
    ValidationException
)
from .image_builder import ImageBuilder
from .models import (
    ObjectRef, Position, ObjectType, Font, Image, Paragraph, FormFieldRef, TextObjectRef, PageRef,
    FindRequest, DeleteRequest, MoveRequest, PageMoveRequest, AddRequest, ModifyRequest, ModifyTextRequest,
    ChangeFormFieldRequest, CommandResult,
    ShapeType, PositionMode, PageSize, Orientation
)
from .paragraph_builder import ParagraphPageBuilder
from .types import PathObject, ParagraphObject, TextLineObject, ImageObject, FormObject, FormFieldObject


class PageClient:
    def __init__(self, page_index: int, root: "PDFDancer", page_size: Optional[PageSize] = None,
                 orientation: Optional[Union[Orientation, str]] = Orientation.PORTRAIT):
        self.page_index = page_index
        self.root = root
        self.object_type = ObjectType.PAGE
        self.position = Position.at_page(page_index)
        self.internal_id = f"PAGE-{page_index}"
        self.page_size = page_size
        if isinstance(orientation, str):
            normalized = orientation.strip().upper()
            try:
                self.orientation = Orientation(normalized)
            except ValueError:
                self.orientation = normalized
        else:
            self.orientation = orientation

    def select_paths_at(self, x: float, y: float) -> List[PathObject]:
        # noinspection PyProtectedMember
        return self.root._to_path_objects(self.root._find_paths(Position.at_page_coordinates(self.page_index, x, y)))

    def select_paragraphs(self) -> List[ParagraphObject]:
        # noinspection PyProtectedMember
        return self.root._to_paragraph_objects(self.root._find_paragraphs(Position.at_page(self.page_index)))

    def select_paragraphs_starting_with(self, text: str) -> List[ParagraphObject]:
        position = Position.at_page(self.page_index)
        position.with_text_starts(text)
        # noinspection PyProtectedMember
        return self.root._to_paragraph_objects(self.root._find_paragraphs(position))

    def select_paragraphs_matching(self, pattern):
        position = Position.at_page(self.page_index)
        position.text_pattern = pattern
        # noinspection PyProtectedMember
        return self.root._to_paragraph_objects(self.root._find_paragraphs(position))

    def select_text_lines_matching(self, pattern: str) -> List[TextLineObject]:
        position = Position.at_page(self.page_index)
        position.text_pattern = pattern
        # noinspection PyProtectedMember
        return self.root._to_textline_objects(self.root._find_text_lines(position))

    def select_paragraphs_at(self, x: float, y: float) -> List[ParagraphObject]:
        position = Position.at_page_coordinates(self.page_index, x, y)
        # noinspection PyProtectedMember
        return self.root._to_paragraph_objects(self.root._find_paragraphs(position))

    def select_text_lines(self) -> List[TextLineObject]:
        position = Position.at_page(self.page_index)
        # noinspection PyProtectedMember
        return self.root._to_textline_objects(self.root._find_text_lines(position))

    def select_text_lines_starting_with(self, text: str) -> List[TextLineObject]:
        position = Position.at_page(self.page_index)
        position.with_text_starts(text)
        # noinspection PyProtectedMember
        return self.root._to_textline_objects(self.root._find_text_lines(position))

    def select_text_lines_at(self, x, y) -> List[TextLineObject]:
        position = Position.at_page_coordinates(self.page_index, x, y)
        # noinspection PyProtectedMember
        return self.root._to_textline_objects(self.root._find_text_lines(position))

    def select_images(self) -> List[ImageObject]:
        # noinspection PyProtectedMember
        return self.root._to_image_objects(self.root._find_images(Position.at_page(self.page_index)))

    def select_images_at(self, x: float, y: float) -> List[ImageObject]:
        position = Position.at_page_coordinates(self.page_index, x, y)
        # noinspection PyProtectedMember
        return self.root._to_image_objects(self.root._find_images(position))

    def select_forms(self) -> List[FormObject]:
        position = Position.at_page(self.page_index)
        # noinspection PyProtectedMember
        return self.root._to_form_objects(self.root._find_form_x_objects(position))

    def select_forms_at(self, x: float, y: float) -> List[FormObject]:
        position = Position.at_page_coordinates(self.page_index, x, y)
        # noinspection PyProtectedMember
        return self.root._to_form_objects(self.root._find_form_x_objects(position))

    def select_form_fields(self) -> List[FormFieldObject]:
        position = Position.at_page(self.page_index)
        # noinspection PyProtectedMember
        return self.root._to_form_field_objects(self.root._find_form_fields(position))

    def select_form_fields_by_name(self, field_name: str) -> List[FormFieldObject]:
        pos = Position.by_name(field_name)
        pos.page_index = self.page_index
        # noinspection PyProtectedMember
        return self.root._to_form_field_objects(self.root._find_form_fields(pos))

    def select_form_fields_at(self, x: float, y: float) -> List[FormFieldObject]:
        position = Position.at_page_coordinates(self.page_index, x, y)
        # noinspection PyProtectedMember
        return self.root._to_form_field_objects(self.root._find_form_fields(position))

    @classmethod
    def from_ref(cls, root: 'PDFDancer', page_ref: PageRef) -> 'PageClient':
        page_client = PageClient(
            page_index=page_ref.position.page_index,
            root=root,
            page_size=page_ref.page_size,
            orientation=page_ref.orientation
        )
        page_client.internal_id = page_ref.internal_id
        if page_ref.position is not None:
            page_client.position = page_ref.position
            page_client.page_index = page_ref.position.page_index
        return page_client

    def delete(self) -> bool:
        # noinspection PyProtectedMember
        return self.root._delete_page(self._ref())

    def move_to(self, target_page_index: int) -> bool:
        """Move this page to a different index within the document."""
        if target_page_index is None or target_page_index < 0:
            raise ValidationException(f"Target page index must be >= 0, got {target_page_index}")

        # noinspection PyProtectedMember
        moved = self.root._move_page(self.page_index, target_page_index)
        if moved:
            self.page_index = target_page_index
            self.position = Position.at_page(target_page_index)
        return moved

    def _ref(self):
        return ObjectRef(internal_id=self.internal_id, position=self.position, type=self.object_type)

    def new_paragraph(self):
        return ParagraphPageBuilder(self.root, self.page_index)

    def select_paths(self):
        # noinspection PyProtectedMember
        return self.root._to_path_objects(self.root._find_paths(Position.at_page(self.page_index)))

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
    def open(cls,
             pdf_data: Union[bytes, Path, str, BinaryIO],
             token: Optional[str] = None,
             base_url: Optional[str] = None,
             timeout: float = 30.0) -> "PDFDancer":
        """
        Create a client session, falling back to environment variables when needed.

        Args:
            pdf_data: PDF payload supplied directly or via filesystem handles.
            token: Override for the API token; falls back to `PDFDANCER_TOKEN` environement variable.
            base_url: Override for the API base URL; falls back to `PDFDANCER_BASE_URL`
                or defaults to `https://api.pdfdancer.com`.
            timeout: HTTP read timeout in seconds.

        Returns:
            A ready-to-use `PDFDancer` client instance.
        """
        resolved_token = cls._resolve_token(token)
        resolved_base_url = cls._resolve_base_url(base_url)

        return PDFDancer(resolved_token, pdf_data, resolved_base_url, timeout)

    @classmethod
    def _resolve_base_url(cls, base_url: Optional[str]) -> Optional[str]:
        env_base_url = os.getenv("PDFDANCER_BASE_URL")
        resolved_base_url = base_url or (env_base_url.strip() if env_base_url and env_base_url.strip() else None)
        if resolved_base_url is None:
            resolved_base_url = "https://api.pdfdancer.com"
        return resolved_base_url

    @classmethod
    def _resolve_token(cls, token: Optional[str]) -> Optional[str]:
        resolved_token = token.strip() if token and token.strip() else None
        if resolved_token is None:
            env_token = os.getenv("PDFDANCER_TOKEN")
            resolved_token = env_token.strip() if env_token and env_token.strip() else None

        if resolved_token is None:
            raise ValidationException(
                "Missing PDFDancer API token. Pass a token via the `token` argument "
                "or set the PDFDANCER_TOKEN environment variable."
            )
        return resolved_token

    @classmethod
    def new(cls,
            token: Optional[str] = None,
            base_url: Optional[str] = None,
            timeout: float = 30.0,
            page_size: Optional[Union[PageSize, str, Mapping[str, Any]]] = None,
            orientation: Optional[Union[Orientation, str]] = None,
            initial_page_count: int = 1) -> "PDFDancer":
        """
        Create a new blank PDF document with optional configuration.

        Args:
            token: Override for the API token; falls back to `PDFDANCER_TOKEN` environment variable.
            base_url: Override for the API base URL; falls back to `PDFDANCER_BASE_URL`
                or defaults to `https://api.pdfdancer.com`.
            timeout: HTTP read timeout in seconds.
            page_size: Page size for the PDF (default: A4). Accepts `PageSize`, a standard name string, or a
                mapping with `width`/`height` values.
            orientation: Page orientation (default: PORTRAIT). Can be Orientation enum or string.
            initial_page_count: Number of initial blank pages (default: 1).

        Returns:
            A ready-to-use `PDFDancer` client instance with a blank PDF.
        """
        resolved_token = cls._resolve_token(token)
        resolved_base_url = cls._resolve_base_url(base_url)

        # Create a new instance that will call _create_blank_pdf_session
        instance = object.__new__(cls)

        # Initialize instance variables
        if not resolved_token or not resolved_token.strip():
            raise ValidationException("Authentication token cannot be null or empty")

        instance._token = resolved_token.strip()
        instance._base_url = resolved_base_url.rstrip('/')
        instance._read_timeout = timeout

        # Create HTTP session for connection reuse
        instance._session = requests.Session()
        instance._session.headers.update({
            'Authorization': f'Bearer {instance._token}'
        })

        # Create blank PDF session
        instance._session_id = instance._create_blank_pdf_session(
            page_size=page_size,
            orientation=orientation,
            initial_page_count=initial_page_count
        )

        # Set pdf_bytes to None since we don't have the PDF bytes yet
        instance._pdf_bytes = None

        return instance

    def __init__(self, token: str, pdf_data: Union[bytes, Path, str, BinaryIO],
                 base_url: str, read_timeout: float = 0):
        """
        Creates a new client with PDF data.
        This constructor initializes the client, uploads the PDF data to create
        a new session, and prepares the client for PDF manipulation operations.

        Args:
            token: Authentication token for API access
            pdf_data: PDF file data as bytes, Path, filename string, or file-like object
            base_url: Base URL of the PDFDancer API server
            read_timeout: Timeout in seconds for HTTP requests (default: 30.0)

        Raises:
            ValidationException: If token is empty or PDF data is invalid
            SessionException: If session creation fails
            HttpClientException: If HTTP communication fails
        """
        # Strict validation like Java client
        if not token or not token.strip():
            raise ValidationException("Authentication token cannot be null or empty")

        self._token = token.strip()
        self._base_url = base_url.rstrip('/')
        self._read_timeout = read_timeout

        # Process PDF data with validation
        self._pdf_bytes = self._process_pdf_data(pdf_data)

        # Create HTTP session for connection reuse
        self._session = requests.Session()
        self._session.headers.update({
            'Authorization': f'Bearer {self._token}'
        })

        # Create session - equivalent to Java constructor behavior
        self._session_id = self._create_session()

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

                with open(file_path, 'rb') as f:
                    return f.read()

            elif hasattr(pdf_data, 'read'):
                # File-like object
                data = pdf_data.read()
                if isinstance(data, str):
                    data = data.encode('utf-8')
                if len(data) == 0:
                    raise ValidationException("PDF data from file-like object is empty")
                return data

            else:
                raise ValidationException(f"Unsupported PDF data type: {type(pdf_data)}")

        except (IOError, OSError) as e:
            raise PdfDancerException(f"Failed to read PDF data: {e}", cause=e)

    def _extract_error_message(self, response: Optional[requests.Response]) -> str:
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

    def _handle_authentication_error(self, response: Optional[requests.Response]) -> None:
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
        base = base_url.rstrip('/')
        path = path.lstrip('/')
        return f"{base}/{path}"

    def _create_session(self) -> str:
        """
        Creates a new PDF processing session by uploading the PDF data.
        """
        try:
            files = {
                'pdf': ('document.pdf', self._pdf_bytes, 'application/pdf')
            }

            request_size = len(self._pdf_bytes)
            if DEBUG:
                print(f"{time.time()}|POST /session/create - request size: {request_size} bytes")

            response = self._session.post(
                self._cleanup_url_path(self._base_url, "/session/create"),
                files=files,
                timeout=self._read_timeout if self._read_timeout > 0 else None,
                verify=not DISABLE_SSL_VERIFY
            )

            response_size = len(response.content)
            if DEBUG:
                print(f"{time.time()}|POST /session/create - response size: {response_size} bytes")

            self._handle_authentication_error(response)
            response.raise_for_status()
            session_id = response.text.strip()

            if not session_id:
                raise SessionException("Server returned empty session ID")

            return session_id

        except requests.exceptions.RequestException as e:
            self._handle_authentication_error(getattr(e, 'response', None))
            error_message = self._extract_error_message(getattr(e, 'response', None))
            raise HttpClientException(f"Failed to create session: {error_message}",
                                      response=getattr(e, 'response', None), cause=e) from None

    def _create_blank_pdf_session(self,
                                  page_size: Optional[Union[PageSize, str, Mapping[str, Any]]] = None,
                                  orientation: Optional[Union[Orientation, str]] = None,
                                  initial_page_count: int = 1) -> str:
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
        try:
            # Build request payload
            request_data = {}

            # Handle page_size - convert to type-safe object with dimensions
            if page_size is not None:
                try:
                    request_data['pageSize'] = PageSize.coerce(page_size).to_dict()
                except ValueError as exc:
                    raise ValidationException(str(exc)) from exc
                except TypeError:
                    raise ValidationException(f"Invalid page_size type: {type(page_size)}")

            # Handle orientation
            if orientation is not None:
                if isinstance(orientation, Orientation):
                    request_data['orientation'] = orientation.value
                elif isinstance(orientation, str):
                    request_data['orientation'] = orientation
                else:
                    raise ValidationException(f"Invalid orientation type: {type(orientation)}")

            # Handle initial_page_count with validation
            if initial_page_count < 1:
                raise ValidationException(f"Initial page count must be at least 1, got {initial_page_count}")
            request_data['initialPageCount'] = initial_page_count

            request_body = json.dumps(request_data)
            request_size = len(request_body.encode('utf-8'))
            if DEBUG:
                print(f"{time.time()}|POST /session/new - request size: {request_size} bytes")

            headers = {'Content-Type': 'application/json'}
            response = self._session.post(
                self._cleanup_url_path(self._base_url, "/session/new"),
                json=request_data,
                headers=headers,
                timeout=self._read_timeout if self._read_timeout > 0 else None,
                verify=not DISABLE_SSL_VERIFY
            )

            response_size = len(response.content)
            if DEBUG:
                print(f"{time.time()}|POST /session/new - response size: {response_size} bytes")

            self._handle_authentication_error(response)
            response.raise_for_status()
            session_id = response.text.strip()

            if not session_id:
                raise SessionException("Server returned empty session ID")

            return session_id

        except requests.exceptions.RequestException as e:
            self._handle_authentication_error(getattr(e, 'response', None))
            error_message = self._extract_error_message(getattr(e, 'response', None))
            raise HttpClientException(f"Failed to create blank PDF session: {error_message}",
                                      response=getattr(e, 'response', None), cause=e) from None

    def _make_request(self, method: str, path: str, data: Optional[dict] = None,
                      params: Optional[dict] = None) -> requests.Response:
        """
        Make HTTP request with session headers and error handling.
        """
        headers = {
            'X-Session-Id': self._session_id,
            'Content-Type': 'application/json'
        }

        try:
            request_size = 0
            if data is not None:
                request_body = json.dumps(data)
                request_size = len(request_body.encode('utf-8'))
            if DEBUG:
                print(f"{time.time()}|{method} {path} - request size: {request_size} bytes")

            response = self._session.request(
                method=method,
                url=self._cleanup_url_path(self._base_url, path),
                json=data,
                params=params,
                headers=headers,
                timeout=self._read_timeout if self._read_timeout > 0 else None,
                verify=not DISABLE_SSL_VERIFY
            )

            response_size = len(response.content)
            if DEBUG:
                print(f"{time.time()}|{method} {path} - response size: {response_size} bytes")

            # Handle FontNotFoundException
            if response.status_code == 404:
                try:
                    error_data = response.json()
                    if error_data.get('error') == 'FontNotFoundException':
                        raise FontNotFoundException(error_data.get('message', 'Font not found'))
                except (json.JSONDecodeError, KeyError):
                    pass

            self._handle_authentication_error(response)
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            self._handle_authentication_error(getattr(e, 'response', None))
            error_message = self._extract_error_message(getattr(e, 'response', None))
            raise HttpClientException(f"API request failed: {error_message}", response=getattr(e, 'response', None),
                                      cause=e) from None

    def _find(self, object_type: Optional[ObjectType] = None, position: Optional[Position] = None) -> List[ObjectRef]:
        """
        Searches for PDF objects matching the specified criteria.
        This method provides flexible search capabilities across all PDF content,
        allowing filtering by object type and position constraints.

        Args:
            object_type: The type of objects to find (None for all types)
            position: Positional constraints for the search (None for all positions)

        Returns:
            List of object references matching the search criteria
        """
        request_data = FindRequest(object_type, position).to_dict()
        response = self._make_request('POST', '/pdf/find', data=request_data)

        # Parse response into ObjectRef objects
        objects_data = response.json()
        return [self._parse_object_ref(obj_data) for obj_data in objects_data]

    def select_paragraphs(self) -> List[TextObjectRef]:
        """
        Searches for paragraph objects returning TextObjectRef with hierarchical structure.
        """
        return self._find_paragraphs(None)

    def _find_paragraphs(self, position: Optional[Position] = None) -> List[TextObjectRef]:
        """
        Searches for paragraph objects returning TextObjectRef with hierarchical structure.
        """
        request_data = FindRequest(ObjectType.PARAGRAPH, position).to_dict()
        response = self._make_request('POST', '/pdf/find', data=request_data)

        objects_data = response.json()
        return [self._parse_text_object_ref(obj_data) for obj_data in objects_data]

    def _find_images(self, position: Optional[Position] = None) -> List[ObjectRef]:
        """
        Searches for image objects at the specified position.
        """
        return self._find(ObjectType.IMAGE, position)

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

    def _find_form_x_objects(self, position: Optional[Position] = None) -> List[ObjectRef]:
        """
        Searches for form field objects at the specified position.
        """
        return self._find(ObjectType.FORM_X_OBJECT, position)

    def select_form_fields(self) -> List[FormFieldObject]:
        """
        Searches for form field objects in the whole document.
        """
        return self._to_form_field_objects(self._find_form_fields(None))

    def select_form_fields_by_name(self, field_name: str) -> List[FormFieldObject]:
        """
        Searches for form field objects in the whole document.
        """
        return self._to_form_field_objects(self._find_form_fields(Position.by_name(field_name)))

    def _find_form_fields(self, position: Optional[Position] = None) -> List[FormFieldRef]:
        """
        Searches for form fields at the specified position.
        Returns FormFieldRef objects with name and value properties.
        """
        request_data = FindRequest(ObjectType.FORM_FIELD, position).to_dict()
        response = self._make_request('POST', '/pdf/find', data=request_data)

        # Parse response into ObjectRef objects
        objects_data = response.json()
        return [self._parse_form_field_ref(obj_data) for obj_data in objects_data]

    def _change_form_field(self, form_field_ref: FormFieldRef, new_value: str) -> bool:
        """
        Changes the value of a form field.
        """
        if form_field_ref is None:
            raise ValidationException("Form field reference cannot be null")

        request_data = ChangeFormFieldRequest(form_field_ref, new_value).to_dict()
        response = self._make_request('PUT', '/pdf/modify/formField', data=request_data)
        return response.json()

    def select_paths(self) -> List[ObjectRef]:
        """
        Searches for vector path objects at the specified position.
        """
        return self._find(ObjectType.PATH, None)

    def _find_paths(self, position: Optional[Position] = None) -> List[ObjectRef]:
        """
        Searches for vector path objects at the specified position.
        """
        return self._find(ObjectType.PATH, position)

    def _find_text_lines(self, position: Optional[Position] = None) -> List[TextObjectRef]:
        """
        Searches for text line objects returning TextObjectRef with hierarchical structure.
        """
        request_data = FindRequest(ObjectType.TEXT_LINE, position).to_dict()
        response = self._make_request('POST', '/pdf/find', data=request_data)

        objects_data = response.json()
        return [self._parse_text_object_ref(obj_data) for obj_data in objects_data]

    def select_text_lines(self) -> List[TextLineObject]:
        """
        Searches for text line objects returning TextLineObject wrappers.
        """
        return self._to_textline_objects(self._find_text_lines(None))

    def page(self, page_index: int) -> PageClient:
        """
        Get a specific page by index, fetching page properties from the server.

        Args:
            page_index: The 0-based page index

        Returns:
            PageClient with page properties populated
        """
        page_ref = self._get_page(page_index)
        if page_ref:
            return PageClient.from_ref(self, page_ref)
        else:
            # Fallback to basic PageClient if page not found
            return PageClient(page_index, self)

    # Page Operations

    def pages(self) -> List[PageClient]:
        return self._to_page_objects(self._get_pages())

    def _get_pages(self) -> List[PageRef]:
        """
        Retrieves references to all pages in the PDF document.
        """
        response = self._make_request('POST', '/pdf/page/find')
        pages_data = response.json()
        return [self._parse_page_ref(page_data) for page_data in pages_data]

    def _get_page(self, page_index: int) -> Optional[PageRef]:
        """
        Retrieves a reference to a specific page by its page index.

        Args:
            page_index: The page index to retrieve (1-based indexing)

        Returns:
            Page reference for the specified page, or None if not found
        """
        if page_index < 0:
            raise ValidationException(f"Page index must be >= 0, got {page_index}")

        params = {'pageIndex': page_index}
        response = self._make_request('POST', '/pdf/page/find', params=params)

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

        response = self._make_request('DELETE', '/pdf/page/delete', data=request_data)
        return response.json()

    def move_page(self, from_page_index: int, to_page_index: int) -> bool:
        """Move a page to a different index within the document."""
        return self._move_page(from_page_index, to_page_index)

    def _move_page(self, from_page_index: int, to_page_index: int) -> bool:
        """Internal helper to perform the page move operation."""
        for value, label in ((from_page_index, "from_page_index"), (to_page_index, "to_page_index")):
            if value is None:
                raise ValidationException(f"{label} cannot be null")
            if not isinstance(value, int):
                raise ValidationException(f"{label} must be an integer, got {type(value)}")
            if value < 0:
                raise ValidationException(f"{label} must be >= 0, got {value}")

        request_data = PageMoveRequest(from_page_index, to_page_index).to_dict()
        response = self._make_request('PUT', '/pdf/page/move', data=request_data)
        result = response.json()
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
        response = self._make_request('DELETE', '/pdf/delete', data=request_data)
        return response.json()

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
        response = self._make_request('PUT', '/pdf/move', data=request_data)
        return response.json()

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
        if paragraph.get_position().page_index is None:
            raise ValidationException("Paragraph position page index is null")
        if paragraph.get_position().page_index < 0:
            raise ValidationException("Paragraph position page index is less than 0")

        return self._add_object(paragraph)

    def _add_object(self, pdf_object) -> bool:
        """
        Internal method to add any PDF object.
        """
        request_data = AddRequest(pdf_object).to_dict()
        response = self._make_request('POST', '/pdf/add', data=request_data)
        return response.json()

    def new_paragraph(self) -> ParagraphBuilder:
        return ParagraphBuilder(self)

    def new_page(self):
        response = self._make_request('POST', '/pdf/page/add', data=None)
        return self._parse_page_ref(response.json())

    def new_image(self) -> ImageBuilder:
        return ImageBuilder(self)

    # Modify Operations
    def _modify_paragraph(self, object_ref: ObjectRef, new_paragraph: Union[Paragraph, str]) -> CommandResult:
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
            response = self._make_request('PUT', '/pdf/text/paragraph', data=request_data)
            return CommandResult.from_dict(response.json())
        else:
            # Object modification
            request_data = ModifyRequest(object_ref, new_paragraph).to_dict()
            response = self._make_request('PUT', '/pdf/modify', data=request_data)
            return CommandResult.from_dict(response.json())

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
        response = self._make_request('PUT', '/pdf/text/line', data=request_data)
        return CommandResult.from_dict(response.json())

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

        params = {'fontName': font_name.strip()}
        response = self._make_request('GET', '/font/find', params=params)

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
                filename = 'font.ttf'

            elif isinstance(ttf_file, (Path, str)):
                font_path = Path(ttf_file)
                if not font_path.exists():
                    raise ValidationException(f"TTF file does not exist: {font_path}")
                if not font_path.is_file():
                    raise ValidationException(f"TTF file is not a file: {font_path}")
                if not font_path.stat().st_size > 0:
                    raise ValidationException(f"TTF file is empty: {font_path}")

                with open(font_path, 'rb') as f:
                    font_data = f.read()
                filename = font_path.name

            elif hasattr(ttf_file, 'read'):
                font_data = ttf_file.read()
                if isinstance(font_data, str):
                    font_data = font_data.encode('utf-8')
                if len(font_data) == 0:
                    raise ValidationException("Font data from file-like object is empty")
                filename = getattr(ttf_file, 'name', 'font.ttf')

            else:
                raise ValidationException(f"Unsupported font file type: {type(ttf_file)}")

            # Upload font file
            files = {
                'ttfFile': (filename, font_data, 'font/ttf')
            }

            request_size = len(font_data)
            if DEBUG:
                print(f"{time.time()}|POST /font/register - request size: {request_size} bytes")

            headers = {'X-Session-Id': self._session_id}
            response = self._session.post(
                self._cleanup_url_path(self._base_url, "/font/register"),
                files=files,
                headers=headers,
                timeout=30,
                verify=not DISABLE_SSL_VERIFY
            )

            response_size = len(response.content)
            if DEBUG:
                print(f"{time.time()}|POST /font/register - response size: {response_size} bytes")

            response.raise_for_status()
            return response.text.strip()

        except (IOError, OSError) as e:
            raise PdfDancerException(f"Failed to read font file: {e}", cause=e)
        except requests.exceptions.RequestException as e:
            error_message = self._extract_error_message(getattr(e, 'response', None))
            raise HttpClientException(f"Font registration failed: {error_message}",
                                      response=getattr(e, 'response', None), cause=e) from None

    # Document Operations

    def get_bytes(self) -> bytes:
        """
        Downloads the current state of the PDF document with all modifications applied.

        Returns:
            PDF file data as bytes with all session modifications applied
        """
        response = self._make_request('GET', f'/session/{self._session_id}/pdf')
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

            with open(output_path, 'wb') as f:
                f.write(pdf_data)

        except (IOError, OSError) as e:
            raise PdfDancerException(f"Failed to save PDF file: {e}", cause=e)

    # Utility Methods

    def _parse_object_ref(self, obj_data: dict) -> ObjectRef:
        """Parse JSON object data into ObjectRef instance."""
        position_data = obj_data.get('position', {})
        position = self._parse_position(position_data) if position_data else None

        object_type = ObjectType(obj_data['type'])

        return ObjectRef(
            internal_id=obj_data['internalId'] if 'internalId' in obj_data else None,
            position=position,
            type=object_type
        )

    def _parse_form_field_ref(self, obj_data: dict) -> FormFieldRef:
        """Parse JSON object data into ObjectRef instance."""
        position_data = obj_data.get('position', {})
        position = self._parse_position(position_data) if position_data else None

        object_type = ObjectType(obj_data['type'])

        return FormFieldRef(
            internal_id=obj_data['internalId'] if 'internalId' in obj_data else None,
            position=position,
            type=object_type,
            name=obj_data['name'] if 'name' in obj_data else None,
            value=obj_data['value'] if 'value' in obj_data else None,
        )

    @staticmethod
    def _parse_position(pos_data: dict) -> Position:
        """Parse JSON position data into Position instance."""
        position = Position()
        position.page_index = pos_data.get('pageIndex')
        position.text_starts_with = pos_data.get('textStartsWith')

        if 'shape' in pos_data:
            position.shape = ShapeType(pos_data['shape'])
        if 'mode' in pos_data:
            position.mode = PositionMode(pos_data['mode'])

        if 'boundingRect' in pos_data:
            rect_data = pos_data['boundingRect']
            from .models import BoundingRect
            position.bounding_rect = BoundingRect(
                x=rect_data['x'],
                y=rect_data['y'],
                width=rect_data['width'],
                height=rect_data['height']
            )

        return position

    def _parse_text_object_ref(self, obj_data: dict, fallback_id: Optional[str] = None) -> TextObjectRef:
        """Parse JSON object data into TextObjectRef instance with hierarchical structure."""
        position_data = obj_data.get('position', {})
        position = self._parse_position(position_data) if position_data else Position()

        object_type = ObjectType(obj_data.get('type', 'TEXT_LINE'))
        line_spacings = obj_data.get('lineSpacings') if isinstance(obj_data.get('lineSpacings'), list) else None
        internal_id = obj_data.get('internalId', fallback_id or '')

        color = None
        color_data = obj_data.get('color')
        if isinstance(color_data, dict):
            from .models import Color
            red = color_data.get('red')
            green = color_data.get('green')
            blue = color_data.get('blue')
            alpha = color_data.get('alpha', 255)
            if all(isinstance(v, int) for v in [red, green, blue]):
                color = Color(red, green, blue, alpha)

        # Parse status if present
        status = None
        status_data = obj_data.get('status')
        if isinstance(status_data, dict):
            from .models import TextStatus, FontRecommendation, FontType

            # Parse font recommendation
            font_rec_data = status_data.get('fontRecommendation')
            font_rec = None
            if isinstance(font_rec_data, dict):
                font_rec = FontRecommendation(
                    font_name=font_rec_data.get('fontName', ''),
                    font_type=FontType(font_rec_data.get('fontType', 'SYSTEM')),
                    similarity_score=font_rec_data.get('similarityScore', 0.0)
                )

            status = TextStatus(
                modified=status_data.get('modified', False),
                encodable=status_data.get('encodable', True),
                font_type=FontType(status_data.get('fontType', 'UNKNOWN')),
                font_recommendation=font_rec
            )

        text_object = TextObjectRef(
            internal_id=internal_id,
            position=position,
            object_type=object_type,
            text=obj_data.get('text') if isinstance(obj_data.get('text'), str) else None,
            font_name=obj_data.get('fontName') if isinstance(obj_data.get('fontName'), str) else None,
            font_size=obj_data.get('fontSize') if isinstance(obj_data.get('fontSize'), (int, float)) else None,
            line_spacings=line_spacings,
            color=color,
            status=status
        )

        if isinstance(obj_data.get('children'), list) and len(obj_data['children']) > 0:
            text_object.children = [
                self._parse_text_object_ref(child_data, f"{internal_id or 'child'}-{index}")
                for index, child_data in enumerate(obj_data['children'])
            ]

        return text_object

    def _parse_page_ref(self, obj_data: dict) -> PageRef:
        """Parse JSON object data into PageRef instance with page-specific properties."""
        position_data = obj_data.get('position', {})
        position = self._parse_position(position_data) if position_data else None

        object_type = ObjectType(obj_data['type'])

        # Parse page size if present
        page_size = None
        if 'pageSize' in obj_data and isinstance(obj_data['pageSize'], dict):
            page_size_data = obj_data['pageSize']
            try:
                page_size = PageSize.from_dict(page_size_data)
            except ValueError:
                page_size = None

        # Parse orientation if present
        orientation_value = obj_data.get('orientation')
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
            internal_id=obj_data.get('internalId'),
            position=position,
            type=object_type,
            page_size=page_size,
            orientation=orientation
        )

    # Builder Pattern Support

    def _paragraph_builder(self) -> 'ParagraphBuilder':
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
        # TODO Could add session cleanup here if API supports it. Cleanup on the server
        pass

    def _to_path_objects(self, refs: List[ObjectRef]) -> List[PathObject]:
        return [PathObject(self, ref.internal_id, ref.type, ref.position) for ref in refs]

    def _to_paragraph_objects(self, refs: List[TextObjectRef]) -> List[ParagraphObject]:
        return [ParagraphObject(self, ref) for ref in refs]

    def _to_textline_objects(self, refs: List[TextObjectRef]) -> List[TextLineObject]:
        return [TextLineObject(self, ref) for ref in refs]

    def _to_image_objects(self, refs: List[ObjectRef]) -> List[ImageObject]:
        return [ImageObject(self, ref.internal_id, ref.type, ref.position) for ref in refs]

    def _to_form_objects(self, refs: List[ObjectRef]) -> List[FormObject]:
        return [FormObject(self, ref.internal_id, ref.type, ref.position) for ref in refs]

    def _to_form_field_objects(self, refs: List[FormFieldRef]) -> List[FormFieldObject]:
        return [FormFieldObject(self, ref.internal_id, ref.type, ref.position, ref.name, ref.value) for ref in
                refs]

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
                result.append(ImageObject(self, ref.internal_id, ref.type, ref.position))
            elif ref.type == ObjectType.PATH:
                result.append(PathObject(self, ref.internal_id, ref.type, ref.position))
            elif ref.type == ObjectType.FORM_X_OBJECT:
                result.append(FormObject(self, ref.internal_id, ref.type, ref.position))
            elif ref.type == ObjectType.FORM_FIELD:
                if isinstance(ref, FormFieldRef):
                    result.append(FormFieldObject(self, ref.internal_id, ref.type, ref.position, ref.name, ref.value))
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
