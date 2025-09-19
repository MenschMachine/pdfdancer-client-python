"""
Tests for ClientV1 class - mirrors Java client test patterns.
"""

from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest
import requests

from pdfdancer import (
    ClientV1, ObjectRef, Position, ObjectType, Image, Paragraph,
    FontNotFoundException, ValidationException
)


class TestClientV1:
    """Test ClientV1 functionality matching Java client patterns."""

    def test_constructor_with_bytes_creates_session(self):
        """Test constructor with PDF bytes creates session successfully."""
        pdf_data = b'%PDF-1.4 fake pdf data'
        token = 'test-token'

        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock session creation response
            mock_response = Mock()
            mock_response.text = 'session-123'
            mock_response.raise_for_status.return_value = None
            mock_session.post.return_value = mock_response

            client = ClientV1(token=token, pdf_data=pdf_data)

            # Verify session creation was called
            mock_session.post.assert_called_once()
            args, kwargs = mock_session.post.call_args
            assert '/session/create' in args[0]
            assert 'files' in kwargs
            assert client._session_id == 'session-123'

    def test_constructor_with_file_path_reads_file(self):
        """Test constructor with file path reads PDF file."""
        token = 'test-token'
        pdf_content = b'%PDF-1.4 fake pdf content'

        with patch('pathlib.Path.exists', return_value=True), \
                patch('pathlib.Path.is_file', return_value=True), \
                patch('pathlib.Path.stat') as mock_stat, \
                patch('builtins.open', mock_open(read_data=pdf_content)), \
                patch('requests.Session') as mock_session_class:
            mock_stat.return_value.st_size = len(pdf_content)
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.text = 'session-456'
            mock_response.raise_for_status.return_value = None
            mock_session.post.return_value = mock_response

            client = ClientV1(token=token, pdf_data='test.pdf')

            assert client._session_id == 'session-456'

    def test_constructor_validation_empty_token_raises_exception(self):
        """Test constructor validates token is not empty."""
        with pytest.raises(ValidationException, match="Authentication token cannot be null or empty"):
            ClientV1(token='', pdf_data=b'fake pdf')

    def test_constructor_validation_null_token_raises_exception(self):
        """Test constructor validates token is not null."""
        with pytest.raises(ValidationException, match="Authentication token cannot be null or empty"):
            ClientV1(token=None, pdf_data=b'fake pdf')

    def test_constructor_validation_empty_pdf_data_raises_exception(self):
        """Test constructor validates PDF data is not empty."""
        with pytest.raises(ValidationException, match="PDF data cannot be empty"):
            ClientV1(token='test-token', pdf_data=b'')

    def test_constructor_validation_null_pdf_data_raises_exception(self):
        """Test constructor validates PDF data is not null."""
        with pytest.raises(ValidationException, match="PDF data cannot be null"):
            ClientV1(token='test-token', pdf_data=None)

    def test_constructor_validation_nonexistent_file_raises_exception(self):
        """Test constructor validates file exists."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(ValidationException, match="PDF file does not exist"):
                ClientV1(token='test-token', pdf_data='nonexistent.pdf')

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing API methods."""
        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock successful session creation
            mock_response = Mock()
            mock_response.text = 'test-session-id'
            mock_response.raise_for_status.return_value = None
            mock_session.post.return_value = mock_response

            client = ClientV1(token='test-token', pdf_data=b'%PDF fake data')
            client._session = mock_session  # Keep reference for assertions
            return client

    def test_find_paragraphs_calls_correct_endpoint(self, mock_client):
        """Test find_paragraphs calls the correct API endpoint."""
        position = Position.at_page(0)

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'internalId': 'para-1',
                'type': 'PARAGRAPH',
                'position': {'pageIndex': 0}
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_client._session.request.return_value = mock_response

        results = mock_client.find_paragraphs(position)

        # Verify API call
        mock_client._session.request.assert_called_once()
        call_args = mock_client._session.request.call_args
        assert call_args[1]['method'] == 'POST'
        assert '/pdf/find' in call_args[1]['url']

        # Verify request data
        request_data = call_args[1]['json']
        assert request_data['objectType'] == 'PARAGRAPH'
        assert request_data['position']['pageIndex'] == 0

        # Verify response parsing
        assert len(results) == 1
        assert results[0].internal_id == 'para-1'
        assert results[0].type == ObjectType.PARAGRAPH

    def test_find_images_with_position(self, mock_client):
        """Test find_images with position constraint."""
        position = Position.at_page_coordinates(1, 100.0, 200.0)

        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_client._session.request.return_value = mock_response

        results = mock_client.find_images(position)

        # Verify correct object type was requested
        call_args = mock_client._session.request.call_args
        request_data = call_args[1]['json']
        assert request_data['objectType'] == 'IMAGE'
        assert request_data['position']['pageIndex'] == 1
        assert request_data['position']['boundingRect']['x'] == 100.0
        assert request_data['position']['boundingRect']['y'] == 200.0

    def test_delete_object_validates_input(self, mock_client):
        """Test delete method validates object reference."""
        with pytest.raises(ValidationException, match="Object reference cannot be null"):
            mock_client.delete(None)

    def test_delete_object_success(self, mock_client):
        """Test successful object deletion."""
        obj_ref = ObjectRef(
            internal_id='obj-1',
            position=Position.at_page(0),
            type=ObjectType.PARAGRAPH
        )

        mock_response = Mock()
        mock_response.json.return_value = True
        mock_response.raise_for_status.return_value = None
        mock_client._session.request.return_value = mock_response

        result = mock_client.delete(obj_ref)

        assert result is True

        # Verify API call
        call_args = mock_client._session.request.call_args
        assert call_args[1]['method'] == 'DELETE'
        assert '/pdf/delete' in call_args[1]['url']

    def test_move_object_validates_inputs(self, mock_client):
        """Test move method validates inputs."""
        obj_ref = ObjectRef('obj-1', Position.at_page(0), ObjectType.PARAGRAPH)
        position = Position.at_page_coordinates(0, 50.0, 75.0)

        # Test null object reference
        with pytest.raises(ValidationException, match="Object reference cannot be null"):
            mock_client.move(None, position)

        # Test null position
        with pytest.raises(ValidationException, match="Position cannot be null"):
            mock_client.move(obj_ref, None)

    def test_add_image_validates_input(self, mock_client):
        """Test add_image validates input."""
        with pytest.raises(ValidationException, match="Image cannot be null"):
            mock_client.add_image(None)

        # Test image without position
        image = Image()
        with pytest.raises(ValidationException, match="Image position is null"):
            mock_client.add_image(image)

    def test_add_image_with_position_override(self, mock_client):
        """Test add_image with position parameter."""
        image = Image()
        position = Position.at_page_coordinates(0, 100.0, 150.0)

        mock_response = Mock()
        mock_response.json.return_value = True
        mock_response.raise_for_status.return_value = None
        mock_client._session.request.return_value = mock_response

        result = mock_client.add_image(image, position)

        assert result is True
        assert image.get_position() == position

    def test_add_paragraph_validates_strict_requirements(self, mock_client):
        """Test add_paragraph has strict validation like Java client."""
        paragraph = Paragraph()

        # Test null paragraph
        with pytest.raises(ValidationException, match="Paragraph cannot be null"):
            mock_client.add_paragraph(None)

        # Test paragraph without position
        with pytest.raises(ValidationException, match="Paragraph position is null"):
            mock_client.add_paragraph(paragraph)

        # Test paragraph with position but no page index
        paragraph.set_position(Position())
        with pytest.raises(ValidationException, match="Paragraph position page index is null"):
            mock_client.add_paragraph(paragraph)

        # Test paragraph with negative page index
        paragraph.set_position(Position.at_page(-1))
        with pytest.raises(ValidationException, match="Paragraph position page index is less than 0"):
            mock_client.add_paragraph(paragraph)

    def test_get_pages_returns_page_references(self, mock_client):
        """Test get_pages returns list of page object references."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {'internalId': 'page-1', 'type': 'PAGE', 'position': {'pageIndex': 0}},
            {'internalId': 'page-2', 'type': 'PAGE', 'position': {'pageIndex': 1}}
        ]
        mock_response.raise_for_status.return_value = None
        mock_client._session.request.return_value = mock_response

        pages = mock_client.get_pages()

        assert len(pages) == 2
        assert pages[0].internal_id == 'page-1'
        assert pages[1].internal_id == 'page-2'

    def test_get_page_with_valid_page_index(self, mock_client):
        """Test get_page with valid page index."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {'internalId': 'page-1', 'type': 'PAGE', 'position': {'pageIndex': 0}}
        ]
        mock_response.raise_for_status.return_value = None
        mock_client._session.request.return_value = mock_response

        page = mock_client.get_page(1)

        assert page is not None
        assert page.internal_id == 'page-1'

        # Verify correct parameter was sent
        call_args = mock_client._session.request.call_args
        assert call_args[1]['params']['pageIndex'] == 1

    def test_get_page_with_invalid_page_index_raises_exception(self, mock_client):
        """Test get_page validates page index is positive or zero."""
        with pytest.raises(ValidationException, match="Page index must be >= 0, got"):
            mock_client.get_page(-1)

    def test_get_page_returns_none_when_not_found(self, mock_client):
        """Test get_page returns None when page not found."""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_client._session.request.return_value = mock_response

        page = mock_client.get_page(999)

        assert page is None

    def test_find_fonts_validates_inputs(self, mock_client):
        """Test find_fonts validates inputs like Java client."""
        with pytest.raises(ValidationException, match="Font name cannot be null or empty"):
            mock_client.find_fonts('', 12)

        with pytest.raises(ValidationException, match="Font name cannot be null or empty"):
            mock_client.find_fonts(None, 12)

        with pytest.raises(ValidationException, match="Font size must be positive"):
            mock_client.find_fonts('Arial', 0)

        with pytest.raises(ValidationException, match="Font size must be positive"):
            mock_client.find_fonts('Arial', -5)

    def test_find_fonts_returns_font_objects(self, mock_client):
        """Test find_fonts returns proper Font objects."""
        mock_response = Mock()
        mock_response.json.return_value = ['Arial', 'Arial-Bold']
        mock_response.raise_for_status.return_value = None
        mock_client._session.request.return_value = mock_response

        fonts = mock_client.find_fonts('Arial', 12)

        assert len(fonts) == 2
        assert fonts[0].name == 'Arial'
        assert fonts[0].size == 12
        assert fonts[1].name == 'Arial-Bold'
        assert fonts[1].size == 12

    def test_register_font_validates_inputs(self, mock_client):
        """Test register_font validates inputs strictly."""
        with pytest.raises(ValidationException, match="TTF file cannot be null"):
            mock_client.register_font(None)

        # Test with non-existent file
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(ValidationException, match="TTF file does not exist"):
                mock_client.register_font('nonexistent.ttf')

    def test_font_not_found_exception_handling(self, mock_client):
        """Test FontNotFoundException is raised for 404 with proper error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': 'FontNotFoundException',
            'message': 'Font Arial not found'
        }
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_client._session.request.return_value = mock_response

        with pytest.raises(FontNotFoundException, match="Font Arial not found"):
            mock_client.find_fonts('Arial', 12)

    def test_get_pdf_file_returns_bytes(self, mock_client):
        """Test get_pdf_file returns PDF content as bytes."""
        pdf_content = b'%PDF-1.4 modified pdf content'

        mock_response = Mock()
        mock_response.content = pdf_content
        mock_response.raise_for_status.return_value = None
        mock_client._session.request.return_value = mock_response

        result = mock_client.get_pdf_file()

        assert result == pdf_content

        # Verify correct endpoint was called
        call_args = mock_client._session.request.call_args
        assert f'/session/{mock_client._session_id}/pdf' in call_args[1]['url']

    def test_save_pdf_writes_file(self, mock_client):
        """Test save_pdf writes PDF content to file."""
        pdf_content = b'%PDF-1.4 test content'

        mock_response = Mock()
        mock_response.content = pdf_content
        mock_response.raise_for_status.return_value = None
        mock_client._session.request.return_value = mock_response

        with patch('pathlib.Path.mkdir'), \
                patch('builtins.open', mock_open()) as mock_file:
            mock_client.save_pdf('output.pdf')

            # Verify file was written with correct content
            mock_file.assert_called_once_with(Path('output.pdf'), 'wb')
            handle = mock_file()
            handle.write.assert_called_once_with(pdf_content)

    def test_save_pdf_validates_file_path(self, mock_client):
        """Test save_pdf validates file path."""
        with pytest.raises(ValidationException, match="File path cannot be null or empty"):
            mock_client.save_pdf('')

        with pytest.raises(ValidationException, match="File path cannot be null or empty"):
            mock_client.save_pdf(None)

    def test_paragraph_builder_returns_builder_instance(self, mock_client):
        """Test paragraph_builder returns ParagraphBuilder instance."""
        builder = mock_client.paragraph_builder()

        from pdfdancer.paragraph_builder import ParagraphBuilder
        assert isinstance(builder, ParagraphBuilder)

    def test_context_manager_support(self):
        """Test client can be used as context manager."""
        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.text = 'session-ctx'
            mock_response.raise_for_status.return_value = None
            mock_session.post.return_value = mock_response

            with ClientV1(token='test-token', pdf_data=b'%PDF fake') as client:
                assert client._session_id == 'session-ctx'

    def test_modify_paragraph_with_text_string(self, mock_client):
        """Test modify_paragraph with text string."""
        obj_ref = ObjectRef('para-1', Position.at_page(0), ObjectType.PARAGRAPH)
        new_text = "Updated paragraph text"

        mock_response = Mock()
        mock_response.json.return_value = True
        mock_response.raise_for_status.return_value = None
        mock_client._session.request.return_value = mock_response

        result = mock_client.modify_paragraph(obj_ref, new_text)

        assert result is True

        # Verify correct endpoint for text modification
        call_args = mock_client._session.request.call_args
        assert '/pdf/text/paragraph' in call_args[1]['url']
        assert call_args[1]['json']['newTextLine'] == new_text

    def test_modify_text_line_validates_inputs(self, mock_client):
        """Test modify_text_line validates inputs."""
        obj_ref = ObjectRef('line-1', Position.at_page(0), ObjectType.TEXT_LINE)

        with pytest.raises(ValidationException, match="Object reference cannot be null"):
            mock_client.modify_text_line(None, "new text")

        with pytest.raises(ValidationException, match="New text cannot be null"):
            mock_client.modify_text_line(obj_ref, None)
