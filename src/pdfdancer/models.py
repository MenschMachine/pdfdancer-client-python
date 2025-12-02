"""
Model classes for the PDFDancer Python client.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, Dict, List, Mapping, Optional, Tuple, Union


@dataclass(frozen=True)
class PageSize:
    """Represents a page size specification, covering both standard and custom dimensions.

    Parameters:
    - name: Optional canonical name of the size (e.g. "A4", "LETTER"). Will be upper‑cased.
    - width: Page width in PDF points (1/72 inch).
    - height: Page height in PDF points (1/72 inch).

    Notes:
    - Use `PageSize.from_name()` or the convenience constants (e.g. `PageSize.A4`) for common sizes.
    - `width` and `height` must be positive numbers and are validated in `__post_init__`.

    Examples:
    - From standard name:
      ```python
      size = PageSize.from_name("A4")  # or PageSize.A4
      ```
    - From custom dimensions:
      ```python
      size = PageSize(name=None, width=500.0, height=700.0)
      ```
    - From dict (e.g. deserialized JSON):
      ```python
      size = PageSize.from_dict({"width": 612, "height": 792, "name": "letter"})
      ```
    - Coercion utility:
      ```python
      size = PageSize.coerce("A4")
      size = PageSize.coerce({"width": 300, "height": 300})
      ```
    """

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
    A4: ClassVar["PageSize"]
    LETTER: ClassVar["PageSize"]
    LEGAL: ClassVar["PageSize"]
    TABLOID: ClassVar["PageSize"]
    A3: ClassVar["PageSize"]
    A5: ClassVar["PageSize"]

    def __post_init__(self) -> None:
        if not isinstance(self.width, (int, float)) or not isinstance(
            self.height, (int, float)
        ):
            raise TypeError("Page width and height must be numeric")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Page width and height must be positive values")

        width = float(self.width)
        height = float(self.height)
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "height", height)

        if self.name is not None:
            if not isinstance(self.name, str):
                raise TypeError("Page size name must be a string when provided")
            normalized_name = self.name.strip().upper()
            object.__setattr__(
                self, "name", normalized_name if normalized_name else None
            )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_name(cls, name: str) -> "PageSize":
        """Create a page size from a known standard name."""
        if not name or not isinstance(name, str):
            raise ValueError("Page size name must be a non-empty string")
        normalized = name.strip().upper()
        if normalized not in cls._STANDARD_SIZES:
            raise ValueError(f"Unknown page size name: {name}")
        width, height = cls._STANDARD_SIZES[normalized]
        return cls(name=normalized, width=width, height=height)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PageSize":
        """Create a page size from a dictionary-like object."""
        width = data.get("width") if isinstance(data, Mapping) else None
        height = data.get("height") if isinstance(data, Mapping) else None
        if width is None or height is None:
            raise ValueError("Page size dictionary must contain 'width' and 'height'")
        name = data.get("name") if isinstance(data, Mapping) else None
        return cls(name=name, width=width, height=height)

    @classmethod
    def coerce(cls, value: Union["PageSize", str, Mapping[str, Any]]) -> "PageSize":
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
    """Server object type discriminator used in refs, requests, and snapshots."""

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
    BUTTON = "BUTTON"
    DROPDOWN = "DROPDOWN"
    TEXT_ELEMENT = "TEXT_ELEMENT"


class PositionMode(Enum):
    """Defines how position matching should be performed when searching for objects."""

    INTERSECT = "INTERSECT"  # Objects that intersect with the specified position area
    CONTAINS = (
        "CONTAINS"  # Objects completely contained within the specified position area
    )


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
    Spatial locator used to find or place objects on a page.

    Parameters:
    - page_number: One-based page number this position refers to. Required for most operations
      that place or search on a specific page; use `Position.at_page()` as a shortcut.
    - shape: Optional geometric shape used when matching by area (`POINT`, `LINE`, `CIRCLE`, `RECT`).
    - mode: How to match objects relative to the shape (`INTERSECT` or `CONTAINS`).
    - bounding_rect: Rectangle describing the area or point (for `POINT`, width/height are 0).
    - text_starts_with: Filter for text objects whose content starts with this string.
    - text_pattern: Regex pattern to match text content.
    - name: Named anchor or element name to target (e.g. form field name).

    Builder helpers:
    - `Position.at_page(page_number)` – target a whole page.
    - `Position.at_page_coordinates(page_number, x, y)` – target a point on a page.
    - `Position.by_name(name)` – target object(s) by name.
    - `pos.at_coordinates(Point(x, y))` – switch to a point on the current page.
    - `pos.move_x(dx)`, `pos.move_y(dy)` – offset the current coordinates.

    Examples:
    ```python
    # A point on page 0
    pos = Position.at_page_coordinates(0, x=72, y=720)

    # Search by name (e.g. a form field) and then move down 12 points
    pos = Position.by_name("Email").move_y(-12)

    # Match anything intersecting a rectangular area on page 1
    pos = Position.at_page(1)
    pos.shape = ShapeType.RECT
    pos.mode = PositionMode.INTERSECT
    pos.bounding_rect = BoundingRect(x=100, y=100, width=200, height=50)
    ```
    """

    page_number: Optional[int] = None
    shape: Optional[ShapeType] = None
    mode: Optional[PositionMode] = None
    bounding_rect: Optional[BoundingRect] = None
    text_starts_with: Optional[str] = None
    text_pattern: Optional[str] = None
    name: Optional[str] = None

    @staticmethod
    def at_page(page_number: int) -> "Position":
        """
        Creates a position specification for an entire page.
        """
        return Position(page_number=page_number, mode=PositionMode.CONTAINS)

    @staticmethod
    def at_page_coordinates(page_number: int, x: float, y: float) -> "Position":
        """
        Creates a position specification for specific coordinates on a page.
        """
        position = Position.at_page(page_number)
        position.at_coordinates(Point(x, y))
        return position

    @staticmethod
    def by_name(name: str) -> "Position":
        """
        Creates a position specification for finding objects by name.
        """
        position = Position()
        position.name = name
        return position

    def at_coordinates(self, point: Point) -> "Position":
        """
        Sets the position to a specific point location.
        """
        self.mode = PositionMode.CONTAINS
        self.shape = ShapeType.POINT
        self.bounding_rect = BoundingRect(point.x, point.y, 0, 0)
        return self

    def with_text_starts(self, text: str) -> "Position":
        self.text_starts_with = text
        return self

    def move_x(self, x_offset: float) -> "Position":
        """Move the position horizontally by the specified offset."""
        if self.bounding_rect:
            self.at_coordinates(Point(self.x() + x_offset, self.y()))
        return self

    def move_y(self, y_offset: float) -> "Position":
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
    Reference to an object in a PDF document returned by the server.

    Parameters:
    - internal_id: Server-side identifier for the object.
    - position: Position information describing where the object is.
    - type: Object type (see `ObjectType`).

    Usage:
    - Instances are typically returned in snapshots or find results.
    - Pass an `ObjectRef` to request objects such as `MoveRequest`, `DeleteRequest`,
      `ModifyRequest`, or `ModifyTextRequest`.

    Example:
    ```python
    # Move an object to a new position
    new_pos = Position.at_page_coordinates(0, 120, 500)
    payload = MoveRequest(object_ref=obj_ref, position=new_pos).to_dict()
    ```
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
        # Normalize type back to API format (API uses "CHECKBOX" not "CHECK_BOX")
        type_value = self.type.value
        if type_value == "CHECK_BOX":
            type_value = "CHECKBOX"

        return {
            "internalId": self.internal_id,
            "position": FindRequest._position_to_dict(self.position),
            "type": type_value,
        }


@dataclass
class Color:
    """RGB color with optional alpha channel.

    Parameters:
    - r: Red component (0-255)
    - g: Green component (0-255)
    - b: Blue component (0-255)
    - a: Alpha component (0-255), default 255 (opaque)

    Raises:
    - ValueError: If any component is outside 0-255.

    Example:
    ```python
    red = Color(255, 0, 0)
    semi_transparent_black = Color(0, 0, 0, a=128)
    ```
    """

    r: int
    g: int
    b: int
    a: int = 255  # Alpha channel, default fully opaque

    def __post_init__(self):
        for component in [self.r, self.g, self.b, self.a]:
            if not 0 <= component <= 255:
                raise ValueError(
                    f"Color component must be between 0 and 255, got {component}"
                )


@dataclass
class Font:
    """Font face and size.

    Parameters:
    - name: Font family name. Can be one of `StandardFonts` values or any embedded font name.
    - size: Font size in points (> 0).

    Raises:
    - ValueError: If `size` is not positive.

    Example:
    ```python
    from pdfdancer.models import Font, StandardFonts

    title_font = Font(name=StandardFonts.HELVETICA_BOLD.value, size=16)
    body_font = Font(name="MyEmbeddedFont", size=10.5)
    ```
    """

    name: str
    size: float

    def __post_init__(self):
        if self.size <= 0:
            raise ValueError(f"Font size must be positive, got {self.size}")


@dataclass
class PathSegment:
    """
    Base class for vector path segments.

    Parameters:
    - stroke_color: Outline color for the segment (`Color`).
    - fill_color: Fill color for closed shapes when applicable (`Color`).
    - stroke_width: Line width in points.
    - dash_array: Dash pattern (e.g. `[3, 2]` for 3 on, 2 off). None or empty for solid.
    - dash_phase: Offset into the dash pattern.

    Notes:
    - Concrete subclasses are `Line` and `Bezier`.
    - Used inside `Path.path_segments` and serialized by `AddRequest`.
    """

    stroke_color: Optional[Color] = None
    fill_color: Optional[Color] = None
    stroke_width: Optional[float] = None
    dash_array: Optional[List[float]] = None
    dash_phase: Optional[float] = None

    def get_stroke_color(self) -> Optional[Color]:
        """Color used for drawing the segment's outline or stroke."""
        return self.stroke_color

    def get_fill_color(self) -> Optional[Color]:
        """Color used for filling the segment's interior area (if applicable)."""
        return self.fill_color

    def get_stroke_width(self) -> Optional[float]:
        """Width of the stroke line in PDF coordinate units."""
        return self.stroke_width

    def get_dash_array(self) -> Optional[List[float]]:
        """Dash pattern for stroking the path segment. Null or empty means solid line."""
        return self.dash_array

    def get_dash_phase(self) -> Optional[float]:
        """Dash phase (offset) into the dash pattern in user space units."""
        return self.dash_phase


@dataclass
class Line(PathSegment):
    """
    Straight line segment between two points.

    Parameters:
    - p0: Start point.
    - p1: End point.

    Example:
    ```python
    from pdfdancer.models import Line, Point, Path

    line = Line(p0=Point(10, 10), p1=Point(100, 10))
    path = Path(path_segments=[line])
    ```
    """

    p0: Optional[Point] = None
    p1: Optional[Point] = None

    def get_p0(self) -> Optional[Point]:
        """Returns the starting point of this line segment."""
        return self.p0

    def get_p1(self) -> Optional[Point]:
        """Returns the ending point of this line segment."""
        return self.p1


@dataclass
class Bezier(PathSegment):
    """
    Cubic Bezier curve segment defined by 4 points.

    Parameters:
    - p0: Start point.
    - p1: First control point.
    - p2: Second control point.
    - p3: End point.

    Example:
    ```python
    curve = Bezier(
        p0=Point(10, 10), p1=Point(50, 80), p2=Point(80, 50), p3=Point(120, 10)
    )
    ```
    """

    p0: Optional[Point] = None
    p1: Optional[Point] = None
    p2: Optional[Point] = None
    p3: Optional[Point] = None

    def get_p0(self) -> Optional[Point]:
        """Returns the starting point p0 of this Bezier segment."""
        return self.p0

    def get_p1(self) -> Optional[Point]:
        """Returns the first control point p1 of this Bezier segment."""
        return self.p1

    def get_p2(self) -> Optional[Point]:
        """Returns the second control point p2 of this Bezier segment."""
        return self.p2

    def get_p3(self) -> Optional[Point]:
        """Returns the ending point p3 of this Bezier segment."""
        return self.p3


@dataclass
class Path:
    """
    Vector path composed of one or more `PathSegment`s.

    Parameters:
    - position: Where to place the path on the page.
    - path_segments: List of `Line` and/or `Bezier` segments.
    - even_odd_fill: If True, use even-odd rule for fills; otherwise nonzero winding.

    Example (adding a triangle to a page):
    ```python
    from pdfdancer.models import Path, Line, Point, Position, AddRequest

    tri = Path(
        position=Position.at_page_coordinates(0, 100, 100),
        path_segments=[
            Line(Point(0, 0), Point(50, 100)),
            Line(Point(50, 100), Point(100, 0)),
            Line(Point(100, 0), Point(0, 0)),
        ],
        even_odd_fill=True,
    )
    payload = AddRequest(tri).to_dict()
    ```
    """

    position: Optional[Position] = None
    path_segments: Optional[List[PathSegment]] = None
    even_odd_fill: Optional[bool] = None

    def get_position(self) -> Optional[Position]:
        """Returns the position of this path."""
        return self.position

    def set_position(self, position: Position) -> None:
        """Sets the position of this path."""
        self.position = position

    def get_path_segments(self) -> Optional[List[PathSegment]]:
        """Returns the list of path segments that compose this path."""
        return self.path_segments

    def get_even_odd_fill(self) -> Optional[bool]:
        """Returns whether even-odd fill rule should be used (true) or nonzero (false)."""
        return self.even_odd_fill


@dataclass
class Image:
    """
    Raster image to be placed on a page.

    Parameters:
    - position: Where to place the image. Use `Position.at_page_coordinates(page, x, y)`.
    - format: Image format hint for the server (e.g. "PNG", "JPEG"). Optional.
    - width: Target width in points. Optional; server may infer from data.
    - height: Target height in points. Optional; server may infer from data.
    - data: Raw image bytes. If provided, it will be base64-encoded in `AddRequest.to_dict()`.

    Example:
    ```python
    from pdfdancer.models import Image, Position, AddRequest

    img = Image(
        position=Position.at_page_coordinates(0, 72, 600),
        format="PNG",
        width=128,
        height=64,
        data=open("/path/logo.png", "rb").read(),
    )
    payload = AddRequest(img).to_dict()
    ```
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
class TextLine:
    """
    One line of text to add to a page.

    Parameters:
    - position: Anchor position where the first line begins.
    - text: the text
      provide separate entries for multiple lines.
    - font: Font to use for all text elements unless overridden later.
    - color: Text color.

    """

    position: Optional[Position] = None
    font: Optional[Font] = None
    color: Optional[Color] = None
    line_spacing: float = 1.2
    text: str = ""

    def get_position(self) -> Optional[Position]:
        """Returns the position of this paragraph."""
        return self.position

    def set_position(self, position: Position) -> None:
        """Sets the position of this paragraph."""
        self.position = position


@dataclass
class Paragraph:
    """
    Multi-line text paragraph to add to a page.

    Parameters:
    - position: Anchor position where the first line begins.
    - text_lines: List of strings, one per line. Use `\n` within a string only if desired; normally
      provide separate entries for multiple lines.
    - font: Font to use for all text elements unless overridden later.
    - color: Text color.
    - line_spacing: Distance multiplier between lines. Server expects a list, handled for you by `AddRequest`.

    Example:
    ```python
    from pdfdancer.models import Paragraph, Position, Font, Color, StandardFonts, AddRequest

    para = Paragraph(
        position=Position.at_page_coordinates(0, 72, 700),
        text_lines=["Hello", "PDFDancer!"],
        font=Font(StandardFonts.HELVETICA.value, 12),
        color=Color(50, 50, 50),
        line_spacing=1.4,
    )
    payload = AddRequest(para).to_dict()
    ```
    """

    position: Optional[Position] = None
    text_lines: Optional[List[TextLine]] = None
    font: Optional[Font] = None
    color: Optional[Color] = None
    line_spacing: float = 1.2
    line_spacings: Optional[List[float]] = None

    def get_position(self) -> Optional[Position]:
        """Returns the position of this paragraph."""
        return self.position

    def set_position(self, position: Position) -> None:
        """Sets the position of this paragraph."""
        self.position = position

    def clear_lines(self) -> None:
        """Removes all text lines from this paragraph."""
        self.text_lines = []

    def add_line(self, text_line: TextLine) -> None:
        """Appends a text line to this paragraph."""
        if self.text_lines is None:
            self.text_lines = []
        self.text_lines.append(text_line)

    def get_lines(self) -> List[TextLine]:
        """Returns the list of text lines, defaulting to an empty list."""
        if self.text_lines is None:
            self.text_lines = []
        return self.text_lines

    def set_lines(self, lines: List[TextLine]) -> None:
        """Replaces the current text lines with the provided list."""
        self.text_lines = list(lines)

    def set_line_spacings(self, spacings: Optional[List[float]]) -> None:
        """Sets the per-line spacing factors for this paragraph."""
        self.line_spacings = list(spacings) if spacings else None

    def get_line_spacings(self) -> Optional[List[float]]:
        """Returns the per-line spacing factors if present."""
        return list(self.line_spacings) if self.line_spacings else None


# Request classes for API communication
@dataclass
class FindRequest:
    """Request for locating objects.

    Parameters:
    - object_type: Filter by `ObjectType` (optional). If None, all types may be returned.
    - position: `Position` describing where/how to search.
    - hint: Optional backend hint or free-form note to influence matching.

    Usage:
    ```python
    req = FindRequest(
        object_type=ObjectType.TEXT_LINE,
        position=Position.at_page_coordinates(0, 72, 700).with_text_starts("Hello"),
    )
    payload = req.to_dict()
    ```
    """

    object_type: Optional[ObjectType]
    position: Optional[Position]
    hint: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "objectType": self.object_type.value if self.object_type else None,
            "position": (
                self._position_to_dict(self.position) if self.position else None
            ),
            "hint": self.hint,
        }

    @staticmethod
    def _position_to_dict(position: Position) -> dict:
        """Convert Position to dictionary for JSON serialization."""
        result = {
            "pageNumber": position.page_number,
            "textStartsWith": position.text_starts_with,
            "textPattern": position.text_pattern,
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
                "height": position.bounding_rect.height,
            }
        return result


@dataclass
class DeleteRequest:
    """Request to delete an existing object.

    Parameters:
    - object_ref: The object to delete.

    Example:
    ```python
    payload = DeleteRequest(object_ref=obj_ref).to_dict()
    ```
    """

    object_ref: ObjectRef

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        # Use ObjectRef.to_dict() to ensure proper type normalization
        return {"objectRef": self.object_ref.to_dict()}


@dataclass
class MoveRequest:
    """Request to move an existing object to a new position.

    Parameters:
    - object_ref: The object to move (obtained from a snapshot or find call).
    - position: The new target `Position` (commonly a point created with `Position.at_page_coordinates`).

    Example:
    ```python
    new_pos = Position.at_page_coordinates(0, 200, 500)
    req = MoveRequest(object_ref=obj_ref, position=new_pos)
    payload = req.to_dict()
    ```
    """

    object_ref: ObjectRef
    position: Position

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        # Server API expects the new coordinates under 'newPosition'
        # Use ObjectRef.to_dict() to ensure proper type normalization
        return {
            "objectRef": self.object_ref.to_dict(),
            "newPosition": FindRequest._position_to_dict(self.position),
        }


@dataclass
class RedactTarget:
    """A single redaction target identifying an object by its internal ID."""

    id: str
    replacement: str

    def to_dict(self) -> dict:
        return {"id": self.id, "replacement": self.replacement}


@dataclass
class RedactRequest:
    """Request for redacting content from a PDF document."""

    targets: List["RedactTarget"]
    default_replacement: str
    placeholder_color: "Color"

    def to_dict(self) -> dict:
        return {
            "targets": [t.to_dict() for t in self.targets],
            "defaultReplacement": self.default_replacement,
            "placeholderColor": {
                "r": self.placeholder_color.r,
                "g": self.placeholder_color.g,
                "b": self.placeholder_color.b,
                "a": self.placeholder_color.a,
            },
        }


@dataclass
class RedactResponse:
    """Response from a redaction operation."""

    count: int
    success: bool
    warnings: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> "RedactResponse":
        return cls(
            count=data.get("count", 0),
            success=data.get("success", False),
            warnings=data.get("warnings", []),
        )


@dataclass
class PageMoveRequest:
    """Request to reorder pages.

    Parameters:
    - from_page: 1-based page number of the page to move.
    - to_page: 1-based destination page number.

    Example:
    ```python
    # Move first page to the end
    req = PageMoveRequest(from_page=1, to_page=doc_page_count)
    payload = req.to_dict()
    ```
    """

    from_page: int
    to_page: int

    def to_dict(self) -> dict:
        return {
            "fromPage": self.from_page,
            "toPage": self.to_page,
        }


@dataclass
class AddPageRequest:
    """Request to add a new page to the document.

    Parameters:
    - page_number: Optional 1-based page number where the new page should be inserted.
    - orientation: Optional page orientation (portrait or landscape).
    - page_size: Optional size of the page.

    Only populated fields are sent to the server to maintain backward compatibility
    with default server behavior.
    """

    page_number: Optional[int] = None
    orientation: Optional[Orientation] = None
    page_size: Optional[PageSize] = None

    def to_dict(self) -> dict:
        payload: Dict[str, Any] = {}
        if self.page_number is not None:
            payload["pageNumber"] = int(self.page_number)
        if self.orientation is not None:
            orientation_value: Orientation
            if isinstance(self.orientation, Orientation):
                orientation_value = self.orientation
            elif isinstance(self.orientation, str):
                normalized = self.orientation.strip().upper()
                orientation_value = Orientation(normalized)
            else:
                raise TypeError(
                    "Orientation must be an Orientation enum or string value"
                )
            payload["orientation"] = orientation_value.value
        if self.page_size is not None:
            page_size = PageSize.coerce(self.page_size)
            payload["pageSize"] = page_size.to_dict()
        return payload


@dataclass
class AddRequest:
    """Request to add a new object to the document.

    Parameters:
    - pdf_object: The object to add (e.g. `Image`, `Paragraph`, or `Path`).

    Usage:
    ```python
    para = Paragraph(position=Position.at_page_coordinates(0, 72, 700), text_lines=["Hello"])
    req = AddRequest(para)
    payload = req.to_dict()  # ready to send to the server API
    ```

    Notes:
    - Serialization details (like base64 for image `data`, or per-segment position for paths)
      are handled for you in `to_dict()`.
    """

    pdf_object: Any  # Can be Image, Paragraph, etc.

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization matching server API.
        Server expects an AddRequest with a nested 'object' containing the PDFObject
        (with a 'type' discriminator).
        """
        obj = self.pdf_object
        return {"object": self._object_to_dict(obj)}

    def _object_to_dict(self, obj: Any) -> dict:
        """Convert PDF object to dictionary for JSON serialization."""
        import base64

        from .models import Path as PathModel

        if isinstance(obj, PathModel):
            # Serialize Path object
            segments = []
            if obj.path_segments:
                for seg in obj.path_segments:
                    seg_dict = self._segment_to_dict(seg)
                    # Include per-segment position to satisfy backend validation (matches Java client)
                    if obj.position:
                        seg_dict["position"] = FindRequest._position_to_dict(
                            obj.position
                        )
                    segments.append(seg_dict)

            return {
                "type": "PATH",
                "position": (
                    FindRequest._position_to_dict(obj.position)
                    if obj.position
                    else None
                ),
                "pathSegments": segments if segments else None,
                "evenOddFill": obj.even_odd_fill,
            }
        elif isinstance(obj, Image):
            size = None
            if obj.width is not None and obj.height is not None:
                size = {"width": obj.width, "height": obj.height}
            data_b64 = None
            if obj.data is not None:
                # Java byte[] expects base64 string in JSON
                data_b64 = base64.b64encode(obj.data).decode("ascii")
            return {
                "type": "IMAGE",
                "position": (
                    FindRequest._position_to_dict(obj.position)
                    if obj.position
                    else None
                ),
                "format": obj.format,
                "size": size,
                "data": data_b64,
            }
        elif isinstance(obj, Paragraph):

            def _font_to_dict(font: Optional[Font]) -> Optional[dict]:
                if font:
                    return {"name": font.name, "size": font.size}
                return None

            def _color_to_dict(color: Optional[Color]) -> Optional[dict]:
                if color:
                    return {
                        "red": color.r,
                        "green": color.g,
                        "blue": color.b,
                        "alpha": color.a,
                    }
                return None

            lines_payload = []
            if obj.text_lines:
                for line in obj.text_lines:
                    if isinstance(line, TextLine):
                        line_text = line.text
                        line_font = line.font or obj.font
                        line_color = line.color or obj.color
                        line_position = line.position or obj.position
                    else:
                        line_text = str(line)
                        line_font = obj.font
                        line_color = obj.color
                        line_position = obj.position

                    text_element = {
                        "text": line_text,
                        "font": _font_to_dict(line_font),
                        "color": _color_to_dict(line_color),
                        "position": (
                            FindRequest._position_to_dict(line_position)
                            if line_position
                            else None
                        ),
                    }
                    text_line = {"textElements": [text_element]}
                    if line_color:
                        text_line["color"] = _color_to_dict(line_color)
                    if line_position:
                        text_line["position"] = FindRequest._position_to_dict(
                            line_position
                        )
                    lines_payload.append(text_line)

            line_spacings = None
            if getattr(obj, "line_spacings", None):
                line_spacings = list(obj.line_spacings)
            elif getattr(obj, "line_spacing", None) is not None:
                line_spacings = [obj.line_spacing]

            return {
                "type": "PARAGRAPH",
                "position": (
                    FindRequest._position_to_dict(obj.position)
                    if obj.position
                    else None
                ),
                "lines": lines_payload if lines_payload else None,
                "lineSpacings": line_spacings,
                "font": _font_to_dict(obj.font),
            }
        elif isinstance(obj, TextLine):

            def _font_to_dict(font: Optional[Font]) -> Optional[dict]:
                if font:
                    return {"name": font.name, "size": font.size}
                return None

            def _color_to_dict(color: Optional[Color]) -> Optional[dict]:
                if color:
                    return {
                        "red": color.r,
                        "green": color.g,
                        "blue": color.b,
                        "alpha": color.a,
                    }
                return None

            # Build textElement with only non-null fields
            text_element = {
                "text": obj.text,
            }

            if obj.font:
                text_element["font"] = _font_to_dict(obj.font)
            if obj.color:
                text_element["color"] = _color_to_dict(obj.color)
            if obj.position:
                text_element["position"] = FindRequest._position_to_dict(obj.position)

            # TEXT_LINE structure matches paragraph line format (textElements only)
            result = {
                "type": "TEXT_LINE",
                "position": (
                    FindRequest._position_to_dict(obj.position)
                    if obj.position
                    else None
                ),
                "textElements": [text_element],
            }

            # Only include top-level font/color if they are not None
            if obj.font:
                result["font"] = _font_to_dict(obj.font)
            if obj.color:
                result["color"] = _color_to_dict(obj.color)

            return result
        else:
            raise ValueError(f"Unsupported object type: {type(obj)}")

    def _segment_to_dict(self, segment: "PathSegment") -> dict:
        """Convert a PathSegment (Line or Bezier) to dictionary for JSON serialization."""
        from .models import Bezier, Line

        result = {}

        # Add common PathSegment properties
        if segment.stroke_color:
            result["strokeColor"] = {
                "red": segment.stroke_color.r,
                "green": segment.stroke_color.g,
                "blue": segment.stroke_color.b,
                "alpha": segment.stroke_color.a,
            }

        if segment.fill_color:
            result["fillColor"] = {
                "red": segment.fill_color.r,
                "green": segment.fill_color.g,
                "blue": segment.fill_color.b,
                "alpha": segment.fill_color.a,
            }

        if segment.stroke_width is not None:
            result["strokeWidth"] = segment.stroke_width

        if segment.dash_array:
            result["dashArray"] = segment.dash_array

        if segment.dash_phase is not None:
            result["dashPhase"] = segment.dash_phase

        # Add segment-specific properties
        if isinstance(segment, Line):
            result["type"] = "LINE"
            result["segmentType"] = "LINE"
            if segment.p0:
                result["p0"] = {"x": segment.p0.x, "y": segment.p0.y}
            if segment.p1:
                result["p1"] = {"x": segment.p1.x, "y": segment.p1.y}

        elif isinstance(segment, Bezier):
            result["type"] = "BEZIER"
            result["segmentType"] = "BEZIER"
            if segment.p0:
                result["p0"] = {"x": segment.p0.x, "y": segment.p0.y}
            if segment.p1:
                result["p1"] = {"x": segment.p1.x, "y": segment.p1.y}
            if segment.p2:
                result["p2"] = {"x": segment.p2.x, "y": segment.p2.y}
            if segment.p3:
                result["p3"] = {"x": segment.p3.x, "y": segment.p3.y}

        return result


@dataclass
class ModifyRequest:
    """Request to replace an object with a new one of possibly different type.

    Parameters:
    - object_ref: The existing object to replace.
    - new_object: The replacement object (e.g. `Paragraph`, `Image`, or `Path`).

    Example:
    ```python
    new_para = Paragraph(position=old.position, text_lines=["Updated text"])
    req = ModifyRequest(object_ref=old, new_object=new_para)
    payload = req.to_dict()
    ```
    """

    object_ref: ObjectRef
    new_object: Any

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        # Use ObjectRef.to_dict() to ensure proper type normalization
        return {
            "ref": self.object_ref.to_dict(),
            "newObject": AddRequest(None)._object_to_dict(self.new_object),
        }


@dataclass
class ModifyTextRequest:
    """Request to change the text content of a text object.

    Parameters:
    - object_ref: The text object to modify (e.g. a `TextObjectRef`).
    - new_text: Replacement text content.

    Example:
    ```python
    req = ModifyTextRequest(object_ref=text_ref, new_text="Hello world")
    payload = req.to_dict()
    ```
    """

    object_ref: ObjectRef
    new_text: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        # Use ObjectRef.to_dict() to ensure proper type normalization
        return {"ref": self.object_ref.to_dict(), "newTextLine": self.new_text}


@dataclass
class ChangeFormFieldRequest:
    """Request to set a form field's value.

    Parameters:
    - object_ref: A `FormFieldRef` (or generic `ObjectRef`) identifying the field.
    - value: The new value as a string. For checkboxes/radio buttons, use the
      appropriate on/off/selection string per the document's field options.

    Example:
    ```python
    req = ChangeFormFieldRequest(object_ref=field_ref, value="Jane Doe")
    payload = req.to_dict()
    ```
    """

    object_ref: ObjectRef
    value: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        # Use ObjectRef.to_dict() to ensure proper type normalization
        return {"ref": self.object_ref.to_dict(), "value": self.value}


@dataclass
class FormFieldRef(ObjectRef):
    """
    Reference to a form field object with name and value.

    Parameters (usually provided by the server):
    - internal_id: Identifier of the form field object.
    - position: Position of the field.
    - type: One of `ObjectType.TEXT_FIELD`, `ObjectType.CHECK_BOX`, etc.
    - name: Field name (as defined inside the PDF).
    - value: Current field value (string representation).

    Usage:
    - You can pass a `FormFieldRef` to `ChangeFormFieldRequest` to update its value.
    ```python
    payload = ChangeFormFieldRequest(object_ref=field_ref, value="john@doe.com").to_dict()
    ```
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
    font_type: "FontType"
    similarity_score: float

    def get_font_name(self) -> str:
        """Get the recommended font name."""
        return self.font_name

    def get_font_type(self) -> "FontType":
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
    Represents a text object with additional properties and optional hierarchy.

    Parameters (typically provided by the server):
    - internal_id: Identifier of the text object.
    - position: Position of the text object.
    - object_type: `ObjectType.TEXT_LINE` or another text-related type.
    - text: Text content, when available.
    - font_name: Name of the font used for the text.
    - font_size: Size of the font in points.
    - line_spacings: Optional list of line spacing values for multi-line objects.
    - color: Text color.
    - status: `TextStatus` providing modification/encoding info.

    Usage:
    - Instances are returned by find/snapshot APIs. You generally should not instantiate
      them manually, but you may read their properties or pass their `ObjectRef`-like
      identity to modification requests (e.g., `ModifyTextRequest`).
    """

    def __init__(
        self,
        internal_id: str,
        position: Position,
        object_type: ObjectType,
        text: Optional[str] = None,
        font_name: Optional[str] = None,
        font_size: Optional[float] = None,
        line_spacings: Optional[List[float]] = None,
        color: Optional[Color] = None,
        status: Optional[TextStatus] = None,
    ):
        super().__init__(internal_id, position, object_type)
        self.text = text
        self.font_name = font_name
        self.font_size = font_size
        self.line_spacings = line_spacings
        self.color = color
        self.status = status
        self.children: List["TextObjectRef"] = []

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

    def get_children(self) -> List["TextObjectRef"]:
        """Get the child text objects."""
        return self.children

    def get_status(self) -> Optional[TextStatus]:
        """Get the status information."""
        return self.status


@dataclass
class PageRef(ObjectRef):
    """
    Reference to a page with size and orientation metadata.

    Parameters (usually provided by the server):
    - internal_id: Identifier of the page object.
    - position: Position referencing the page (often via `Position.at_page(page_number)`).
    - type: Should be `ObjectType.PAGE`.
    - page_size: `PageSize` of the page.
    - orientation: `Orientation.PORTRAIT` or `Orientation.LANDSCAPE`.

    Usage:
    - Returned inside `PageSnapshot` objects. You can inspect page size/orientation
      and use the page number for subsequent operations.
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
    Outcome returned by certain API endpoints.

    Parameters:
    - command_name: Name of the executed command on the server.
    - element_id: Optional related element ID (when applicable).
    - message: Informational message or error description.
    - success: Whether the command succeeded.
    - warning: Optional warning details.

    Example:
    ```python
    # Parse from a server JSON response dict
    result = CommandResult.from_dict(resp_json)
    if not result.success:
        print("Operation failed:", result.message)
    ```
    """

    command_name: str
    element_id: str | None
    message: str | None
    success: bool
    warning: str | None

    @classmethod
    def from_dict(cls, data: dict) -> "CommandResult":
        """Create a CommandResult from a dictionary response."""
        return cls(
            command_name=data.get("commandName", ""),
            element_id=data.get("elementId", ""),
            message=data.get("message", ""),
            success=data.get("success", False),
            warning=data.get("warning", ""),
        )

    @classmethod
    def empty(cls, command_name: str, element_id: str | None) -> "CommandResult":
        return CommandResult(
            command_name=command_name,
            element_id=element_id,
            message=None,
            success=True,
            warning=None,
        )


@dataclass
class PageSnapshot:
    """
    Snapshot of a single page containing all elements and page metadata.

    Parameters (provided by the server):
    - page_ref: `PageRef` describing the page (size, orientation, etc.).
    - elements: List of `ObjectRef` (and subclasses) present on the page.

    Usage:
    - Iterate over `elements` to find items to modify or move.
    - Use `page_ref.position.page_number` as the page number for follow-up operations.
    """

    page_ref: PageRef
    elements: List[ObjectRef]

    def get_page_ref(self) -> PageRef:
        """Get the page reference."""
        return self.page_ref

    def get_elements(self) -> List[ObjectRef]:
        """Get the list of elements on this page."""
        return self.elements


@dataclass
class DocumentSnapshot:
    """
    Snapshot of a document including pages and fonts used.

    Parameters (provided by the server):
    - page_count: Number of pages in the document.
    - fonts: List of `FontRecommendation` entries summarizing fonts in the document.
    - pages: Ordered list of `PageSnapshot` objects, one per page.

    Usage:
    ```python
    # Iterate pages and elements
    for page in snapshot.pages:
        for el in page.elements:
            if isinstance(el, TextObjectRef) and el.get_text():
                print(el.get_text())
    ```
    """

    page_count: int
    fonts: List[FontRecommendation]
    pages: List[PageSnapshot]

    def get_page_count(self) -> int:
        """Get the total number of pages."""
        return self.page_count

    def get_fonts(self) -> List[FontRecommendation]:
        """Get the list of fonts used in the document."""
        return self.fonts

    def get_pages(self) -> List[PageSnapshot]:
        """Get the list of page snapshots."""
        return self.pages
