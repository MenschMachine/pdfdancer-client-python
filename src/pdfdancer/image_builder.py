from pathlib import Path

from pdfdancer import ValidationException, Image, Position


class ImageBuilder:

    def __init__(self, client: 'PDFDancer'):
        """
        Initialize the image builder with a client reference.

        Args:
            client: The PDFDancer instance for font registration
        """
        if client is None:
            raise ValidationException("Client cannot be null")

        self._client = client
        self._image = Image()

    def from_file(self, img_path: Path) -> 'ImageBuilder':
        self._image.data = img_path.read_bytes()
        return self

    def at(self, page, x, y) -> 'ImageBuilder':
        self._image.position = Position.at_page_coordinates(page, x, y)
        return self

    def add(self) -> bool:
        return self._client._add_image(self._image, self._image.position)
