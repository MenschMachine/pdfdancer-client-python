"""
ParagraphBuilder for the PDFDancer Python client.
Mirrors the behaviour of the Java implementation while keeping Python conventions.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Union

from . import StandardFonts
from .exceptions import ValidationException
from .models import (
    Color,
    Font,
    ObjectRef,
    Paragraph,
    Point,
    Position,
    TextLine,
    TextObjectRef,
)

if TYPE_CHECKING:
    from .pdfdancer_v1 import PDFDancer

DEFAULT_LINE_SPACING_FACTOR = 1.2
DEFAULT_TEXT_COLOR = Color(0, 0, 0)
_DEFAULT_BASE_FONT_SIZE = 12.0


class ParagraphBuilder:
    """
    Fluent builder used to assemble `Paragraph` instances.
    Behaviour is aligned with the Java `ParagraphBuilder` so that mixed client/server
    scenarios stay predictable.
    """

    def __init__(self, client: "PDFDancer"):
        if client is None:
            raise ValidationException("Client cannot be null")

        self._client = client
        self._paragraph = Paragraph()
        self._line_spacing_factor: Optional[float] = None
        self._text_color: Optional[Color] = None
        self._text: Optional[str] = None
        self._ttf_file: Optional[Path] = None
        self._font: Optional[Font] = None
        self._font_explicitly_changed = False
        self._original_paragraph_position: Optional[Position] = None
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
            and self._line_spacing_factor is None
        )

    def text(self, text: str, color: Optional[Color] = None) -> "ParagraphBuilder":
        if text is None:
            raise ValidationException("Text cannot be null")
        self._text = text
        if color is not None:
            self.color(color)
        return self

    def font(
        self, font: Union[Font, str, StandardFonts], font_size: Optional[float] = None
    ) -> "ParagraphBuilder":
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
    ) -> "ParagraphBuilder":
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

    def set_original_paragraph_position(self, position: Position) -> None:
        self._original_paragraph_position = position
        if position and self._paragraph.get_position() is None:
            self._paragraph.set_position(deepcopy(position))

    def target(self, object_ref: ObjectRef) -> "ParagraphBuilder":
        if object_ref is None:
            raise ValidationException("Object reference cannot be null")
        self._target_object_ref = object_ref
        return self

    def line_spacing(self, spacing: float) -> "ParagraphBuilder":
        if spacing <= 0:
            raise ValidationException(f"Line spacing must be positive, got {spacing}")
        self._line_spacing_factor = spacing
        return self

    def color(self, color: Color) -> "ParagraphBuilder":
        if color is None:
            raise ValidationException("Color cannot be null")
        self._text_color = color
        return self

    def move_to(self, x: float, y: float) -> "ParagraphBuilder":
        """
        Move the paragraph anchor to new coordinates on the same page.
        """
        position = self._paragraph.get_position()
        if (
            position is None
            and self._target_object_ref
            and self._target_object_ref.position
        ):
            position = deepcopy(self._target_object_ref.position)
            self._paragraph.set_position(position)

        if position is None:
            raise ValidationException(
                "Cannot move paragraph without an existing position"
            )

        page_number = position.page_number
        if page_number is None:
            raise ValidationException(
                "Paragraph position must include a page number to move"
            )

        self._position_changed = True
        return self.at(page_number, x, y)

    def at_position(self, position: Position) -> "ParagraphBuilder":
        if position is None:
            raise ValidationException("Position cannot be null")
        # Defensive copy so builder mutations do not alter original references
        self._paragraph.set_position(deepcopy(position))
        self._position_changed = True
        return self

    def at(self, page_number: int, x: float, y: float) -> "ParagraphBuilder":
        return self.at_position(Position.at_page_coordinates(page_number, x, y))

    def add_text_line(
        self, text_line: Union[TextLine, TextObjectRef, str]
    ) -> "ParagraphBuilder":
        self._paragraph.add_line(self._coerce_text_line(text_line))
        return self

    def get_text(self) -> Optional[str]:
        return self._text

    def add(self) -> bool:
        # noinspection PyProtectedMember
        return self._client._add_paragraph(self._finalize_paragraph())

    def modify(self, object_ref: Optional[ObjectRef] = None):
        target_ref = object_ref or self._target_object_ref
        if target_ref is None:
            raise ValidationException(
                "Object reference must be provided to modify a paragraph"
            )

        if self.only_text_changed():
            # Backend accepts plain text updates for simple edits
            return self._client._modify_paragraph(target_ref, self._text or "")

        paragraph = self._finalize_paragraph()
        return self._client._modify_paragraph(target_ref, paragraph)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _finalize_paragraph(self) -> Paragraph:
        if self._paragraph.get_position() is None:
            raise ValidationException("Position must be set before building paragraph")

        if (
            self._target_object_ref is None
            and self._font is None
            and self._paragraph.font is None
        ):
            raise ValidationException("Font must be set before building paragraph")

        if self._text is not None:
            self._finalize_lines_from_text()
        elif not self._paragraph.text_lines:
            raise ValidationException(
                "Either text must be provided or existing lines supplied"
            )
        else:
            self._finalize_existing_lines()

        self._reposition_lines()

        should_skip_lines = (
            self._position_changed
            and self._text is None
            and self._text_color is None
            and (self._font is None or not self._font_explicitly_changed)
            and self._line_spacing_factor is None
        )
        if should_skip_lines:
            self._paragraph.text_lines = None
            self._paragraph.set_line_spacings(None)

        final_font = self._font if self._font is not None else self._original_font
        if final_font is None:
            final_font = Font(StandardFonts.HELVETICA.value, _DEFAULT_BASE_FONT_SIZE)
        self._paragraph.font = final_font

        if self._text_color is not None:
            final_color = self._text_color
        elif self._text is not None:
            final_color = self._original_color or DEFAULT_TEXT_COLOR
        else:
            final_color = self._original_color
        self._paragraph.color = final_color
        return self._paragraph

    def _finalize_lines_from_text(self) -> None:
        base_font = self._font or self._original_font
        base_color = self._text_color or self._original_color or DEFAULT_TEXT_COLOR
        color = base_color

        if self._line_spacing_factor is not None:
            spacing = self._line_spacing_factor
        else:
            existing_spacings = self._paragraph.get_line_spacings()
            if existing_spacings:
                spacing = existing_spacings[0]
            elif self._paragraph.line_spacing:
                spacing = self._paragraph.line_spacing
            else:
                spacing = DEFAULT_LINE_SPACING_FACTOR

        self._paragraph.clear_lines()
        lines: List[TextLine] = []
        for index, line_text in enumerate(self._split_text(self._text or "")):
            line_position = self._calculate_line_position(index, spacing)
            lines.append(
                TextLine(
                    position=line_position,
                    font=base_font,
                    color=color,
                    line_spacing=spacing,
                    text=line_text,
                )
            )
        self._paragraph.set_lines(lines)
        self._paragraph.set_line_spacings(
            [spacing] * (len(lines) - 1) if len(lines) > 1 else None
        )
        self._paragraph.line_spacing = spacing

    def _finalize_existing_lines(self) -> None:
        lines = self._paragraph.text_lines or []
        spacing_override = self._line_spacing_factor
        spacing_for_calc = spacing_override

        if spacing_for_calc is None:
            existing_spacings = self._paragraph.get_line_spacings()
            if existing_spacings:
                spacing_for_calc = existing_spacings[0]
        if spacing_for_calc is None:
            spacing_for_calc = (
                self._paragraph.line_spacing or DEFAULT_LINE_SPACING_FACTOR
            )

        updated_lines: List[TextLine] = []
        for index, line in enumerate(lines):
            if isinstance(line, TextLine):
                if spacing_override is not None:
                    line.line_spacing = spacing_override
                if self._text_color is not None:
                    line.color = self._text_color
                if self._font is not None and self._font_explicitly_changed:
                    line.font = self._font
                updated_lines.append(line)
            else:
                line_position = self._calculate_line_position(index, spacing_for_calc)
                updated_lines.append(
                    TextLine(
                        position=line_position,
                        font=(
                            self._font
                            if self._font is not None
                            else self._original_font
                        ),
                        color=self._text_color
                        or self._original_color
                        or DEFAULT_TEXT_COLOR,
                        line_spacing=(
                            spacing_override
                            if spacing_override is not None
                            else spacing_for_calc
                        ),
                        text=str(line),
                    )
                )

        self._paragraph.set_lines(updated_lines)

        if spacing_override is not None:
            self._paragraph.set_line_spacings(
                [spacing_override] * (len(updated_lines) - 1)
                if len(updated_lines) > 1
                else None
            )
            self._paragraph.line_spacing = spacing_override

    def _reposition_lines(self) -> None:
        if self._text is not None:
            # Newly generated text lines already align with the updated paragraph position.
            return
        paragraph_pos = self._paragraph.get_position()
        lines = self._paragraph.text_lines or []
        if not paragraph_pos or not lines:
            return

        base_position = self._original_paragraph_position
        if base_position is None:
            for line in lines:
                if isinstance(line, TextLine) and line.position is not None:
                    base_position = line.position
                    break

        if base_position is None:
            return

        target_x = paragraph_pos.x()
        target_y = paragraph_pos.y()
        base_x = base_position.x()
        base_y = base_position.y()
        if None in (target_x, target_y, base_x, base_y):
            return

        dx = target_x - base_x
        dy = target_y - base_y
        if dx == 0 and dy == 0:
            return

        for line in lines:
            if isinstance(line, TextLine) and line.position is not None:
                current_x = line.position.x()
                current_y = line.position.y()
                if current_x is None or current_y is None:
                    continue
                line.position.at_coordinates(Point(current_x + dx, current_y + dy))

    def _coerce_text_line(
        self, source: Union[TextLine, TextObjectRef, str]
    ) -> TextLine:
        if isinstance(source, TextLine):
            return source

        if isinstance(source, TextObjectRef):
            font = None
            if source.font_name and source.font_size:
                font = Font(source.font_name, source.font_size)
            elif getattr(source, "children", None):
                for child in source.children:
                    if child.font_name and child.font_size:
                        font = Font(child.font_name, child.font_size)
                        break
            if font is None:
                font = self._original_font

            spacing = self._line_spacing_factor
            if spacing is None and source.line_spacings:
                spacing = source.line_spacings[0]
            if spacing is None:
                spacing = self._paragraph.line_spacing or DEFAULT_LINE_SPACING_FACTOR

            color = source.color or self._original_color

            line = TextLine(
                position=deepcopy(source.position) if source.position else None,
                font=font,
                color=color,
                line_spacing=spacing,
                text=source.text or "",
            )
            if self._original_font is None and font is not None:
                self._original_font = font
            if self._original_color is None and color is not None:
                self._original_color = color
            return line

        if isinstance(source, str):
            current_index = len(self._paragraph.get_lines())
            spacing = (
                self._line_spacing_factor
                if self._line_spacing_factor is not None
                else (self._paragraph.line_spacing or DEFAULT_LINE_SPACING_FACTOR)
            )
            line_position = self._calculate_line_position(current_index, spacing)
            return TextLine(
                position=line_position,
                font=self._font or self._original_font,
                color=self._text_color or self._original_color or DEFAULT_TEXT_COLOR,
                line_spacing=spacing,
                text=source,
            )

        raise ValidationException(f"Unsupported text line type: {type(source)}")

    def _split_text(self, text: str) -> List[str]:
        processed = text.replace("\r\n", "\n").replace("\r", "\n").replace("\\n", "\n")
        parts = processed.split("\n")
        while parts and parts[-1] == "":
            parts.pop()
        if not parts:
            parts = [""]
        return parts

    def _calculate_line_position(
        self, line_index: int, spacing_factor: float
    ) -> Optional[Position]:
        paragraph_position = self._paragraph.get_position()
        if paragraph_position is None:
            return None

        page_number = paragraph_position.page_number
        base_x = paragraph_position.x()
        base_y = paragraph_position.y()
        if page_number is None or base_x is None or base_y is None:
            return None

        offset = line_index * self._calculate_baseline_distance(spacing_factor)
        return Position.at_page_coordinates(page_number, base_x, base_y + offset)

    def _calculate_baseline_distance(self, spacing_factor: float) -> float:
        factor = spacing_factor if spacing_factor > 0 else DEFAULT_LINE_SPACING_FACTOR
        return self._baseline_font_size() * factor

    def _baseline_font_size(self) -> float:
        if self._font and self._font.size:
            return self._font.size
        if self._original_font and self._original_font.size:
            return self._original_font.size
        return _DEFAULT_BASE_FONT_SIZE

    def _register_ttf(self, ttf_file: Path, font_size: float) -> Font:
        try:
            font_name = self._client.register_font(ttf_file)
            return Font(font_name, font_size)
        except Exception as exc:
            raise ValidationException(
                f"Failed to register font file {ttf_file}: {exc}"
            ) from exc

    def _build(self) -> Paragraph:
        """
        Backwards-compatible alias for callers that invoked the previous `_build`.
        """
        return self._finalize_paragraph()

    @classmethod
    def from_object_ref(
        cls, client: "PDFDancer", object_ref: TextObjectRef
    ) -> "ParagraphBuilder":
        if object_ref is None:
            raise ValidationException("Object reference cannot be null")

        builder = cls(client)
        builder.target(object_ref)

        if object_ref.position:
            builder.at_position(object_ref.position)
            builder.set_original_paragraph_position(object_ref.position)

        if object_ref.line_spacings:
            builder._paragraph.set_line_spacings(object_ref.line_spacings)
            builder._paragraph.line_spacing = (
                object_ref.line_spacings[0]
                if object_ref.line_spacings
                else builder._paragraph.line_spacing
            )

        if object_ref.font_name and object_ref.font_size:
            builder._original_font = Font(object_ref.font_name, object_ref.font_size)

        if object_ref.color:
            builder._original_color = object_ref.color

        if object_ref.children:
            for child in object_ref.children:
                builder.add_text_line(child)
        elif object_ref.text:
            for segment in object_ref.text.split("\n"):
                builder.add_text_line(segment)

        return builder


class ParagraphPageBuilder(ParagraphBuilder):

    def __init__(self, client: "PDFDancer", page_number: int):
        super().__init__(client)
        self._page_number: Optional[int] = page_number

    # noinspection PyMethodOverriding
    def at(self, x: float, y: float) -> "ParagraphBuilder":
        return super().at(self._page_number, x, y)
