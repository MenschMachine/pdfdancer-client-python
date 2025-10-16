"""
ParagraphBuilder for the PDFDancer Python client.
Closely mirrors the Java ParagraphBuilder class with Python conventions.
"""

from pathlib import Path
from typing import Optional, Union

from .exceptions import ValidationException
from .models import Paragraph, Font, Color, Position


class ParagraphBuilder:
    """
    Builder class for constructing Paragraph objects with fluent interface.
    Mirrors the Java ParagraphBuilder class exactly.
    """

    def __init__(self, client: 'PDFDancer'):
        """
        Initialize the paragraph builder with a client reference.

        Args:
            client: The ClientV1 instance for font registration
        """
        if client is None:
            raise ValidationException("Client cannot be null")

        self._client = client
        self._paragraph = Paragraph()
        self._line_spacing = 1.2
        self._text_color = Color(0, 0, 0)  # Black by default
        self._text: Optional[str] = None
        self._ttf_file: Optional[Path] = None
        self._font: Optional[Font] = None

    def text(self, text: str, color: Optional[Color] = None) -> 'ParagraphBuilder':
        """
        Set the text content for the paragraph.
        Equivalent to fromString() methods in Java ParagraphBuilder.

        Args:
            text: The text content for the paragraph
            color: Optional text color (uses default if not provided)

        Returns:
            Self for method chaining

        Raises:
            ValidationException: If text is None or empty
        """
        if text is None:
            raise ValidationException("Text cannot be null")
        if not text.strip():
            raise ValidationException("Text cannot be empty")

        self._text = text
        if color is not None:
            self._text_color = color

        return self

    def font(self, font_name: str, font_size: float) -> 'ParagraphBuilder':
        """
        Set the font for the paragraph using an existing Font object.
        Equivalent to withFont(Font) in Java ParagraphBuilder.

        Args:
            font_name: The Font to use
            font_size: The font size

        Returns:
            Self for method chaining

        Raises:
            ValidationException: If font is None
        """
        font = Font(font_name, font_size)
        if font is None:
            raise ValidationException("Font cannot be null")

        self._font = font
        self._ttf_file = None  # Clear TTF file when using existing font
        return self

    def font_file(self, ttf_file: Union[Path, str], font_size: float) -> 'ParagraphBuilder':
        """
        Set the font for the paragraph using a TTF file.
        Equivalent to withFont(File, double) in Java ParagraphBuilder.

        Args:
            ttf_file: Path to the TTF font file
            font_size: Size of the font

        Returns:
            Self for method chaining

        Raises:
            ValidationException: If TTF file is invalid or font size is not positive
        """
        if ttf_file is None:
            raise ValidationException("TTF file cannot be null")
        if font_size <= 0:
            raise ValidationException(f"Font size must be positive, got {font_size}")

        ttf_path = Path(ttf_file)

        # Strict validation like Java client
        if not ttf_path.exists():
            raise ValidationException(f"TTF file does not exist: {ttf_path}")
        if not ttf_path.is_file():
            raise ValidationException(f"TTF file is not a file: {ttf_path}")
        if not ttf_path.stat().st_size > 0:
            raise ValidationException(f"TTF file is empty: {ttf_path}")

        # Check file permissions
        try:
            with open(ttf_path, 'rb') as f:
                f.read(1)  # Try to read one byte to check readability
        except (IOError, OSError):
            raise ValidationException(f"TTF file is not readable: {ttf_path}")

        self._ttf_file = ttf_path
        self._font = self._register_ttf(ttf_path, font_size)
        return self

    def line_spacing(self, spacing: float) -> 'ParagraphBuilder':
        """
        Set the line spacing for the paragraph.
        Equivalent to withLineSpacing() in Java ParagraphBuilder.

        Args:
            spacing: Line spacing value (typically 1.0 to 2.0)

        Returns:
            Self for method chaining

        Raises:
            ValidationException: If spacing is not positive
        """
        if spacing <= 0:
            raise ValidationException(f"Line spacing must be positive, got {spacing}")

        self._line_spacing = spacing
        return self

    def color(self, color: Color) -> 'ParagraphBuilder':
        """
        Set the text color for the paragraph.
        Equivalent to withColor() in Java ParagraphBuilder.

        Args:
            color: The Color object for the text

        Returns:
            Self for method chaining

        Raises:
            ValidationException: If color is None
        """
        if color is None:
            raise ValidationException("Color cannot be null")

        self._text_color = color
        return self

    def at(self, page_index: int, x: float, y: float) -> 'ParagraphBuilder':
        """
        Set the position for the paragraph.
        Equivalent to withPosition() in Java ParagraphBuilder.

        Args:
            position: The Position object for the paragraph

        Returns:
            Self for method chaining

        Raises:
            ValidationException: If position is None
        """
        position = Position.at_page_coordinates(page_index, x, y)
        if position is None:
            raise ValidationException("Position cannot be null")

        self._paragraph.set_position(position)
        return self

    def build(self) -> Paragraph:
        """
        Build and return the final Paragraph object.
        Equivalent to build() in Java ParagraphBuilder.

        This method validates all required fields and constructs the final paragraph
        with text processing similar to ParagraphUtil.finalizeText() in Java.

        Returns:
            The constructed Paragraph object

        Raises:
            ValidationException: If required fields are missing or invalid
        """
        # Validate required fields
        if self._text is None:
            raise ValidationException("Text must be set before building paragraph")
        if self._font is None:
            raise ValidationException("Font must be set before building paragraph")
        if self._paragraph.get_position() is None:
            raise ValidationException("Position must be set before building paragraph")

        # Set paragraph properties
        self._paragraph.font = self._font
        self._paragraph.color = self._text_color
        self._paragraph.line_spacing = self._line_spacing

        # Process text into lines (simplified version of ParagraphUtil.finalizeText)
        # In the full implementation, this would handle text wrapping, line breaks, etc.
        self._paragraph.text_lines = self._process_text_lines(self._text)

        return self._paragraph

    def _register_ttf(self, ttf_file: Path, font_size: float) -> Font:
        """
        Register a TTF font with the client and return a Font object.
        Equivalent to registerTTF() private method in Java ParagraphBuilder.

        Args:
            ttf_file: Path to the TTF font file
            font_size: Size of the font

        Returns:
            Font object with the registered font name and size
        """
        try:
            font_name = self._client.register_font(ttf_file)
            return Font(font_name, font_size)
        except Exception as e:
            raise ValidationException(f"Failed to register font file {ttf_file}: {e}")

    def _process_text_lines(self, text: str) -> list[str]:
        """
        Process text into lines for the paragraph.
        This is a simplified version - the full implementation would handle
        word wrapping, line breaks, and other text formatting based on the font
        and paragraph width.

        Args:
            text: The input text to process

        Returns:
            List of text lines for the paragraph
        """
        # Handle escaped newlines (\\n) as actual newlines
        processed_text = text.replace('\\n', '\n')

        # Simple implementation - split on newlines
        # In the full version, this would implement proper text layout
        lines = processed_text.split('\n')

        # Remove empty lines at the end but preserve intentional line breaks
        while lines and not lines[-1].strip():
            lines.pop()

        # Ensure at least one line
        if not lines:
            lines = ['']

        return lines

    def add(self):
        self._client._add_paragraph(self.build())


class ParagraphPageBuilder(ParagraphBuilder):

    def __init__(self, client: 'PDFDancer', page_index: int):
        super().__init__(client)
        self._page_index: Optional[int] = page_index

    # noinspection PyMethodOverriding
    def at(self, x: float, y: float) -> 'ParagraphBuilder':
        return super().at(self._page_index, x, y)
