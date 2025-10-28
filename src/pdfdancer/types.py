from __future__ import annotations

import statistics
import sys
from dataclasses import dataclass
from typing import Optional, List

from . import ObjectType, Position, ObjectRef, Point, Paragraph, Font, Color, FormFieldRef, TextObjectRef
from .models import CommandResult


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

    def __eq__(self, other):
        if not isinstance(other, PathObject):
            return False
        return (self.internal_id == other.internal_id and
                self.object_type == other.object_type and
                self.position == other.position)


class ImageObject(PDFObjectBase):
    def __eq__(self, other):
        if not isinstance(other, ImageObject):
            return False
        return (self.internal_id == other.internal_id and
                self.object_type == other.object_type and
                self.position == other.position)


class FormObject(PDFObjectBase):
    def __eq__(self, other):
        if not isinstance(other, FormObject):
            return False
        return (self.internal_id == other.internal_id and
                self.object_type == other.object_type and
                self.position == other.position)


def _process_text_lines(text: str) -> List[str]:
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
    def apply(self) -> CommandResult:
        if (
                self._position is None
                and self._line_spacing is None
                and self._font_size is None
                and self._font_name is None
                and self._color is None
        ):
            # noinspection PyProtectedMember
            result = self._target_obj._client._modify_paragraph(self._object_ref, self._new_text)
            if result.warning:
                print(f"WARNING: {result.warning}", file=sys.stderr)
            return result
        else:
            new_paragraph = Paragraph(
                position=self._position if self._position is not None else self._object_ref.position,
                line_spacing=self._get_line_spacing(),
                font=self._get_font(),
                text_lines=self._get_text_lines(),
                color=self._get_color(),
            )
            # noinspection PyProtectedMember
            result = self._target_obj._client._modify_paragraph(self._object_ref, new_paragraph)
            if result.warning:
                print(f"WARNING: {result.warning}", file=sys.stderr)
            return result

    def _get_line_spacing(self) -> float:
        if self._line_spacing is not None:
            return self._line_spacing
        elif self._object_ref.line_spacings is not None:
            return statistics.mean(self._object_ref.line_spacings)
        else:
            return DEFAULT_LINE_SPACING

    def _get_font(self):
        if self._font_name is not None and self._font_size is not None:
            return Font(name=self._font_name, size=self._font_size)
        elif self._object_ref.font_name is not None and self._object_ref.font_size is not None:
            return Font(name=self._object_ref.font_name, size=self._object_ref.font_size)
        else:
            raise Exception("Font is none")

    def _get_text_lines(self):
        if self._new_text is not None:
            # this replaces the text of the entire paragraph with the new text, so this is fine
            return _process_text_lines(self._new_text)
        elif self._object_ref.text is not None:
            # no new text, so other properties changed, we need to keep the existing text lines
            return _process_text_lines(self._object_ref.text)
        else:
            raise Exception("Paragraph has no text")

    def _get_color(self):
        if self._color is not None:
            return self._color
        elif self._object_ref.color is not None:
            return self._object_ref.color
        else:
            return DEFAULT_COLOR


class TextLineEdit(BaseTextEdit):
    def apply(self) -> bool:
        if (
                self._line_spacing is None
                and self._font_size is None
                and self._font_name is None
                and self._color is None
        ):
            # noinspection PyProtectedMember
            result = self._target_obj._client._modify_text_line(self._object_ref, self._new_text)
            if result.warning:
                print(f"WARNING: {result.warning}", file=sys.stderr)
            return result
        else:
            # noinspection PyProtectedMember
            # return self._target_obj._client._modify_text_line(self._object_ref, new_textline)
            raise UnsupportedOperation("Full TextLineEdit not implemented - TODO")


class ParagraphObject(PDFObjectBase):
    """Represents a paragraph text block inside a PDF page."""

    def __init__(self, client: 'PDFDancer', object_ref: TextObjectRef):
        super().__init__(client, object_ref.internal_id, object_ref.type, object_ref.position)
        self._object_ref = object_ref

    def __getattr__(self, name):
        """
        Automatically delegate attribute/method lookup to _object_ref
        if it's not found on this object.
        """
        return getattr(self._object_ref, name)

    def edit(self) -> ParagraphEdit:
        return ParagraphEdit(self, self.object_ref())

    def object_ref(self) -> TextObjectRef:
        return self._object_ref

    def __eq__(self, other):
        if not isinstance(other, ParagraphObject):
            return False
        return (self.internal_id == other.internal_id and
                self.object_type == other.object_type and
                self.position == other.position and
                self._object_ref.text == other._object_ref.text and
                self._object_ref.font_name == other._object_ref.font_name and
                self._object_ref.font_size == other._object_ref.font_size and
                self._object_ref.line_spacings == other._object_ref.line_spacings and
                self._object_ref.color == other._object_ref.color and
                self._object_ref.children == other._object_ref.children)


class TextLineObject(PDFObjectBase):
    """Represents a single line of text inside a PDF page."""

    def __init__(self, client: 'PDFDancer', object_ref: TextObjectRef):
        super().__init__(client, object_ref.internal_id, object_ref.type, object_ref.position)
        self._object_ref = object_ref

    def edit(self) -> TextLineEdit:
        return TextLineEdit(self, self.object_ref())

    def object_ref(self) -> TextObjectRef:
        return self._object_ref

    def __eq__(self, other):
        if not isinstance(other, TextLineObject):
            return False
        return (self.internal_id == other.internal_id and
                self.object_type == other.object_type and
                self.position == other.position and
                self._object_ref.text == other._object_ref.text and
                self._object_ref.font_name == other._object_ref.font_name and
                self._object_ref.font_size == other._object_ref.font_size and
                self._object_ref.line_spacings == other._object_ref.line_spacings and
                self._object_ref.color == other._object_ref.color and
                self._object_ref.children == other._object_ref.children)


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

    def __eq__(self, other):
        if not isinstance(other, FormFieldObject):
            return False
        return (self.internal_id == other.internal_id and
                self.object_type == other.object_type and
                self.position == other.position and
                self.name == other.name and
                self.value == other.value)
