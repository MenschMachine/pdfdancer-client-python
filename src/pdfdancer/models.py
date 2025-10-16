"""
Model classes for the PDFDancer Python client.
Closely mirrors the Java model classes with Python conventions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Any


class StandardFonts(Enum):
    """
    The 14 standard PDF fonts that are guaranteed to be available in all PDF readers.
    These fonts do not need to be embedded in the PDF document.

    Serif fonts (Times family):
    - TIMES_ROMAN: Standard Times Roman font
    - TIMES_BOLD: Bold version of Times Roman
    - TIMES_ITALIC: Italic version of Times Roman
    - TIMES_BOLD_ITALIC: Bold and italic version of Times Roman

    Sans-serif fonts (Helvetica family):
    - HELVETICA: Standard Helvetica font
    - HELVETICA_BOLD: Bold version of Helvetica
    - HELVETICA_OBLIQUE: Oblique (italic) version of Helvetica
    - HELVETICA_BOLD_OBLIQUE: Bold and oblique version of Helvetica

    Monospace fonts (Courier family):
    - COURIER: Standard Courier font
    - COURIER_BOLD: Bold version of Courier
    - COURIER_OBLIQUE: Oblique (italic) version of Courier
    - COURIER_BOLD_OBLIQUE: Bold and oblique version of Courier

    Symbol and decorative fonts:
    - SYMBOL: Symbol font for mathematical and special characters
    - ZAPF_DINGBATS: Zapf Dingbats font for decorative symbols
    """
    TIMES_ROMAN = "Times-Roman"
    TIMES_BOLD = "Times-Bold"
    TIMES_ITALIC = "Times-Italic"
    TIMES_BOLD_ITALIC = "Times-BoldItalic"
    HELVETICA = "Helvetica"
    HELVETICA_BOLD = "Helvetica-Bold"
    HELVETICA_OBLIQUE = "Helvetica-Oblique"
    HELVETICA_BOLD_OBLIQUE = "Helvetica-BoldOblique"
    COURIER = "Courier"
    COURIER_BOLD = "Courier-Bold"
    COURIER_OBLIQUE = "Courier-Oblique"
    COURIER_BOLD_OBLIQUE = "Courier-BoldOblique"
    SYMBOL = "Symbol"
    ZAPF_DINGBATS = "ZapfDingbats"


class ObjectType(Enum):
    """Object type enumeration matching the Java ObjectType."""
    FORM_FIELD = "FORM_FIELD"
    IMAGE = "IMAGE"
    FORM_X_OBJECT = "FORM_X_OBJECT"
    PATH = "PATH"
    PARAGRAPH = "PARAGRAPH"
    TEXT_LINE = "TEXT_LINE"
    PAGE = "PAGE"
    TEXT_FIELD = "TEXT_FIELD"
    CHECK_BOX = "CHECK_BOX"
    RADIO_BUTTON = "RADIO_BUTTON"


class PositionMode(Enum):
    """Defines how position matching should be performed when searching for objects."""
    INTERSECT = "INTERSECT"  # Objects that intersect with the specified position area
    CONTAINS = "CONTAINS"  # Objects completely contained within the specified position area


class ShapeType(Enum):
    """Defines the geometric shape type used for position specification."""
    POINT = "POINT"  # Single point coordinate
    LINE = "LINE"  # Linear shape between two points
    CIRCLE = "CIRCLE"  # Circular area with radius
    RECT = "RECT"  # Rectangular area with width and height


@dataclass
class Point:
    """Represents a 2D point with x and y coordinates."""
    x: float
    y: float


@dataclass
class BoundingRect:
    """
    Represents a bounding rectangle with position and dimensions.
    Matches the Java BoundingRect class.
    """
    x: float
    y: float
    width: float
    height: float

    def get_x(self) -> float:
        return self.x

    def get_y(self) -> float:
        return self.y

    def get_width(self) -> float:
        return self.width

    def get_height(self) -> float:
        return self.height


@dataclass
class Position:
    """
    Represents spatial positioning and location information for PDF objects.
    Closely mirrors the Java Position class with Python conventions.
    """
    page_index: Optional[int] = None
    shape: Optional[ShapeType] = None
    mode: Optional[PositionMode] = None
    bounding_rect: Optional[BoundingRect] = None
    text_starts_with: Optional[str] = None
    name: Optional[str] = None

    @staticmethod
    def at_page(page_index: int) -> 'Position':
        """
        Creates a position specification for an entire page.
        Equivalent to Position.fromPageIndex() in Java.
        """
        return Position(page_index=page_index, mode=PositionMode.CONTAINS)

    @staticmethod
    def at_page_coordinates(page_index: int, x: float, y: float) -> 'Position':
        """
        Creates a position specification for specific coordinates on a page.
        Equivalent to Position.onPageCoordinates() in Java.
        """
        position = Position.at_page(page_index)
        position.at_coordinates(Point(x, y))
        return position

    @staticmethod
    def by_name(name: str) -> 'Position':
        """
        Creates a position specification for finding objects by name.
        Equivalent to Position.byName() in Java.
        """
        position = Position()
        position.name = name
        return position

    def at_coordinates(self, point: Point) -> 'Position':
        """
        Sets the position to a specific point location.
        Equivalent to Position.set() in Java.
        """
        self.mode = PositionMode.CONTAINS
        self.shape = ShapeType.POINT
        self.bounding_rect = BoundingRect(point.x, point.y, 0, 0)
        return self

    def with_text_starts(self, text: str) -> 'Position':
        self.text_starts_with = text
        return self

    def move_x(self, x_offset: float) -> 'Position':
        """Move the position horizontally by the specified offset."""
        if self.bounding_rect:
            self.at_coordinates(Point(self.x() + x_offset, self.y()))
        return self

    def move_y(self, y_offset: float) -> 'Position':
        """Move the position vertically by the specified offset."""
        if self.bounding_rect:
            self.at_coordinates(Point(self.x(), self.y() + y_offset))
        return self

    def x(self) -> Optional[float]:
        """Returns the X coordinate of this position."""
        return self.bounding_rect.get_x() if self.bounding_rect else None

    def y(self) -> Optional[float]:
        """Returns the Y coordinate of this position."""
        return self.bounding_rect.get_y() if self.bounding_rect else None

    def copy(self) -> 'Position':
        """Creates a copy of this position."""
        # Create deep copy of bounding_rect if it exists
        bounding_rect_copy = None
        if self.bounding_rect:
            bounding_rect_copy = BoundingRect(
                self.bounding_rect.x,
                self.bounding_rect.y,
                self.bounding_rect.width,
                self.bounding_rect.height
            )

        pos = Position(self.page_index, self.shape, self.mode, bounding_rect_copy, self.text_starts_with)
        return pos


@dataclass
class ObjectRef:
    """
    Lightweight reference to a PDF object providing identity and type information.
    Mirrors the Java ObjectRef class exactly.
    """
    internal_id: str
    position: Position
    type: ObjectType

    def get_internal_id(self) -> str:
        """Returns the internal identifier for the referenced object."""
        return self.internal_id

    def get_position(self) -> Position:
        """Returns the current position information for the referenced object."""
        return self.position

    def set_position(self, position: Position) -> None:
        """Updates the position information for the referenced object."""
        self.position = position

    def get_type(self) -> ObjectType:
        """Returns the type classification of the referenced object."""
        return self.type

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "internalId": self.internal_id,
            "position": FindRequest._position_to_dict(self.position),
            "type": self.type.value
        }


@dataclass
class Color:
    """Represents an RGB color with optional alpha channel, values from 0-255."""
    r: int
    g: int
    b: int
    a: int = 255  # Alpha channel, default fully opaque

    def __post_init__(self):
        # Validation similar to Java client
        for component in [self.r, self.g, self.b, self.a]:
            if not 0 <= component <= 255:
                raise ValueError(f"Color component must be between 0 and 255, got {component}")


@dataclass
class Font:
    """Represents a font with name and size."""
    name: str
    size: float

    def __post_init__(self):
        if self.size <= 0:
            raise ValueError(f"Font size must be positive, got {self.size}")


@dataclass
class Image:
    """
    Represents an image object in a PDF document.
    Matches the Java Image class structure.
    """
    position: Optional[Position] = None
    format: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    data: Optional[bytes] = None

    def get_position(self) -> Optional[Position]:
        """Returns the position of this image."""
        return self.position

    def set_position(self, position: Position) -> None:
        """Sets the position of this image."""
        self.position = position


@dataclass
class Paragraph:
    """
    Represents a paragraph of text in a PDF document.
    Structure mirrors the Java Paragraph class.
    """
    position: Optional[Position] = None
    text_lines: Optional[List[str]] = None
    font: Optional[Font] = None
    color: Optional[Color] = None
    line_spacing: float = 1.2

    def get_position(self) -> Optional[Position]:
        """Returns the position of this paragraph."""
        return self.position

    def set_position(self, position: Position) -> None:
        """Sets the position of this paragraph."""
        self.position = position


# Request classes for API communication
@dataclass
class FindRequest:
    """Request object for find operations."""
    object_type: Optional[ObjectType]
    position: Optional[Position]
    hint: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "objectType": self.object_type.value if self.object_type else None,
            "position": self._position_to_dict(self.position) if self.position else None,
            "hint": self.hint
        }

    @staticmethod
    def _position_to_dict(position: Position) -> dict:
        """Convert Position to dictionary for JSON serialization."""
        result = {
            "pageIndex": position.page_index,
            "textStartsWith": position.text_starts_with
        }
        if position.name:
            result["name"] = position.name
        if position.shape:
            result["shape"] = position.shape.value
        if position.mode:
            result["mode"] = position.mode.value
        if position.bounding_rect:
            result["boundingRect"] = {
                "x": position.bounding_rect.x,
                "y": position.bounding_rect.y,
                "width": position.bounding_rect.width,
                "height": position.bounding_rect.height
            }
        return result


@dataclass
class DeleteRequest:
    """Request object for delete operations."""
    object_ref: ObjectRef

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "objectRef": {
                "internalId": self.object_ref.internal_id,
                "position": FindRequest._position_to_dict(self.object_ref.position),
                "type": self.object_ref.type.value
            }
        }


@dataclass
class MoveRequest:
    """Request object for move operations."""
    object_ref: ObjectRef
    position: Position

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        # Server API expects the new coordinates under 'newPosition' (see Java MoveRequest)
        return {
            "objectRef": {
                "internalId": self.object_ref.internal_id,
                "position": FindRequest._position_to_dict(self.object_ref.position),
                "type": self.object_ref.type.value
            },
            "newPosition": FindRequest._position_to_dict(self.position)
        }


@dataclass
class AddRequest:
    """Request object for add operations."""
    pdf_object: Any  # Can be Image, Paragraph, etc.

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization matching server API.
        Server expects an AddRequest with a nested 'object' containing the PDFObject
        (with a 'type' discriminator), mirroring Java AddRequest(PDFObject object).
        """
        obj = self.pdf_object
        return {
            "object": self._object_to_dict(obj)
        }

    def _object_to_dict(self, obj: Any) -> dict:
        """Convert PDF object to dictionary for JSON serialization."""
        import base64
        if isinstance(obj, Image):
            size = None
            if obj.width is not None and obj.height is not None:
                size = {"width": obj.width, "height": obj.height}
            data_b64 = None
            if obj.data is not None:
                # Java byte[] expects base64 string in JSON
                data_b64 = base64.b64encode(obj.data).decode("ascii")
            return {
                "type": "IMAGE",
                "position": FindRequest._position_to_dict(obj.position) if obj.position else None,
                "format": obj.format,
                "size": size,
                "data": data_b64
            }
        elif isinstance(obj, Paragraph):
            # Build lines -> List<TextLine> with minimal structure required by server
            lines = []
            if obj.text_lines:
                for line in obj.text_lines:
                    text_element = {
                        "text": line,
                        "font": {"name": obj.font.name, "size": obj.font.size} if obj.font else None,
                        "color": {"r": obj.color.r, "g": obj.color.g, "b": obj.color.b} if obj.color else None,
                        "position": FindRequest._position_to_dict(obj.position) if obj.position else None
                    }
                    text_line = {
                        "textElements": [text_element]
                    }
                    # TextLine has color and position
                    if obj.color:
                        text_line["color"] = {"r": obj.color.r, "g": obj.color.g, "b": obj.color.b}
                    if obj.position:
                        text_line["position"] = FindRequest._position_to_dict(obj.position)
                    lines.append(text_line)
            line_spacings = None
            if hasattr(obj, "line_spacing") and obj.line_spacing is not None:
                # Server expects a list
                line_spacings = [obj.line_spacing]
            return {
                "type": "PARAGRAPH",
                "position": FindRequest._position_to_dict(obj.position) if obj.position else None,
                "lines": lines,
                "lineSpacings": line_spacings,
                "font": {"name": obj.font.name, "size": obj.font.size} if obj.font else None
            }
        else:
            raise ValueError(f"Unsupported object type: {type(obj)}")


@dataclass
class ModifyRequest:
    """Request object for modify operations."""
    object_ref: ObjectRef
    new_object: Any

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "ref": {
                "internalId": self.object_ref.internal_id,
                "position": FindRequest._position_to_dict(self.object_ref.position),
                "type": self.object_ref.type.value
            },
            "newObject": AddRequest(None)._object_to_dict(self.new_object)
        }


@dataclass
class ModifyTextRequest:
    """Request object for text modification operations."""
    object_ref: ObjectRef
    new_text: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "ref": {
                "internalId": self.object_ref.internal_id,
                "position": FindRequest._position_to_dict(self.object_ref.position),
                "type": self.object_ref.type.value
            },
            "newTextLine": self.new_text
        }


@dataclass
class ChangeFormFieldRequest:
    object_ref: ObjectRef
    value: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "ref": {
                "internalId": self.object_ref.internal_id,
                "position": FindRequest._position_to_dict(self.object_ref.position),
                "type": self.object_ref.type.value
            },
            "value": self.value
        }


@dataclass
class FormFieldRef(ObjectRef):
    """
    Represents a form field reference with additional form-specific properties.
    Extends ObjectRef to include form field name and value.
    """
    name: Optional[str] = None
    value: Optional[str] = None

    def get_name(self) -> Optional[str]:
        """Get the form field name."""
        return self.name

    def get_value(self) -> Optional[str]:
        """Get the form field value."""
        return self.value
