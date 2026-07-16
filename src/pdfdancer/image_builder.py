from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pdfdancer import Image, Position, ValidationException

if TYPE_CHECKING:
    from .pdfdancer_v1 import PDFDancer


class ImageBuilder:

    def __init__(self, client: "PDFDancer"):
        """
        Initialize the image builder with a client reference.

        Args:
            client: The PDFDancer instance for font registration
        """
        if client is None:
            raise ValidationException("Client cannot be null")

        self._client = client
        self._image = Image()

    def from_file(self, img_path: Path) -> "ImageBuilder":
        img_path = Path(img_path)
        if not img_path.is_file():
            raise ValidationException(f"Image file not found: {img_path}")
        self._image.data = img_path.read_bytes()
        if not self._image.data:
            raise ValidationException("Image file cannot be empty")
        self._image.format = img_path.suffix.lstrip(".").upper() or None
        return self

    def at(self, page, x, y) -> "ImageBuilder":
        self._image.position = Position.at_page_coordinates(page, x, y)
        return self

    def add(self) -> bool:
        if self._image.data is None:
            raise ValidationException("Call from_file() before add()")
        if self._image.position is None:
            raise ValidationException("Call at() before add()")
        # noinspection PyProtectedMember
        return self._client._add_image(self._image, self._image.position)


class ImageOnPageBuilder:

    def __init__(self, client: "PDFDancer", page_number: int):
        """
        Initialize the image builder with a client reference.

        Args:
            client: The PDFDancer instance for font registration
        """
        if client is None:
            raise ValidationException("Client cannot be null")

        self._client = client
        self._image = Image()
        self._page_number = page_number

    def from_file(self, img_path: Path) -> "ImageOnPageBuilder":
        img_path = Path(img_path)
        if not img_path.is_file():
            raise ValidationException(f"Image file not found: {img_path}")
        self._image.data = img_path.read_bytes()
        if not self._image.data:
            raise ValidationException("Image file cannot be empty")
        self._image.format = img_path.suffix.lstrip(".").upper() or None
        return self

    def at(self, x, y) -> "ImageOnPageBuilder":
        self._image.position = Position.at_page_coordinates(self._page_number, x, y)
        return self

    def add(self) -> bool:
        if self._image.data is None:
            raise ValidationException("Call from_file() before add()")
        if self._image.position is None:
            raise ValidationException("Call at() before add()")
        # noinspection PyProtectedMember
        return self._client._add_image(self._image, self._image.position)
