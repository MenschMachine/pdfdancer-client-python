"""
PDFDancer Python Client V1

A Python client that closely mirrors the Java Client class structure and functionality.
Provides session-based PDF manipulation operations with strict validation.
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Union, BinaryIO

import requests

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
    ObjectRef, Position, ObjectType, Font, Image, Paragraph, FormFieldRef,
    FindRequest, DeleteRequest, MoveRequest, AddRequest, ModifyRequest, ModifyTextRequest, ChangeFormFieldRequest,
    ShapeType, PositionMode
)
from .paragraph_builder import ParagraphPageBuilder
from .types import PathObject, ParagraphObject, TextLineObject, ImageObject, FormObject, FormFieldObject


class PageClient:
    def __init__(self, page_index: int, root: "PDFDancer"):
        self.page_index = page_index
        self.root = root
        self.object_type = ObjectType.PAGE
        self.position = Position.at_page(page_index)
        self.internal_id = f"PAGE-{page_index}"

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
    def from_ref(cls, root: 'PDFDancer', object_ref: ObjectRef) -> 'PageClient':
        page_client = PageClient(page_index=object_ref.position.page_index, root=root)
        return page_client

    def delete(self) -> bool:
        # noinspection PyProtectedMember
        return self.root._delete_page(self._ref())

    def _ref(self):
        return ObjectRef(internal_id=self.internal_id, position=self.position, type=self.object_type)

    def new_paragraph(self):
        return ParagraphPageBuilder(self.root, self.page_index)


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
        resolved_token = token.strip() if token and token.strip() else None
        if resolved_token is None:
            env_token = os.getenv("PDFDANCER_TOKEN")
            resolved_token = env_token.strip() if env_token and env_token.strip() else None

        if resolved_token is None:
            raise ValidationException(
                "Missing PDFDancer API token. Pass a token via the `token` argument "
                "or set the PDFDANCER_TOKEN environment variable."
            )

        env_base_url = os.getenv("PDFDANCER_BASE_URL")
        resolved_base_url = base_url or (env_base_url.strip() if env_base_url and env_base_url.strip() else None)
        if resolved_base_url is None:
            resolved_base_url = "https://api.pdfdancer.com"

        return PDFDancer(resolved_token, pdf_data, resolved_base_url, timeout)

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

    def _process_pdf_data(self, pdf_data: Union[bytes, Path, str, BinaryIO]) -> bytes:
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

    def _create_session(self) -> str:
        """
        Creates a new PDF processing session by uploading the PDF data.
        """
        try:
            files = {
                'pdf': ('document.pdf', self._pdf_bytes, 'application/pdf')
            }

            response = self._session.post(
                f"{self._base_url}/session/create",
                files=files,
                timeout=self._read_timeout if self._read_timeout > 0 else None
            )

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
            response = self._session.request(
                method=method,
                url=f"{self._base_url}{path}",
                json=data,
                params=params,
                headers=headers,
                timeout=self._read_timeout if self._read_timeout > 0 else None
            )

            # Handle FontNotFoundException specifically like Java client
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

    # Search Operations - matching Java client exactly

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

    def select_paragraphs(self) -> List[ParagraphObject]:
        """
        Searches for paragraph objects at the specified position.
        """
        return self._to_paragraph_objects(self._find(ObjectType.PARAGRAPH, None))

    def _find_paragraphs(self, position: Optional[Position] = None) -> List[ObjectRef]:
        """
        Searches for paragraph objects at the specified position.
        """
        return self._find(ObjectType.PARAGRAPH, position)

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

    def _find_text_lines(self, position: Optional[Position] = None) -> List[ObjectRef]:
        """
        Searches for text line objects at the specified position.
        """
        return self._find(ObjectType.TEXT_LINE, position)

    def select_text_lines(self) -> List[TextLineObject]:
        """
        Searches for text line objects at the specified position.
        """
        return self._to_textline_objects(self._find(ObjectType.TEXT_LINE, None))

    def page(self, page_index: int) -> PageClient:
        return PageClient(page_index, self)

    # Page Operations

    def pages(self) -> List[PageClient]:
        return self._to_page_objects(self._get_pages())

    def _get_pages(self) -> List[ObjectRef]:
        """
        Retrieves references to all pages in the PDF document.
        """
        response = self._make_request('POST', '/pdf/page/find')
        pages_data = response.json()
        return [self._parse_object_ref(page_data) for page_data in pages_data]

    def _get_page(self, page_index: int) -> Optional[ObjectRef]:
        """
        Retrieves a reference to a specific page by its page index.

        Args:
            page_index: The page index to retrieve (1-based indexing)

        Returns:
            Object reference for the specified page, or None if not found
        """
        if page_index < 0:
            raise ValidationException(f"Page index must be >= 0, got {page_index}")

        params = {'pageIndex': page_index}
        response = self._make_request('POST', '/pdf/page/find', params=params)

        pages_data = response.json()
        if not pages_data:
            return None

        return self._parse_object_ref(pages_data[0])

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

    def new_image(self) -> ImageBuilder:
        return ImageBuilder(self)

    # Modify Operations
    def _modify_paragraph(self, object_ref: ObjectRef, new_paragraph: Union[Paragraph, str]) -> bool:
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
            raise ValidationException("New paragraph cannot be null")

        if isinstance(new_paragraph, str):
            # Text modification
            request_data = ModifyTextRequest(object_ref, new_paragraph).to_dict()
            response = self._make_request('PUT', '/pdf/text/paragraph', data=request_data)
        else:
            # Object modification
            request_data = ModifyRequest(object_ref, new_paragraph).to_dict()
            response = self._make_request('PUT', '/pdf/modify', data=request_data)

        return response.json()

    def _modify_text_line(self, object_ref: ObjectRef, new_text: str) -> bool:
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
        return response.json()

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

            headers = {'X-Session-Id': self._session_id}
            response = self._session.post(
                f"{self._base_url}/font/register",
                files=files,
                headers=headers,
                timeout=30
            )

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

    def _parse_form_field_ref(self, obj_data: dict) -> ObjectRef:
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
        # Could add session cleanup here if API supports it
        pass

    def _to_path_objects(self, path_refs: List[ObjectRef]) -> List[PathObject]:
        return [PathObject(self, ref.internal_id, ref.type, ref.position) for ref in path_refs]

    def _to_paragraph_objects(self, path_refs: List[ObjectRef]) -> List[ParagraphObject]:
        return [ParagraphObject(self, ref.internal_id, ref.type, ref.position) for ref in path_refs]

    def _to_textline_objects(self, path_refs: List[ObjectRef]) -> List[TextLineObject]:
        return [TextLineObject(self, ref.internal_id, ref.type, ref.position) for ref in path_refs]

    def _to_image_objects(self, path_refs: List[ObjectRef]) -> List[ImageObject]:
        return [ImageObject(self, ref.internal_id, ref.type, ref.position) for ref in path_refs]

    def _to_form_objects(self, path_refs: List[ObjectRef]) -> List[FormObject]:
        return [FormObject(self, ref.internal_id, ref.type, ref.position) for ref in path_refs]

    def _to_form_field_objects(self, path_refs: List[FormFieldRef]) -> List[FormFieldObject]:
        return [FormFieldObject(self, ref.internal_id, ref.type, ref.position, ref.name, ref.value) for ref in
                path_refs]

    def _to_page_objects(self, path_refs: List[ObjectRef]) -> List[PageClient]:
        return [PageClient.from_ref(self, ref) for ref in path_refs]

    def _to_page_object(self, ref: ObjectRef) -> PageClient:
        return PageClient.from_ref(self, ref)
