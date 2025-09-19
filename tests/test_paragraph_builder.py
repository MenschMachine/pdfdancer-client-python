"""
Tests for ParagraphBuilder class - mirrors Java builder test patterns.
"""

from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from pdfdancer import (
    ClientV1, ParagraphBuilder, Paragraph, Font, Color, Position,
    ValidationException
)


class TestParagraphBuilder:
    """Test ParagraphBuilder functionality matching Java patterns."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing builder."""
        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock successful session creation
            mock_response = Mock()
            mock_response.text = 'test-session-id'
            mock_response.raise_for_status.return_value = None
            mock_session.post.return_value = mock_response

            client = ClientV1(token='test-token', pdf_data=b'%PDF fake data')
            return client

    def test_constructor_validates_client(self):
        """Test constructor validates client is not null."""
        with pytest.raises(ValidationException, match="Client cannot be null"):
            ParagraphBuilder(None)

    def test_from_string_validates_text(self, mock_client):
        """Test from_string validates text input."""
        builder = ParagraphBuilder(mock_client)

        with pytest.raises(ValidationException, match="Text cannot be null"):
            builder.from_string(None)

        with pytest.raises(ValidationException, match="Text cannot be empty"):
            builder.from_string("")

        with pytest.raises(ValidationException, match="Text cannot be empty"):
            builder.from_string("   ")  # Only whitespace

    def test_from_string_sets_text_and_color(self, mock_client):
        """Test from_string sets text and optional color."""
        builder = ParagraphBuilder(mock_client)
        color = Color(255, 0, 0)  # Red

        result = builder.from_string("Test text", color)

        assert result is builder  # Returns self for chaining
        assert builder._text == "Test text"
        assert builder._text_color == color

    def test_from_string_without_color_uses_default(self, mock_client):
        """Test from_string without color uses default black."""
        builder = ParagraphBuilder(mock_client)

        builder.from_string("Test text")

        assert builder._text == "Test text"
        assert builder._text_color == Color(0, 0, 0)  # Default black

    def test_with_font_validates_input(self, mock_client):
        """Test with_font validates font input."""
        builder = ParagraphBuilder(mock_client)

        with pytest.raises(ValidationException, match="Font cannot be null"):
            builder.with_font(None)

    def test_with_font_sets_font_and_clears_ttf_file(self, mock_client):
        """Test with_font sets font and clears TTF file reference."""
        builder = ParagraphBuilder(mock_client)
        font = Font("Arial", 12.0)

        # First set a TTF file
        builder._ttf_file = Path("some_font.ttf")

        result = builder.with_font(font)

        assert result is builder
        assert builder._font == font
        assert builder._ttf_file is None  # Should be cleared

    def test_with_font_file_validates_inputs(self, mock_client):
        """Test with_font_file validates inputs strictly like Java."""
        builder = ParagraphBuilder(mock_client)

        # Test null file
        with pytest.raises(ValidationException, match="TTF file cannot be null"):
            builder.with_font_file(None, 12.0)

        # Test non-positive font size
        with pytest.raises(ValidationException, match="Font size must be positive"):
            builder.with_font_file("font.ttf", 0)

        with pytest.raises(ValidationException, match="Font size must be positive"):
            builder.with_font_file("font.ttf", -5.0)

        # Test non-existent file
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(ValidationException, match="TTF file does not exist"):
                builder.with_font_file("nonexistent.ttf", 12.0)

        # Test directory instead of file
        with patch('pathlib.Path.exists', return_value=True), \
                patch('pathlib.Path.is_file', return_value=False):
            with pytest.raises(ValidationException, match="TTF file is not a file"):
                builder.with_font_file("directory", 12.0)

        # Test empty file
        with patch('pathlib.Path.exists', return_value=True), \
                patch('pathlib.Path.is_file', return_value=True), \
                patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 0
            with pytest.raises(ValidationException, match="TTF file is empty"):
                builder.with_font_file("empty.ttf", 12.0)

    def test_with_font_file_validates_readability(self, mock_client):
        """Test with_font_file validates file is readable."""
        builder = ParagraphBuilder(mock_client)

        with patch('pathlib.Path.exists', return_value=True), \
                patch('pathlib.Path.is_file', return_value=True), \
                patch('pathlib.Path.stat') as mock_stat, \
                patch('builtins.open', side_effect=IOError("Permission denied")):
            mock_stat.return_value.st_size = 1000
            with pytest.raises(ValidationException, match="TTF file is not readable"):
                builder.with_font_file("unreadable.ttf", 12.0)

    def test_with_font_file_registers_font_successfully(self, mock_client):
        """Test with_font_file registers font and creates Font object."""
        builder = ParagraphBuilder(mock_client)

        with patch('pathlib.Path.exists', return_value=True), \
                patch('pathlib.Path.is_file', return_value=True), \
                patch('pathlib.Path.stat') as mock_stat, \
                patch('builtins.open', mock_open(read_data=b"fake ttf data")):
            mock_stat.return_value.st_size = 1000

            # Mock client's register_font method
            mock_client.register_font = Mock(return_value="CustomFont-Regular")

            result = builder.with_font_file("custom.ttf", 14.0)

            assert result is builder
            assert builder._font.name == "CustomFont-Regular"
            assert builder._font.size == 14.0
            assert builder._ttf_file == Path("custom.ttf")

            # Verify register_font was called
            mock_client.register_font.assert_called_once_with(Path("custom.ttf"))

    def test_with_line_spacing_validates_input(self, mock_client):
        """Test with_line_spacing validates spacing is positive."""
        builder = ParagraphBuilder(mock_client)

        with pytest.raises(ValidationException, match="Line spacing must be positive"):
            builder.with_line_spacing(0)

        with pytest.raises(ValidationException, match="Line spacing must be positive"):
            builder.with_line_spacing(-1.5)

    def test_with_line_spacing_sets_spacing(self, mock_client):
        """Test with_line_spacing sets spacing correctly."""
        builder = ParagraphBuilder(mock_client)

        result = builder.with_line_spacing(1.5)

        assert result is builder
        assert builder._line_spacing == 1.5

    def test_with_color_validates_input(self, mock_client):
        """Test with_color validates color input."""
        builder = ParagraphBuilder(mock_client)

        with pytest.raises(ValidationException, match="Color cannot be null"):
            builder.with_color(None)

    def test_with_color_sets_color(self, mock_client):
        """Test with_color sets text color."""
        builder = ParagraphBuilder(mock_client)
        color = Color(128, 128, 128)  # Gray

        result = builder.with_color(color)

        assert result is builder
        assert builder._text_color == color

    def test_with_position_validates_input(self, mock_client):
        """Test with_position validates position input."""
        builder = ParagraphBuilder(mock_client)

        with pytest.raises(ValidationException, match="Position cannot be null"):
            builder.with_position(None)

    def test_with_position_sets_position(self, mock_client):
        """Test with_position sets paragraph position."""
        builder = ParagraphBuilder(mock_client)
        position = Position.at_page_coordinates(0, 100.0, 200.0)

        result = builder.with_position(position)

        assert result is builder
        assert builder._paragraph.get_position() == position

    def test_build_validates_required_fields(self, mock_client):
        """Test build validates all required fields are set."""
        builder = ParagraphBuilder(mock_client)

        # Test missing text
        with pytest.raises(ValidationException, match="Text must be set before building paragraph"):
            builder.build()

        # Set text but missing font
        builder.from_string("Test text")
        with pytest.raises(ValidationException, match="Font must be set before building paragraph"):
            builder.build()

        # Set font but missing position
        font = Font("Arial", 12.0)
        builder.with_font(font)
        with pytest.raises(ValidationException, match="Position must be set before building paragraph"):
            builder.build()

    def test_build_creates_paragraph_successfully(self, mock_client):
        """Test build creates paragraph with all properties set."""
        builder = ParagraphBuilder(mock_client)
        font = Font("Arial", 12.0)
        color = Color(255, 0, 0)
        position = Position.at_page_coordinates(0, 50.0, 75.0)

        paragraph = (builder
                     .from_string("Test paragraph text\\nWith multiple lines", color)
                     .with_font(font)
                     .with_line_spacing(1.5)
                     .with_position(position)
                     .build())

        assert isinstance(paragraph, Paragraph)
        assert paragraph.font == font
        assert paragraph.color == color
        assert paragraph.line_spacing == 1.5
        assert paragraph.get_position() == position
        assert paragraph.text_lines == ["Test paragraph text", "With multiple lines"]

    def test_fluent_interface_chaining(self, mock_client):
        """Test fluent interface allows method chaining."""
        builder = ParagraphBuilder(mock_client)
        font = Font("Times", 14.0)
        color = Color(0, 0, 255)  # Blue
        position = Position.at_page(1)

        # Test that all methods return the builder for chaining
        result = (builder
                  .from_string("Chained text")
                  .with_font(font)
                  .with_color(color)
                  .with_line_spacing(2.0)
                  .with_position(position))

        assert result is builder

        # Verify final state
        paragraph = builder.build()
        assert paragraph.font == font
        assert paragraph.color == color
        assert paragraph.line_spacing == 2.0
        assert paragraph.get_position() == position

    def test_process_text_lines_handles_newlines(self, mock_client):
        """Test _process_text_lines handles newline characters correctly."""
        builder = ParagraphBuilder(mock_client)

        # Test simple text
        lines = builder._process_text_lines("Single line")
        assert lines == ["Single line"]

        # Test multiple lines
        lines = builder._process_text_lines("Line 1\\nLine 2\\nLine 3")
        assert lines == ["Line 1", "Line 2", "Line 3"]

        # Test empty lines at end are removed
        lines = builder._process_text_lines("Content\\n\\n\\n")
        assert lines == ["Content"]

        # Test empty input
        lines = builder._process_text_lines("")
        assert lines == [""]

    def test_default_values(self, mock_client):
        """Test builder has correct default values."""
        builder = ParagraphBuilder(mock_client)

        assert builder._line_spacing == 1.2
        assert builder._text_color == Color(0, 0, 0)  # Black
        assert builder._text is None
        assert builder._ttf_file is None
        assert builder._font is None

    def test_register_ttf_handles_font_registration_failure(self, mock_client):
        """Test _register_ttf handles font registration failures."""
        builder = ParagraphBuilder(mock_client)

        # Mock client register_font to raise an exception
        mock_client.register_font = Mock(side_effect=Exception("Registration failed"))

        with patch('pathlib.Path.exists', return_value=True), \
                patch('pathlib.Path.is_file', return_value=True), \
                patch('pathlib.Path.stat') as mock_stat, \
                patch('builtins.open', mock_open(read_data=b"fake ttf")):
            mock_stat.return_value.st_size = 1000

            with pytest.raises(ValidationException, match="Failed to register font file"):
                builder.with_font_file("failing.ttf", 12.0)
