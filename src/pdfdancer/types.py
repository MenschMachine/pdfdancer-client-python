from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from . import (
    FormFieldRef,
    ObjectRef,
    ObjectType,
    PathObjectRef,
    Position,
)
from .exceptions import ValidationException

if TYPE_CHECKING:
    from .models import Color, CommandResult, Image, ImageFlipDirection
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
    Base class for selectable PDF object references (paths, text lines, etc.)
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

    def clear_clipping(self) -> bool:
        """Detach any active clipping path from this object."""
        return self._client.clear_clipping(self.object_ref())


# -------------------------------------------------------------------
# Subclasses
# -------------------------------------------------------------------


class PathObject(PDFObjectBase):
    """Represents a vector path object inside a PDF page."""

    def __init__(self, client: "PDFDancer", object_ref):
        """
        Initialize a PathObject.

        Args:
            client: PDFDancer client instance
            object_ref: ObjectRef or PathObjectRef with path data
        """
        super().__init__(
            client, object_ref.internal_id, object_ref.type, object_ref.position
        )
        self._object_ref = object_ref

    @property
    def bounding_box(self) -> Optional[BoundingRect]:
        """Optional bounding rectangle (if available)."""
        return self.position.bounding_rect

    def edit(self) -> PathEditSession:
        """Start a fluent editing session to modify path colors."""
        return PathEditSession(self._client, self.object_ref())

    def object_ref(self):
        """Return an ObjectRef for this path."""
        return self._object_ref

    def get_stroke_color(self) -> Optional["Color"]:
        """Get the stroke/outline color of the path, or None if not set."""
        if isinstance(self._object_ref, PathObjectRef):
            return self._object_ref.get_stroke_color()
        return None

    def get_fill_color(self) -> Optional["Color"]:
        """Get the fill color of the path, or None if not set."""
        if isinstance(self._object_ref, PathObjectRef):
            return self._object_ref.get_fill_color()
        return None

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

    @property
    def width(self) -> Optional[float]:
        return (
            self.position.bounding_rect.width if self.position.bounding_rect else None
        )

    @property
    def height(self) -> Optional[float]:
        return (
            self.position.bounding_rect.height if self.position.bounding_rect else None
        )

    @property
    def aspect_ratio(self) -> Optional[float]:
        return (
            self.width / self.height if self.width is not None and self.height else None
        )

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
            angle: Rotation angle in degrees (positive = clockwise)

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

    def flip_horizontal(self) -> "CommandResult":
        from .models import ImageFlipDirection

        return self.flip(ImageFlipDirection.HORIZONTAL)

    def flip_vertical(self) -> "CommandResult":
        from .models import ImageFlipDirection

        return self.flip(ImageFlipDirection.VERTICAL)

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

    def replace_from_file(self, image_path: Path) -> "CommandResult":
        from .models import Image

        path = Path(image_path)
        if not path.is_file():
            raise ValidationException(f"Image file not found: {path}")
        data = path.read_bytes()
        if not data:
            raise ValidationException("Image file cannot be empty")
        return self.replace(Image(format=path.suffix.lstrip(".").upper(), data=data))

    def fill_region(
        self, x: int, y: int, width: int, height: int, color: "Color"
    ) -> "CommandResult":
        """Fill a rectangular region within this image with a solid color.

        Args:
            x: X coordinate of the region (pixels from left edge of image)
            y: Y coordinate of the region (pixels from top edge of image)
            width: Width of the region in pixels
            height: Height of the region in pixels
            color: Fill color as a Color object (alpha channel is ignored)

        Returns:
            CommandResult indicating success or failure
        """
        from .models import Color, ImageTransformRequest, ImageTransformType

        if not isinstance(color, Color):
            raise ValidationException("color must be a Color object")
        if width <= 0:
            raise ValidationException(f"width must be positive, got {width}")
        if height <= 0:
            raise ValidationException(f"height must be positive, got {height}")

        # Convert Color to integer: 0xRRGGBB format (RGB only, no alpha)
        fill_color_int = (color.r << 16) | (color.g << 8) | color.b

        request = ImageTransformRequest(
            object_ref=self.object_ref(),
            transform_type=ImageTransformType.FILL_REGION,
            fill_region_x=x,
            fill_region_y=y,
            fill_region_width=width,
            fill_region_height=height,
            fill_color=fill_color_int,
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


class PathGroupObject:
    """Represents a group of vector paths that can be manipulated as a unit."""

    def __init__(self, client: "PDFDancer", page_index: int, info):
        self._client = client
        self._page_index = page_index
        self._info = info

    @property
    def group_id(self) -> str:
        return self._info.group_id

    @property
    def path_count(self) -> int:
        return self._info.path_count

    @property
    def bounding_box(self):
        return self._info.bounding_box

    @property
    def x(self) -> float:
        return self._info.x

    @property
    def y(self) -> float:
        return self._info.y

    def move_to(self, x: float, y: float) -> bool:
        return self._client._move_path_group(self._page_index, self.group_id, x, y)

    def scale(self, factor: float) -> bool:
        return self._client._scale_path_group(self._page_index, self.group_id, factor)

    def rotate(self, degrees: float) -> bool:
        return self._client._rotate_path_group(self._page_index, self.group_id, degrees)

    def resize(self, width: float, height: float) -> bool:
        return self._client._resize_path_group(
            self._page_index, self.group_id, width, height
        )

    def remove(self) -> bool:
        return self._client._remove_path_group(self._page_index, self.group_id)

    def clear_clipping(self) -> bool:
        return self._client.clear_path_group_clipping(
            self._page_index + 1, self.group_id
        )

    def __repr__(self):
        return f"PathGroupObject(group_id={self.group_id!r}, path_count={self.path_count}, page_index={self._page_index})"


class FormObject(PDFObjectBase):
    def __eq__(self, other):
        if not isinstance(other, FormObject):
            return False
        return (
            self.internal_id == other.internal_id
            and self.object_type == other.object_type
            and self.position == other.position
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

    def set_value(self, value: str) -> bool:
        result = self._client._change_form_field(self.object_ref(), value)
        if result:
            self.value = value
        return result

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


class PathEditSession:
    """
    Fluent editing helper for modifying path stroke and fill colors.
    """

    def __init__(self, client: "PDFDancer", object_ref):
        self._client = client
        self._object_ref = object_ref
        self._stroke_color = None
        self._fill_color = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return False
        self.apply()
        return False

    def stroke_color(self, color) -> "PathEditSession":
        """
        Set the stroke/outline color.

        Args:
            color: The stroke color (Color object)

        Returns:
            Self for method chaining
        """
        self._stroke_color = color
        return self

    def fill_color(self, color) -> "PathEditSession":
        """
        Set the fill color.

        Args:
            color: The fill color (Color object)

        Returns:
            Self for method chaining
        """
        self._fill_color = color
        return self

    def apply(self):
        """
        Apply the color modifications to the path.

        Returns:
            CommandResult indicating success or failure
        """
        return self._client._modify_path(
            self._object_ref, self._stroke_color, self._fill_color
        )
