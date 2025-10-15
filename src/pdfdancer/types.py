from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import ObjectType, Position, ObjectRef
from .exceptions import HttpClientException


@dataclass
class BoundingRect:
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None


class PathObject:
    """
    Represents a vector path object inside a PDF page.
    Provides high-level methods for inspecting, moving, and deleting paths.

    Instances are created internally by PDFDancer selectors (e.g. pdf.select_paths()).
    """

    def __init__(self, client: 'PDFDancer', internal_id: str, object_type: ObjectType, position: Position):
        self._client = client
        self.position = position
        self.internal_id = internal_id
        self.object_type = object_type

    # --------------------------------------------------------------
    # Core properties
    # --------------------------------------------------------------
    def internal_id(self) -> str:
        """Internal PDFDancer object identifier, e.g. 'PATH_000023'."""
        return self.internal_id

    def type(self) -> ObjectType:
        """Enum value representing the PDF object type."""
        return self.object_type

    def position(self) -> Position:
        """The geometric position of the path on its page."""
        return self.position

    @property
    def page_index(self) -> int:
        """Page index where this path resides."""
        return self.position.page_index

    @property
    def bounding_box(self) -> Optional[BoundingRect]:
        """Optional bounding rectangle (if available)."""
        return self.position.bounding_rect

    def delete(self) -> bool:
        """Delete this path from the PDF document."""
        return self._client.delete(ObjectRef(self.internal_id, self.position, self.object_type))

    def move_to(self, x: float, y: float) -> bool:
        """Delete this path from the PDF document."""
        return self._client.move(ObjectRef(self.internal_id, self.position, self.object_type),
                                 Position.at_page_coordinates(self.position.page_index, x, y))

    # --------------------------------------------------------------
    # Representation helpers
    # --------------------------------------------------------------
    def __repr__(self) -> str:
        return f"<PathObject id={self.internal_id} page={self.page_index}>"

