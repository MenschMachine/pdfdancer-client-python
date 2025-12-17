from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from . import FormFieldRef, ObjectRef, ObjectType, Point, Position, TextObjectRef
from .exceptions import ValidationException

if TYPE_CHECKING:
    from .models import CommandResult, Image, ImageFlipDirection
    from .pdfdancer_v1 import PDFDancer


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

    def __init__(
        self,
        client: "PDFDancer",
        internal_id: str,
        object_type: ObjectType,
        position: Position,
    ):
        self._client = client
        self.position = position
        self.internal_id = internal_id
        self.object_type = object_type

    @property
    def page_number(self) -> int:
        """Page index where this object resides."""
        return self.position.page_number

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
            Position.at_page_coordinates(self.position.page_number, x, y),
        )

    def redact(self, replacement: str = "[REDACTED]") -> bool:
        """Redact this object from the PDF document."""
        from .models import RedactTarget

        target = RedactTarget(self.internal_id, replacement)
        result = self._client._redact([target], replacement)
        return result.success


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
        return (
            self.internal_id == other.internal_id
            and self.object_type == other.object_type
            and self.position == other.position
        )


class ImageObject(PDFObjectBase):
    """Represents an image object inside a PDF page."""

    def scale(self, factor: float) -> "CommandResult":
        """Scale this image by a factor.

        Args:
            factor: Scale factor (e.g., 0.5 for half size, 2.0 for double size)

        Returns:
            CommandResult indicating success or failure
        """
        from .models import ImageTransformRequest, ImageTransformType

        request = ImageTransformRequest(
            object_ref=self.object_ref(),
            transform_type=ImageTransformType.SCALE,
            scale_factor=factor,
        )
        return self._client._transform_image(request)

    def scale_to(
        self, width: float, height: float, preserve_aspect_ratio: bool = True
    ) -> "CommandResult":
        """Scale this image to a target size.

        Args:
            width: Target width
            height: Target height
            preserve_aspect_ratio: If True, maintain proportions (default True)

        Returns:
            CommandResult indicating success or failure
        """
        from .models import ImageTransformRequest, ImageTransformType, Size

        request = ImageTransformRequest(
            object_ref=self.object_ref(),
            transform_type=ImageTransformType.SCALE,
            target_size=Size(width, height),
            preserve_aspect_ratio=preserve_aspect_ratio,
        )
        return self._client._transform_image(request)

    def rotate(self, angle: float) -> "CommandResult":
        """Rotate this image by a specified angle.

        Args:
            angle: Rotation angle in degrees (positive = counter-clockwise)

        Returns:
            CommandResult indicating success or failure
        """
        from .models import ImageTransformRequest, ImageTransformType

        request = ImageTransformRequest(
            object_ref=self.object_ref(),
            transform_type=ImageTransformType.ROTATE,
            rotation_angle=angle,
        )
        return self._client._transform_image(request)

    def crop(
        self, left: int = 0, top: int = 0, right: int = 0, bottom: int = 0
    ) -> "CommandResult":
        """Crop this image by removing pixels from edges.

        Args:
            left: Pixels to crop from left edge
            top: Pixels to crop from top edge
            right: Pixels to crop from right edge
            bottom: Pixels to crop from bottom edge

        Returns:
            CommandResult indicating success or failure
        """
        from .models import ImageTransformRequest, ImageTransformType

        request = ImageTransformRequest(
            object_ref=self.object_ref(),
            transform_type=ImageTransformType.CROP,
            crop_left=left,
            crop_top=top,
            crop_right=right,
            crop_bottom=bottom,
        )
        return self._client._transform_image(request)

    def set_opacity(self, opacity: float) -> "CommandResult":
        """Set the opacity of this image.

        Args:
            opacity: Opacity value from 0.0 (fully transparent) to 1.0 (fully opaque)

        Returns:
            CommandResult indicating success or failure
        """
        from .models import ImageTransformRequest, ImageTransformType

        if not 0.0 <= opacity <= 1.0:
            raise ValidationException(
                f"Opacity must be between 0.0 and 1.0, got {opacity}"
            )

        request = ImageTransformRequest(
            object_ref=self.object_ref(),
            transform_type=ImageTransformType.OPACITY,
            opacity=opacity,
        )
        return self._client._transform_image(request)

    def flip(self, direction: "ImageFlipDirection") -> "CommandResult":
        """Flip this image in the specified direction.

        Args:
            direction: Flip direction (HORIZONTAL, VERTICAL, or BOTH)

        Returns:
            CommandResult indicating success or failure
        """
        from .models import ImageTransformRequest, ImageTransformType

        request = ImageTransformRequest(
            object_ref=self.object_ref(),
            transform_type=ImageTransformType.FLIP,
            flip_direction=direction,
        )
        return self._client._transform_image(request)

    def replace(self, new_image: "Image") -> "CommandResult":
        """Replace this image with a new image.

        Args:
            new_image: The new Image object to replace this one with

        Returns:
            CommandResult indicating success or failure
        """
        from .models import ImageTransformRequest, ImageTransformType

        request = ImageTransformRequest(
            object_ref=self.object_ref(),
            transform_type=ImageTransformType.REPLACE,
            new_image=new_image,
        )
        return self._client._transform_image(request)

    def __eq__(self, other):
        if not isinstance(other, ImageObject):
            return False
        return (
            self.internal_id == other.internal_id
            and self.object_type == other.object_type
            and self.position == other.position
        )


class FormObject(PDFObjectBase):
    def __eq__(self, other):
        if not isinstance(other, FormObject):
            return False
        return (
            self.internal_id == other.internal_id
            and self.object_type == other.object_type
            and self.position == other.position
        )


class BaseTextEdit:
    """Common base for text-like editable objects (Paragraph, TextLine, etc.)"""

    def __init__(self, target_obj, object_ref):
        self._color = None
        self._position = None
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

    def move_to(self, x: float, y: float):
        self._position = Position().at_coordinates(Point(x, y))
        return self

    # --- Abstract method: implemented by subclass ---
    def apply(self):
        raise NotImplementedError("Subclasses must implement apply()")


class TextLineEdit(BaseTextEdit):
    def apply(self) -> bool:
        # If only text changed (no font, color, or position), use simple text modification
        only_text_changed = (
            self._new_text is not None
            and self._font_name is None
            and self._font_size is None
            and self._color is None
            and self._position is None
        )

        if only_text_changed:
            # noinspection PyProtectedMember
            result = self._target_obj._client._modify_text_line(
                self._object_ref, self._new_text
            )
            if result.warning:
                print(f"WARNING: {result.warning}", file=sys.stderr)
            return result

        # If only position changed (move operation)
        only_move = (
            self._position is not None
            and self._new_text is None
            and self._font_name is None
            and self._font_size is None
            and self._color is None
        )

        if only_move:
            page_number = (
                self._object_ref.position.page_number
                if self._object_ref.position
                else None
            )
            if page_number is None:
                raise ValidationException(
                    "Text line position must include a page number to move"
                )

            # Extract x, y from self._position
            x = self._position.x()
            y = self._position.y()
            if x is None or y is None:
                raise ValidationException("Position must have x and y coordinates")

            position = Position.at_page_coordinates(page_number, x, y)
            # noinspection PyProtectedMember
            result = self._target_obj._client._move(self._object_ref, position)
            return result

        # For font/color changes or combined operations, use TextLineBuilder
        # This ensures proper handling of font/color fallbacks just like ParagraphEditSession
        from .text_line_builder import TextLineBuilder

        builder = TextLineBuilder.from_object_ref(
            self._target_obj._client, self._object_ref
        )

        # Apply modifications to builder
        # IMPORTANT: Always explicitly set text to ensure it's preserved
        if self._new_text is not None:
            builder.text(self._new_text)
        elif hasattr(self._object_ref, "text") and self._object_ref.text:
            # Preserve original text when only changing font/color/position
            builder.text(self._object_ref.text)

        # IMPORTANT: Always explicitly set font to ensure it's preserved
        if self._font_name is not None and self._font_size is not None:
            builder.font(self._font_name, self._font_size)
        elif hasattr(self._object_ref, "font_name") and hasattr(
            self._object_ref, "font_size"
        ):
            if self._object_ref.font_name and self._object_ref.font_size:
                # Preserve original font when only changing color/position
                builder.font(self._object_ref.font_name, self._object_ref.font_size)

        if self._color is not None:
            builder.color(self._color)
        if self._position is not None:
            x = self._position.x()
            y = self._position.y()
            if x is None or y is None:
                raise ValidationException("Position must have x and y coordinates")
            page_number = (
                self._object_ref.position.page_number
                if self._object_ref.position
                else None
            )
            if page_number is None:
                raise ValidationException(
                    "Text line position must include a page number"
                )
            builder.at(page_number, x, y)

        # Use builder's modify method which handles all the complexity
        result = builder.modify(self._object_ref)
        if result.warning:
            print(f"WARNING: {result.warning}", file=sys.stderr)
        return result


class ParagraphObject(PDFObjectBase):
    """Represents a paragraph text block inside a PDF page."""

    def __init__(self, client: "PDFDancer", object_ref: TextObjectRef):
        super().__init__(
            client, object_ref.internal_id, object_ref.type, object_ref.position
        )
        self._object_ref = object_ref

    def __getattr__(self, name):
        """
        Automatically delegate attribute/method lookup to _object_ref
        if it's not found on this object.
        """
        return getattr(self._object_ref, name)

    def edit(self):
        return ParagraphEditSession(self._client, self.object_ref())

    def object_ref(self) -> TextObjectRef:
        return self._object_ref

    def __eq__(self, other):
        if not isinstance(other, ParagraphObject):
            return False
        return (
            self.internal_id == other.internal_id
            and self.object_type == other.object_type
            and self.position == other.position
            and self._object_ref.text == other._object_ref.text
            and self._object_ref.font_name == other._object_ref.font_name
            and self._object_ref.font_size == other._object_ref.font_size
            and self._object_ref.line_spacings == other._object_ref.line_spacings
            and self._object_ref.color == other._object_ref.color
            and self._object_ref.children == other._object_ref.children
        )


class TextLineObject(PDFObjectBase):
    """Represents a single line of text inside a PDF page."""

    def __init__(self, client: "PDFDancer", object_ref: TextObjectRef):
        super().__init__(
            client, object_ref.internal_id, object_ref.type, object_ref.position
        )
        self._object_ref = object_ref

    def __getattr__(self, name):
        """
        Automatically delegate attribute/method lookup to _object_ref
        if it's not found on this object.
        """
        return getattr(self._object_ref, name)

    def edit(self) -> TextLineEdit:
        return TextLineEdit(self, self.object_ref())

    def object_ref(self) -> TextObjectRef:
        return self._object_ref

    def __eq__(self, other):
        if not isinstance(other, TextLineObject):
            return False
        return (
            self.internal_id == other.internal_id
            and self.object_type == other.object_type
            and self.position == other.position
            and self._object_ref.text == other._object_ref.text
            and self._object_ref.font_name == other._object_ref.font_name
            and self._object_ref.font_size == other._object_ref.font_size
            and self._object_ref.line_spacings == other._object_ref.line_spacings
            and self._object_ref.color == other._object_ref.color
            and self._object_ref.children == other._object_ref.children
        )


class ParagraphEditSession:
    """
    Fluent editing helper that reuses ParagraphBuilder for modifications while preserving
    the legacy context-manager workflow (replace/font/color/etc.).
    """

    def __init__(self, client: "PDFDancer", object_ref: TextObjectRef):
        self._client = client
        self._object_ref = object_ref
        self._new_text = None
        self._font_name = None
        self._font_size = None
        self._color = None
        self._line_spacing = None
        self._new_position = None
        self._has_changes = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return False
        self.apply()
        return False

    def replace(self, text: str):
        self._new_text = text
        self._has_changes = True
        return self

    def font(self, font_name, font_size: float):
        self._font_name = font_name
        self._font_size = font_size
        self._has_changes = True
        return self

    def color(self, color):
        self._color = color
        self._has_changes = True
        return self

    def line_spacing(self, spacing: float):
        self._line_spacing = spacing
        self._has_changes = True
        return self

    def move_to(self, x: float, y: float):
        self._new_position = (x, y)
        self._has_changes = True
        return self

    def apply(self):
        if not self._has_changes:
            return self._client._modify_paragraph(self._object_ref, None)

        only_text_changed = (
            self._new_text is not None
            and self._font_name is None
            and self._font_size is None
            and self._color is None
            and self._line_spacing is None
            and self._new_position is None
        )

        if only_text_changed:
            result = self._client._modify_paragraph(self._object_ref, self._new_text)
            self._has_changes = False
            return result

        only_move = (
            self._new_position is not None
            and self._new_text is None
            and self._font_name is None
            and self._font_size is None
            and self._color is None
            and self._line_spacing is None
        )

        if only_move:
            page_number = (
                self._object_ref.position.page_number
                if self._object_ref.position
                else None
            )
            if page_number is None:
                raise ValidationException(
                    "Paragraph position must include a page number to move"
                )
            position = Position.at_page_coordinates(page_number, *self._new_position)
            result = self._client._move(self._object_ref, position)
            self._has_changes = False
            return result

        from .paragraph_builder import ParagraphBuilder

        builder = ParagraphBuilder.from_object_ref(self._client, self._object_ref)

        if self._new_text is not None:
            builder.text(self._new_text)
        if self._font_name is not None and self._font_size is not None:
            builder.font(self._font_name, self._font_size)
        if self._color is not None:
            builder.color(self._color)
        if self._line_spacing is not None:
            builder.line_spacing(self._line_spacing)
        if self._new_position is not None:
            builder.move_to(*self._new_position)

        result = builder.modify(self._object_ref)
        self._has_changes = False
        return result


class FormFieldEdit:
    def __init__(self, form_field: "FormFieldObject", object_ref: FormFieldRef):
        self.form_field = form_field
        self.object_ref = object_ref

    def value(self, new_value: str) -> "FormFieldEdit":
        self.form_field.value = new_value
        return self

    def apply(self) -> bool:
        # noinspection PyProtectedMember
        return self.form_field._client._change_form_field(
            self.object_ref, self.form_field.value
        )


class FormFieldObject(PDFObjectBase):
    def __init__(
        self,
        client: "PDFDancer",
        internal_id: str,
        object_type: ObjectType,
        position: Position,
        field_name: str,
        field_value: str,
    ):
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
        return (
            self.internal_id == other.internal_id
            and self.object_type == other.object_type
            and self.position == other.position
            and self.name == other.name
            and self.value == other.value
        )
