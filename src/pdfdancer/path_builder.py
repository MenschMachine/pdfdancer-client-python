"""
PathBuilder for the PDFDancer Python client.
Provides fluent interface for constructing vector paths with lines and curves.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .exceptions import ValidationException
from .models import Bezier, Color, Line, Path, PathSegment, Point, Position

if TYPE_CHECKING:
    from .pdfdancer_v1 import PDFDancer


class PathBuilder:
    """
    Builder class for constructing Path objects with fluent interface.
    Allows building complex vector paths from multiple line and bezier segments.
    All coordinates are absolute page coordinates.
    """

    def __init__(self, client: "PDFDancer", page_number: int):
        """
        Initialize the path builder with a client reference and page number.

        Args:
            client: The PDFDancer instance for adding the path
            page_number: The page number (1-indexed)
        """
        if client is None:
            raise ValidationException("Client cannot be null")

        self._client = client
        self._page_number = page_number
        self._segments: List[PathSegment] = []
        self._even_odd_fill: bool = False
        self._current_stroke_color: Optional[Color] = Color(0, 0, 0)  # Black default
        self._current_fill_color: Optional[Color] = None
        self._current_stroke_width: float = 1.0
        self._current_dash_array: Optional[List[float]] = None
        self._current_dash_phase: Optional[float] = None

    def stroke_color(self, color: Color) -> "PathBuilder":
        """
        Set the stroke color for subsequent segments.

        Args:
            color: The stroke color

        Returns:
            Self for method chaining
        """
        self._current_stroke_color = color
        return self

    def fill_color(self, color: Color) -> "PathBuilder":
        """
        Set the fill color for subsequent segments.

        Args:
            color: The fill color

        Returns:
            Self for method chaining
        """
        self._current_fill_color = color
        return self

    def stroke_width(self, width: float) -> "PathBuilder":
        """
        Set the stroke width for subsequent segments.

        Args:
            width: The stroke width in points

        Returns:
            Self for method chaining
        """
        if width <= 0:
            raise ValidationException("Stroke width must be positive")
        self._current_stroke_width = width
        return self

    def dash_pattern(
        self, dash_array: List[float], dash_phase: float = 0.0
    ) -> "PathBuilder":
        """
        Set a dash pattern for subsequent segments.

        Args:
            dash_array: List of on/off lengths (e.g., [10, 5] = 10pt on, 5pt off)
            dash_phase: Offset into the pattern

        Returns:
            Self for method chaining
        """
        self._current_dash_array = dash_array
        self._current_dash_phase = dash_phase
        return self

    def solid(self) -> "PathBuilder":
        """
        Set segments to solid (no dash pattern).

        Returns:
            Self for method chaining
        """
        self._current_dash_array = None
        self._current_dash_phase = None
        return self

    def add_line(self, p0: Point, p1: Point) -> "PathBuilder":
        """
        Add a straight line segment to the path.

        Args:
            p0: Starting point
            p1: Ending point

        Returns:
            Self for method chaining
        """
        line = Line(
            p0=p0,
            p1=p1,
            stroke_color=self._current_stroke_color,
            fill_color=self._current_fill_color,
            stroke_width=self._current_stroke_width,
            dash_array=self._current_dash_array,
            dash_phase=self._current_dash_phase,
        )
        self._segments.append(line)
        return self

    def add_bezier(self, p0: Point, p1: Point, p2: Point, p3: Point) -> "PathBuilder":
        """
        Add a cubic Bezier curve segment to the path.

        Args:
            p0: Starting point
            p1: First control point
            p2: Second control point
            p3: Ending point

        Returns:
            Self for method chaining
        """
        bezier = Bezier(
            p0=p0,
            p1=p1,
            p2=p2,
            p3=p3,
            stroke_color=self._current_stroke_color,
            fill_color=self._current_fill_color,
            stroke_width=self._current_stroke_width,
            dash_array=self._current_dash_array,
            dash_phase=self._current_dash_phase,
        )
        self._segments.append(bezier)
        return self

    def add_rectangle(
        self, x: float, y: float, width: float, height: float
    ) -> "PathBuilder":
        """
        Convenient method to add a rectangle as four line segments to the path.

        Args:
            x: X coordinate of bottom-left corner
            y: Y coordinate of bottom-left corner
            width: Rectangle width
            height: Rectangle height

        Returns:
            Self for method chaining
        """
        if width <= 0:
            raise ValidationException("Rectangle width must be positive")
        if height <= 0:
            raise ValidationException("Rectangle height must be positive")

        # Create rectangle as 4 line segments (clockwise from bottom-left)
        bottom_left = Point(x, y)
        bottom_right = Point(x + width, y)
        top_right = Point(x + width, y + height)
        top_left = Point(x, y + height)

        # Add four lines forming the rectangle
        self.add_line(bottom_left, bottom_right)
        self.add_line(bottom_right, top_right)
        self.add_line(top_right, top_left)
        self.add_line(top_left, bottom_left)

        return self

    def even_odd_fill(self, enabled: bool = True) -> "PathBuilder":
        """
        Set the fill rule to even-odd (vs nonzero winding).

        Args:
            enabled: True for even-odd, False for nonzero winding

        Returns:
            Self for method chaining
        """
        self._even_odd_fill = enabled
        return self

    def add(self) -> bool:
        """
        Build the path and add it to the PDF document.

        Returns:
            True if successful

        Raises:
            ValidationException: If required properties are missing
        """
        if not self._segments:
            raise ValidationException("Path must have at least one segment")

        # Create position with only page index set
        position = Position.at_page_coordinates(self._page_number, 0, 0)

        # Build the Path object
        path = Path(
            position=position,
            path_segments=self._segments,
            even_odd_fill=self._even_odd_fill,
        )

        # Add it using the client's internal method
        # noinspection PyProtectedMember
        return self._client._add_path(path)


class LineBuilder:
    """
    Builder class for constructing Line objects with fluent interface.
    Mirrors the Java client LineBuilder API.
    """

    def __init__(self, client: "PDFDancer", page_number: int):
        """
        Initialize the line builder.

        Args:
            client: The PDFDancer instance for adding the line
            page_number: The page number (1-indexed)
        """
        if client is None:
            raise ValidationException("Client cannot be null")

        self._client = client
        self._page_number = page_number
        self._p0: Optional[Point] = None
        self._p1: Optional[Point] = None
        self._stroke_color: Optional[Color] = Color(0, 0, 0)  # Black default
        self._fill_color: Optional[Color] = None
        self._stroke_width: float = 1.0
        self._dash_array: Optional[List[float]] = None
        self._dash_phase: Optional[float] = None

    def from_point(self, x: float, y: float) -> "LineBuilder":
        """
        Set the starting point of the line (absolute page coordinates).

        Args:
            x: X coordinate on the page
            y: Y coordinate on the page

        Returns:
            Self for method chaining
        """
        self._p0 = Point(x, y)
        return self

    def to_point(self, x: float, y: float) -> "LineBuilder":
        """
        Set the ending point of the line (absolute page coordinates).

        Args:
            x: X coordinate on the page
            y: Y coordinate on the page

        Returns:
            Self for method chaining
        """
        self._p1 = Point(x, y)
        return self

    def stroke_color(self, color: Color) -> "LineBuilder":
        """
        Set the stroke color.

        Args:
            color: The stroke color

        Returns:
            Self for method chaining
        """
        self._stroke_color = color
        return self

    def fill_color(self, color: Color) -> "LineBuilder":
        """
        Set the fill color.

        Args:
            color: The fill color

        Returns:
            Self for method chaining
        """
        self._fill_color = color
        return self

    def stroke_width(self, width: float) -> "LineBuilder":
        """
        Set the stroke width.

        Args:
            width: The stroke width in points

        Returns:
            Self for method chaining
        """
        if width <= 0:
            raise ValidationException("Stroke width must be positive")
        self._stroke_width = width
        return self

    def dash_pattern(
        self, dash_array: List[float], dash_phase: float = 0.0
    ) -> "LineBuilder":
        """
        Set a dash pattern.

        Args:
            dash_array: List of on/off lengths (e.g., [10, 5] = 10pt on, 5pt off)
            dash_phase: Offset into the pattern

        Returns:
            Self for method chaining
        """
        self._dash_array = dash_array
        self._dash_phase = dash_phase
        return self

    def solid(self) -> "LineBuilder":
        """
        Set line to solid (no dash pattern).

        Returns:
            Self for method chaining
        """
        self._dash_array = None
        self._dash_phase = None
        return self

    def add(self) -> bool:
        """
        Build the line and add it to the PDF document.

        Returns:
            True if successful

        Raises:
            ValidationException: If required properties are missing
        """
        if self._p0 is None:
            raise ValidationException("Line start point must be set using from_point()")
        if self._p1 is None:
            raise ValidationException("Line end point must be set using to_point()")

        # Build the Line object
        line = Line(
            p0=self._p0,
            p1=self._p1,
            stroke_color=self._stroke_color,
            fill_color=self._fill_color,
            stroke_width=self._stroke_width,
            dash_array=self._dash_array,
            dash_phase=self._dash_phase,
        )

        # Create position with only page index set
        position = Position.at_page_coordinates(self._page_number, 0, 0)

        # Wrap in Path with single segment
        path = Path(position=position, path_segments=[line], even_odd_fill=False)

        # Add it using the client's internal method
        # noinspection PyProtectedMember
        return self._client._add_path(path)


class BezierBuilder:
    """
    Builder class for constructing Bezier curve objects with fluent interface.
    Mirrors the Java client BezierBuilder API.
    """

    def __init__(self, client: "PDFDancer", page_number: int):
        """
        Initialize the bezier builder.

        Args:
            client: The PDFDancer instance for adding the bezier
            page_number: The page number (1-indexed)
        """
        if client is None:
            raise ValidationException("Client cannot be null")

        self._client = client
        self._page_number = page_number
        self._p0: Optional[Point] = None
        self._p1: Optional[Point] = None
        self._p2: Optional[Point] = None
        self._p3: Optional[Point] = None
        self._stroke_color: Optional[Color] = Color(0, 0, 0)  # Black default
        self._fill_color: Optional[Color] = None
        self._stroke_width: float = 1.0
        self._dash_array: Optional[List[float]] = None
        self._dash_phase: Optional[float] = None

    def from_point(self, x: float, y: float) -> "BezierBuilder":
        """
        Set the starting point of the curve (absolute page coordinates).

        Args:
            x: X coordinate on the page
            y: Y coordinate on the page

        Returns:
            Self for method chaining
        """
        self._p0 = Point(x, y)
        return self

    def control_point_1(self, x: float, y: float) -> "BezierBuilder":
        """
        Set the first control point (absolute page coordinates).

        Args:
            x: X coordinate on the page
            y: Y coordinate on the page

        Returns:
            Self for method chaining
        """
        self._p1 = Point(x, y)
        return self

    def control_point_2(self, x: float, y: float) -> "BezierBuilder":
        """
        Set the second control point (absolute page coordinates).

        Args:
            x: X coordinate on the page
            y: Y coordinate on the page

        Returns:
            Self for method chaining
        """
        self._p2 = Point(x, y)
        return self

    def to_point(self, x: float, y: float) -> "BezierBuilder":
        """
        Set the ending point of the curve (absolute page coordinates).

        Args:
            x: X coordinate on the page
            y: Y coordinate on the page

        Returns:
            Self for method chaining
        """
        self._p3 = Point(x, y)
        return self

    def stroke_color(self, color: Color) -> "BezierBuilder":
        """
        Set the stroke color.

        Args:
            color: The stroke color

        Returns:
            Self for method chaining
        """
        self._stroke_color = color
        return self

    def fill_color(self, color: Color) -> "BezierBuilder":
        """
        Set the fill color.

        Args:
            color: The fill color

        Returns:
            Self for method chaining
        """
        self._fill_color = color
        return self

    def stroke_width(self, width: float) -> "BezierBuilder":
        """
        Set the stroke width.

        Args:
            width: The stroke width in points

        Returns:
            Self for method chaining
        """
        if width <= 0:
            raise ValidationException("Stroke width must be positive")
        self._stroke_width = width
        return self

    def dash_pattern(
        self, dash_array: List[float], dash_phase: float = 0.0
    ) -> "BezierBuilder":
        """
        Set a dash pattern.

        Args:
            dash_array: List of on/off lengths (e.g., [10, 5] = 10pt on, 5pt off)
            dash_phase: Offset into the pattern

        Returns:
            Self for method chaining
        """
        self._dash_array = dash_array
        self._dash_phase = dash_phase
        return self

    def solid(self) -> "BezierBuilder":
        """
        Set curve to solid (no dash pattern).

        Returns:
            Self for method chaining
        """
        self._dash_array = None
        self._dash_phase = None
        return self

    def add(self) -> bool:
        """
        Build the bezier curve and add it to the PDF document.

        Returns:
            True if successful

        Raises:
            ValidationException: If required properties are missing
        """
        if self._p0 is None:
            raise ValidationException(
                "Bezier start point must be set using from_point()"
            )
        if self._p1 is None:
            raise ValidationException(
                "Bezier first control point must be set using control_point_1()"
            )
        if self._p2 is None:
            raise ValidationException(
                "Bezier second control point must be set using control_point_2()"
            )
        if self._p3 is None:
            raise ValidationException("Bezier end point must be set using to_point()")

        # Build the Bezier object
        bezier = Bezier(
            p0=self._p0,
            p1=self._p1,
            p2=self._p2,
            p3=self._p3,
            stroke_color=self._stroke_color,
            fill_color=self._fill_color,
            stroke_width=self._stroke_width,
            dash_array=self._dash_array,
            dash_phase=self._dash_phase,
        )

        # Create position with only page index set
        position = Position.at_page_coordinates(self._page_number, 0, 0)

        # Wrap in Path with single segment
        path = Path(position=position, path_segments=[bezier], even_odd_fill=False)

        # Add it using the client's internal method
        # noinspection PyProtectedMember
        return self._client._add_path(path)


class RectangleBuilder:
    """
    Builder class for constructing Rectangle objects with fluent interface.
    Provides a convenient way to create a rectangle path with a single builder.
    """

    def __init__(self, client: "PDFDancer", page_number: int):
        """
        Initialize the rectangle builder.

        Args:
            client: The PDFDancer instance for adding the rectangle
            page_number: The page number (1-indexed)
        """
        if client is None:
            raise ValidationException("Client cannot be null")

        self._client = client
        self._page_number = page_number
        self._x: Optional[float] = None
        self._y: Optional[float] = None
        self._width: Optional[float] = None
        self._height: Optional[float] = None
        self._stroke_color: Optional[Color] = Color(0, 0, 0)  # Black default
        self._fill_color: Optional[Color] = None
        self._stroke_width: float = 1.0
        self._dash_array: Optional[List[float]] = None
        self._dash_phase: Optional[float] = None
        self._even_odd_fill: bool = False

    def at_coordinates(self, x: float, y: float) -> "RectangleBuilder":
        """
        Set the bottom-left corner position of the rectangle.

        Args:
            x: X coordinate on the page
            y: Y coordinate on the page

        Returns:
            Self for method chaining
        """
        self._x = x
        self._y = y
        return self

    def with_size(self, width: float, height: float) -> "RectangleBuilder":
        """
        Set the dimensions of the rectangle.

        Args:
            width: Rectangle width
            height: Rectangle height

        Returns:
            Self for method chaining
        """
        self._width = width
        self._height = height
        return self

    def stroke_color(self, color: Color) -> "RectangleBuilder":
        """
        Set the stroke color.

        Args:
            color: The stroke color

        Returns:
            Self for method chaining
        """
        self._stroke_color = color
        return self

    def fill_color(self, color: Color) -> "RectangleBuilder":
        """
        Set the fill color.

        Args:
            color: The fill color

        Returns:
            Self for method chaining
        """
        self._fill_color = color
        return self

    def stroke_width(self, width: float) -> "RectangleBuilder":
        """
        Set the stroke width.

        Args:
            width: The stroke width in points

        Returns:
            Self for method chaining
        """
        if width <= 0:
            raise ValidationException("Stroke width must be positive")
        self._stroke_width = width
        return self

    def dash_pattern(
        self, dash_array: List[float], dash_phase: float = 0.0
    ) -> "RectangleBuilder":
        """
        Set a dash pattern.

        Args:
            dash_array: List of on/off lengths (e.g., [10, 5] = 10pt on, 5pt off)
            dash_phase: Offset into the pattern

        Returns:
            Self for method chaining
        """
        self._dash_array = dash_array
        self._dash_phase = dash_phase
        return self

    def solid(self) -> "RectangleBuilder":
        """
        Set rectangle to solid (no dash pattern).

        Returns:
            Self for method chaining
        """
        self._dash_array = None
        self._dash_phase = None
        return self

    def even_odd_fill(self, enabled: bool = True) -> "RectangleBuilder":
        """
        Set the fill rule to even-odd (vs nonzero winding).

        Args:
            enabled: True for even-odd, False for nonzero winding

        Returns:
            Self for method chaining
        """
        self._even_odd_fill = enabled
        return self

    def add(self) -> bool:
        """
        Build the rectangle and add it to the PDF document.

        Returns:
            True if successful

        Raises:
            ValidationException: If required properties are missing
        """
        if self._x is None or self._y is None:
            raise ValidationException(
                "Rectangle position must be set using at_coordinates()"
            )
        if self._width is None or self._height is None:
            raise ValidationException(
                "Rectangle dimensions must be set using with_size()"
            )
        if self._width <= 0:
            raise ValidationException("Rectangle width must be positive")
        if self._height <= 0:
            raise ValidationException("Rectangle height must be positive")

        # Create rectangle as 4 line segments
        bottom_left = Point(self._x, self._y)
        bottom_right = Point(self._x + self._width, self._y)
        top_right = Point(self._x + self._width, self._y + self._height)
        top_left = Point(self._x, self._y + self._height)

        # Create four lines forming the rectangle
        lines = [
            Line(
                p0=bottom_left,
                p1=bottom_right,
                stroke_color=self._stroke_color,
                fill_color=self._fill_color,
                stroke_width=self._stroke_width,
                dash_array=self._dash_array,
                dash_phase=self._dash_phase,
            ),
            Line(
                p0=bottom_right,
                p1=top_right,
                stroke_color=self._stroke_color,
                fill_color=self._fill_color,
                stroke_width=self._stroke_width,
                dash_array=self._dash_array,
                dash_phase=self._dash_phase,
            ),
            Line(
                p0=top_right,
                p1=top_left,
                stroke_color=self._stroke_color,
                fill_color=self._fill_color,
                stroke_width=self._stroke_width,
                dash_array=self._dash_array,
                dash_phase=self._dash_phase,
            ),
            Line(
                p0=top_left,
                p1=bottom_left,
                stroke_color=self._stroke_color,
                fill_color=self._fill_color,
                stroke_width=self._stroke_width,
                dash_array=self._dash_array,
                dash_phase=self._dash_phase,
            ),
        ]

        # Create position with only page index set
        position = Position.at_page_coordinates(self._page_number, 0, 0)

        # Wrap in Path with four line segments
        path = Path(
            position=position, path_segments=lines, even_odd_fill=self._even_odd_fill
        )

        # Add it using the client's internal method
        # noinspection PyProtectedMember
        return self._client._add_path(path)
