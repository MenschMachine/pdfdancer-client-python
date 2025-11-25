"""
TextLineBuilder for the PDFDancer Python client.
Mirrors the behaviour of ParagraphBuilder for single line text objects.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from . import StandardFonts
from .exceptions import ValidationException
from .models import (
    Color,
    Font,
    ObjectRef,
    Position,
    TextLine,
    TextObjectRef,
)

if TYPE_CHECKING:
    from .pdfdancer_v1 import PDFDancer

DEFAULT_TEXT_COLOR = Color(0, 0, 0)
_DEFAULT_BASE_FONT_SIZE = 12.0


class TextLineBuilder:
    """
    Fluent builder used to assemble `TextLine` instances.
    Behaviour is aligned with ParagraphBuilder but simplified for single-line text.
    """

    def __init__(self, client: "PDFDancer"):
        if client is None:
            raise ValidationException("Client cannot be null")

        self._client = client
        self._text_line = TextLine()
        self._text_color: Optional[Color] = None
        self._text: Optional[str] = None
        self._ttf_file: Optional[Path] = None
        self._font: Optional[Font] = None
        self._font_explicitly_changed = False
        self._original_text_line_position: Optional[Position] = None
        self._target_object_ref: Optional[ObjectRef] = None
        self._original_font: Optional[Font] = None
        self._original_color: Optional[Color] = None
        self._position_changed = False

    def only_text_changed(self) -> bool:
        """Return True when only the text payload has been modified."""
        return (
            self._text is not None
            and self._text_color is None
            and self._ttf_file is None
            and (self._font is None or not self._font_explicitly_changed)
        )

    def text(self, text: str, color: Optional[Color] = None) -> "TextLineBuilder":
        if text is None:
            raise ValidationException("Text cannot be null")
        self._text = text
        if color is not None:
            self.color(color)
        return self

    def font(
        self, font: Union[Font, str, StandardFonts], font_size: Optional[float] = None
    ) -> "TextLineBuilder":
        """
        Configure the font either by providing a `Font` instance or name + size.
        """
        if isinstance(font, Font):
            resolved_font = font
        else:
            if isinstance(font, StandardFonts):
                font = font.value
            if font is None:
                raise ValidationException("Font name cannot be null")
            if font_size is None:
                raise ValidationException(
                    "Font size must be provided when setting font by name"
                )
            resolved_font = Font(str(font), font_size)

        self._font = resolved_font
        self._ttf_file = None
        self._font_explicitly_changed = True
        return self

    def font_file(
        self, ttf_file: Union[Path, str], font_size: float
    ) -> "TextLineBuilder":
        if ttf_file is None:
            raise ValidationException("TTF file cannot be null")
        if font_size <= 0:
            raise ValidationException(f"Font size must be positive, got {font_size}")

        ttf_path = Path(ttf_file)

        if not ttf_path.exists():
            raise ValidationException(f"TTF file does not exist: {ttf_path}")
        if not ttf_path.is_file():
            raise ValidationException(f"TTF file is not a file: {ttf_path}")
        if ttf_path.stat().st_size <= 0:
            raise ValidationException(f"TTF file is empty: {ttf_path}")

        try:
            with open(ttf_path, "rb") as handle:
                handle.read(1)
        except (IOError, OSError) as exc:
            raise ValidationException(f"TTF file is not readable: {ttf_path}") from exc

        self._ttf_file = ttf_path
        self._font = self._register_ttf(ttf_path, font_size)
        self._font_explicitly_changed = True
        return self

    def set_font_explicitly_changed(self, changed: bool) -> None:
        self._font_explicitly_changed = bool(changed)

    def set_original_text_line_position(self, position: Position) -> None:
        self._original_text_line_position = position
        if position and self._text_line.position is None:
            self._text_line.position = deepcopy(position)

    def target(self, object_ref: ObjectRef) -> "TextLineBuilder":
        if object_ref is None:
            raise ValidationException("Object reference cannot be null")
        self._target_object_ref = object_ref
        return self

    def color(self, color: Color) -> "TextLineBuilder":
        if color is None:
            raise ValidationException("Color cannot be null")
        self._text_color = color
        return self

    def move_to(self, x: float, y: float) -> "TextLineBuilder":
        """
        Move the text line to new coordinates on the same page.
        """
        position = self._text_line.position
        if (
            position is None
            and self._target_object_ref
            and self._target_object_ref.position
        ):
            position = deepcopy(self._target_object_ref.position)
            self._text_line.position = position

        if position is None:
            raise ValidationException(
                "Cannot move text line without an existing position"
            )

        page_number = position.page_number
        if page_number is None:
            raise ValidationException(
                "Text line position must include a page number to move"
            )

        self._position_changed = True
        return self.at(page_number, x, y)

    def at_position(self, position: Position) -> "TextLineBuilder":
        if position is None:
            raise ValidationException("Position cannot be null")
        # Defensive copy so builder mutations do not alter original references
        self._text_line.position = deepcopy(position)
        self._position_changed = True
        return self

    def at(self, page_number: int, x: float, y: float) -> "TextLineBuilder":
        return self.at_position(Position.at_page_coordinates(page_number, x, y))

    def get_text(self) -> Optional[str]:
        return self._text

    def add(self) -> bool:
        """
        Add a new text line to the document.
        Note: Text lines are typically part of paragraphs. This method is not
        currently supported for standalone text lines.
        """
        raise NotImplementedError(
            "Adding standalone text lines is not supported. "
            "Text lines should be added as part of paragraphs."
        )

    def modify(self, object_ref: Optional[ObjectRef] = None):
        target_ref = object_ref or self._target_object_ref
        if target_ref is None:
            raise ValidationException(
                "Object reference must be provided to modify a text line"
            )

        if self.only_text_changed():
            # Backend accepts plain text updates for simple edits
            return self._client._modify_text_line(target_ref, self._text or "")

        text_line = self._finalize_text_line()
        # Use /pdf/modify endpoint for complex modifications
        return self._client._modify_text_line_full(target_ref, text_line)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _finalize_text_line(self) -> TextLine:
        if self._text_line.position is None:
            raise ValidationException("Position must be set before building text line")

        if (
            self._target_object_ref is None
            and self._font is None
            and self._text_line.font is None
        ):
            raise ValidationException("Font must be set before building text line")

        if self._text is not None:
            self._text_line.text = self._text
        elif not self._text_line.text:
            raise ValidationException("Text must be provided for text line")

        final_font = self._font if self._font is not None else self._original_font
        if final_font is None:
            final_font = Font(StandardFonts.HELVETICA.value, _DEFAULT_BASE_FONT_SIZE)
        self._text_line.font = final_font

        if self._text_color is not None:
            final_color = self._text_color
        elif self._text is not None:
            final_color = self._original_color or DEFAULT_TEXT_COLOR
        else:
            final_color = self._original_color

        # Ensure color is never None
        if final_color is None:
            final_color = DEFAULT_TEXT_COLOR
        self._text_line.color = final_color

        return self._text_line

    def _register_ttf(self, ttf_file: Path, font_size: float) -> Font:
        try:
            font_name = self._client.register_font(ttf_file)
            return Font(font_name, font_size)
        except Exception as exc:
            raise ValidationException(
                f"Failed to register font file {ttf_file}: {exc}"
            ) from exc

    @classmethod
    def from_object_ref(
        cls, client: "PDFDancer", object_ref: TextObjectRef
    ) -> "TextLineBuilder":
        if object_ref is None:
            raise ValidationException("Object reference cannot be null")

        builder = cls(client)
        builder.target(object_ref)

        if object_ref.position:
            builder.at_position(object_ref.position)
            builder.set_original_text_line_position(object_ref.position)

        if object_ref.font_name and object_ref.font_size:
            builder._original_font = Font(object_ref.font_name, object_ref.font_size)

        if object_ref.color:
            builder._original_color = object_ref.color

        if object_ref.text:
            builder._text_line.text = object_ref.text

        return builder


class TextLinePageBuilder(TextLineBuilder):
    def __init__(self, client: "PDFDancer", page_number: int):
        super().__init__(client)
        self._page_number: Optional[int] = page_number

    # noinspection PyMethodOverriding
    def at(self, x: float, y: float) -> "TextLineBuilder":
        return super().at(self._page_number, x, y)
