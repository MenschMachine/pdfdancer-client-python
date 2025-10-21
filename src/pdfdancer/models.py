"""
Model classes for the PDFDancer Python client.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Any, Dict, Mapping, Tuple, ClassVar, Union


@dataclass(frozen=True)
class PageSize:
    """Represents a page size specification, covering both standard and custom dimensions."""

    name: Optional[str]
    width: float
    height: float

    _STANDARD_SIZES: ClassVar[Dict[str, Tuple[float, float]]] = {
        "A4": (595.0, 842.0),
        "LETTER": (612.0, 792.0),
        "LEGAL": (612.0, 1008.0),
        "TABLOID": (792.0, 1224.0),
        "A3": (842.0, 1191.0),
        "A5": (420.0, 595.0),
    }

    # Convenience aliases populated after class definition; annotated for type checkers.
    A4: ClassVar['PageSize']
    LETTER: ClassVar['PageSize']
    LEGAL: ClassVar['PageSize']
    TABLOID: ClassVar['PageSize']
    A3: ClassVar['PageSize']
    A5: ClassVar['PageSize']

    def __post_init__(self) -> None:
        if not isinstance(self.width, (int, float)) or not isinstance(self.height, (int, float)):
            raise TypeError("Page width and height must be numeric")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Page width and height must be positive values")

        width = float(self.width)
        height = float(self.height)
        object.__setattr__(self, 'width', width)
        object.__setattr__(self, 'height', height)

        if self.name is not None:
            if not isinstance(self.name, str):
                raise TypeError("Page size name must be a string when provided")
            normalized_name = self.name.strip().upper()
            object.__setattr__(self, 'name', normalized_name if normalized_name else None)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_name(cls, name: str) -> 'PageSize':
        """Create a page size from a known standard name."""
        if not name or not isinstance(name, str):
            raise ValueError("Page size name must be a non-empty string")
        normalized = name.strip().upper()
        if normalized not in cls._STANDARD_SIZES:
            raise ValueError(f"Unknown page size name: {name}")
        width, height = cls._STANDARD_SIZES[normalized]
        return cls(name=normalized, width=width, height=height)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> 'PageSize':
        """Create a page size from a dictionary-like object."""
        width = data.get('width') if isinstance(data, Mapping) else None
        height = data.get('height') if isinstance(data, Mapping) else None
        if width is None or height is None:
            raise ValueError("Page size dictionary must contain 'width' and 'height'")
        name = data.get('name') if isinstance(data, Mapping) else None
        return cls(name=name, width=width, height=height)

    @classmethod
    def coerce(cls, value: Union['PageSize', str, Mapping[str, Any]]) -> 'PageSize':
        """Normalize various page size inputs into a PageSize instance."""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls.from_name(value)
        if isinstance(value, Mapping):
            return cls.from_dict(value)
        raise TypeError(f"Cannot convert type {type(value)} to PageSize")

    @classmethod
    def standard_names(cls) -> List[str]:
        """Return a list of supported standard page size names."""
        return sorted(cls._STANDARD_SIZES.keys())


# Populate convenience constants for standard sizes.
PageSize.A4 = PageSize.from_name("A4")
PageSize.LETTER = PageSize.from_name("LETTER")
PageSize.LEGAL = PageSize.from_name("LEGAL")
PageSize.TABLOID = PageSize.from_name("TABLOID")
PageSize.A3 = PageSize.from_name("A3")
PageSize.A5 = PageSize.from_name("A5")


class Orientation(Enum):
    """Page orientation options."""
    PORTRAIT = "PORTRAIT"
    LANDSCAPE = "LANDSCAPE"


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
    """
    page_index: Optional[int] = None
    shape: Optional[ShapeType] = None
    mode: Optional[PositionMode] = None
    bounding_rect: Optional[BoundingRect] = None
    text_starts_with: Optional[str] = None
    text_pattern: Optional[str] = None
    name: Optional[str] = None

    @staticmethod
    def at_page(page_index: int) -> 'Position':
        """
        Creates a position specification for an entire page.
        """
        return Position(page_index=page_index, mode=PositionMode.CONTAINS)

    @staticmethod
    def at_page_coordinates(page_index: int, x: float, y: float) -> 'Position':
        """
        Creates a position specification for specific coordinates on a page.
        """
        position = Position.at_page(page_index)
        position.at_coordinates(Point(x, y))
        return position

    @staticmethod
    def by_name(name: str) -> 'Position':
        """
        Creates a position specification for finding objects by name.
        """
        position = Position()
        position.name = name
        return position

    def at_coordinates(self, point: Point) -> 'Position':
        """
        Sets the position to a specific point location.
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


@dataclass
class ObjectRef:
    """
    Lightweight reference to a PDF object providing identity and type information.
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
            "textStartsWith": position.text_starts_with,
            "textPattern": position.text_pattern
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
        # Server API expects the new coordinates under 'newPosition'
        return {
            "objectRef": {
                "internalId": self.object_ref.internal_id,
                "position": FindRequest._position_to_dict(self.object_ref.position),
                "type": self.object_ref.type.value
            },
            "newPosition": FindRequest._position_to_dict(self.position)
        }


@dataclass
class PageMoveRequest:
    """Request object for moving pages within the document."""
    from_page_index: int
    to_page_index: int

    def to_dict(self) -> dict:
        return {
            "fromPageIndex": self.from_page_index,
            "toPageIndex": self.to_page_index
        }


@dataclass
class AddRequest:
    """Request object for add operations."""
    pdf_object: Any  # Can be Image, Paragraph, etc.

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization matching server API.
        Server expects an AddRequest with a nested 'object' containing the PDFObject
        (with a 'type' discriminator).
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
                        "color": {"red": obj.color.r, "green": obj.color.g, "blue": obj.color.b,
                                  "alpha": obj.color.a} if obj.color else None,
                        "position": FindRequest._position_to_dict(obj.position) if obj.position else None
                    }
                    text_line = {
                        "textElements": [text_element]
                    }
                    # TextLine has color and position
                    if obj.color:
                        text_line["color"] = {"red": obj.color.r, "green": obj.color.g, "blue": obj.color.b,
                                              "alpha": obj.color.a}
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


class FontType(Enum):
    """Font type classification from the PDF."""
    SYSTEM = "SYSTEM"
    STANDARD = "STANDARD"
    EMBEDDED = "EMBEDDED"


@dataclass
class FontRecommendation:
    """Represents a font recommendation with similarity score."""
    font_name: str
    font_type: 'FontType'
    similarity_score: float

    def get_font_name(self) -> str:
        """Get the recommended font name."""
        return self.font_name

    def get_font_type(self) -> 'FontType':
        """Get the recommended font type."""
        return self.font_type

    def get_similarity_score(self) -> float:
        """Get the similarity score."""
        return self.similarity_score


@dataclass
class TextStatus:
    """Status information for text objects."""
    modified: bool
    encodable: bool
    font_type: FontType
    font_recommendation: FontRecommendation

    def is_modified(self) -> bool:
        """Check if the text has been modified."""
        return self.modified

    def is_encodable(self) -> bool:
        """Check if the text is encodable."""
        return self.encodable

    def get_font_type(self) -> FontType:
        """Get the font type."""
        return self.font_type

    def get_font_recommendation(self) -> FontRecommendation:
        """Get the font recommendation."""
        return self.font_recommendation


class TextObjectRef(ObjectRef):
    """
    Represents a text object reference with additional text-specific properties.
    Extends ObjectRef to include text content, font information, and hierarchical structure.
    """

    def __init__(self, internal_id: str, position: Position, object_type: ObjectType,
                 text: Optional[str] = None, font_name: Optional[str] = None,
                 font_size: Optional[float] = None, line_spacings: Optional[List[float]] = None,
                 color: Optional[Color] = None, status: Optional[TextStatus] = None):
        super().__init__(internal_id, position, object_type)
        self.text = text
        self.font_name = font_name
        self.font_size = font_size
        self.line_spacings = line_spacings
        self.color = color
        self.status = status
        self.children: List['TextObjectRef'] = []

    def get_text(self) -> Optional[str]:
        """Get the text content."""
        return self.text

    def get_font_name(self) -> Optional[str]:
        """Get the font name."""
        return self.font_name

    def get_font_size(self) -> Optional[float]:
        """Get the font size."""
        return self.font_size

    def get_line_spacings(self) -> Optional[List[float]]:
        """Get the line spacings."""
        return self.line_spacings

    def get_color(self) -> Optional[Color]:
        """Get the color."""
        return self.color

    def get_children(self) -> List['TextObjectRef']:
        """Get the child text objects."""
        return self.children

    def get_status(self) -> Optional[TextStatus]:
        """Get the status information."""
        return self.status


@dataclass
class PageRef(ObjectRef):
    """
    Represents a page reference with additional page-specific properties.
    Extends ObjectRef to include page size and orientation.
    """
    page_size: Optional[PageSize]
    orientation: Optional[Orientation]

    def get_page_size(self) -> Optional[PageSize]:
        """Get the page size."""
        return self.page_size

    def get_orientation(self) -> Optional[Orientation]:
        """Get the page orientation."""
        return self.orientation


@dataclass
class CommandResult:
    """
    Result object returned by certain API endpoints indicating the outcome of an operation.
    """
    command_name: str
    element_id: str | None
    message: str | None
    success: bool
    warning: str | None

    @classmethod
    def from_dict(cls, data: dict) -> 'CommandResult':
        """Create a CommandResult from a dictionary response."""
        return cls(
            command_name=data.get('commandName', ''),
            element_id=data.get('elementId', ''),
            message=data.get('message', ''),
            success=data.get('success', False),
            warning=data.get('warning', '')
        )

    @classmethod
    def empty(cls, command_name: str, element_id: str | None) -> 'CommandResult':
        return CommandResult(command_name=command_name, element_id=element_id, message=None, success=True, warning=None)
