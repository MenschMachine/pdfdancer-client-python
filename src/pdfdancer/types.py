from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import ObjectType, Position, ObjectRef, Point, Paragraph, Font, Color, FormFieldRef


@dataclass
class BoundingRect:
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None


class UnsupportedOperation(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class PDFObjectBase:
    """
    Base class for all PDF objects (paths, paragraphs, text lines, etc.)
    providing shared behavior such as position, deletion, and movement.
    """

    def __init__(self, client: 'PDFDancer', internal_id: str, object_type: ObjectType, position: Position):
        self._client = client
        self.position = position
        self.internal_id = internal_id
        self.object_type = object_type

    @property
    def page_index(self) -> int:
        """Page index where this object resides."""
        return self.position.page_index

    def object_ref(self) -> ObjectRef:
        return ObjectRef(self.internal_id, self.position, self.object_type)

    # --------------------------------------------------------------
    # Common actions
    # --------------------------------------------------------------
    def delete(self) -> bool:
        """Delete this object from the PDF document."""
        return self._client._delete(self.object_ref())

    def move_to(self, x: float, y: float) -> bool:
        """Move this object to a new position."""
        return self._client._move(
            self.object_ref(),
            Position.at_page_coordinates(self.position.page_index, x, y)
        )


# -------------------------------------------------------------------
# Subclasses
# -------------------------------------------------------------------

class PathObject(PDFObjectBase):
    """Represents a vector path object inside a PDF page."""

    @property
    def bounding_box(self) -> Optional[BoundingRect]:
        """Optional bounding rectangle (if available)."""
        return self.position.bounding_rect


class ImageObject(PDFObjectBase):
    pass


class FormObject(PDFObjectBase):
    pass


def _process_text_lines(text: str) -> list[str]:
    """
    Process text into lines for the paragraph.
    This is a simplified version - the full implementation would handle
    word wrapping, line breaks, and other text formatting based on the font
    and paragraph width. TODO

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


DEFAULT_LINE_SPACING = 1.2
DEFAULT_COLOR = Color(0, 0, 0)


class BaseTextEdit:
    """Common base for text-like editable objects (Paragraph, TextLine, etc.)"""

    def __init__(self, target_obj, object_ref):
        self._color = None
        self._position = None
        self._line_spacing = None
        self._font_size = None
        self._font_name = None
        self._new_text = None
        self._target_obj = target_obj
        self._object_ref = object_ref

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self.apply()

    # --- Common fluent configuration methods ---

    def replace(self, text: str):
        self._new_text = text
        return self

    def font(self, font_name: str, font_size: float):
        self._font_name = font_name
        self._font_size = font_size
        return self

    def color(self, color):
        self._color = color
        return self

    def line_spacing(self, line_spacing: float):
        self._line_spacing = line_spacing
        return self

    def move_to(self, x: float, y: float):
        self._position = Position().at_coordinates(Point(x, y))
        return self

    # --- Abstract method: implemented by subclass ---
    def apply(self):
        raise NotImplementedError("Subclasses must implement apply()")


class ParagraphEdit(BaseTextEdit):
    def apply(self) -> bool:
        if (
                self._position is None
                and self._line_spacing is None
                and self._font_size is None
                and self._font_name is None
                and self._color is None
        ):
            # noinspection PyProtectedMember
            return self._target_obj._client._modify_paragraph(self._object_ref, self._new_text)
        else:
            new_paragraph = Paragraph(
                position=self._position,
                line_spacing=self._line_spacing if self._line_spacing is not None else DEFAULT_LINE_SPACING,
                font=Font(name=self._font_name, size=self._font_size),
                text_lines=_process_text_lines(self._new_text),
                color=self._color if self._color is not None else DEFAULT_COLOR,
            )
            # noinspection PyProtectedMember
            return self._target_obj._client._modify_paragraph(self._object_ref, new_paragraph)


class TextLineEdit(BaseTextEdit):
    def apply(self) -> bool:
        if (
                self._position is None
                and self._line_spacing is None
                and self._font_size is None
                and self._font_name is None
                and self._color is None
        ):
            # noinspection PyProtectedMember
            return self._target_obj._client._modify_text_line(self._object_ref, self._new_text)
        else:
            raise UnsupportedOperation("TextLineEdit cannot be applied to text lines")


class ParagraphObject(PDFObjectBase):
    """Represents a paragraph text block inside a PDF page."""

    def edit(self) -> ParagraphEdit:
        return ParagraphEdit(self, self.object_ref())


class TextLineObject(PDFObjectBase):
    """Represents a single line of text inside a PDF page."""

    def edit(self) -> TextLineEdit:
        return TextLineEdit(self, self.object_ref())


class FormFieldEdit:
    def __init__(self, form_field: 'FormFieldObject', object_ref: FormFieldRef):
        self.form_field = form_field
        self.object_ref = object_ref

    def value(self, new_value: str) -> 'FormFieldEdit':
        self.form_field.value = new_value
        return self

    def apply(self) -> bool:
        # noinspection PyProtectedMember
        return self.form_field._client._change_form_field(self.object_ref, self.form_field.value)


class FormFieldObject(PDFObjectBase):
    def __init__(self, client: 'PDFDancer', internal_id: str, object_type: ObjectType, position: Position,
                 field_name: str, field_value: str):
        super().__init__(client, internal_id, object_type, position)
        self.name = field_name
        self.value = field_value

    def edit(self) -> FormFieldEdit:
        return FormFieldEdit(self, self.object_ref())

    def object_ref(self) -> FormFieldRef:
        ref = FormFieldRef(self.internal_id, self.position, self.object_type)
        ref.name = self.name
        ref.value = self.value
        return ref
