from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .exceptions import ValidationException
from .models import AddPageRequest, Orientation, PageRef, PageSize

if TYPE_CHECKING:
    from .pdfdancer_v1 import PDFDancer


class PageBuilder:
    """
    Fluent builder for adding pages with optional orientation, size, and index.

    Usage:
        pdf.new_page().at_index(1).landscape().a4().add()
    """

    def __init__(self, client: "PDFDancer") -> None:
        if client is None:
            raise ValidationException("Client cannot be null")

        self._client = client
        self._page_index: Optional[int] = None
        self._orientation: Optional[Orientation] = None
        self._page_size: Optional[PageSize] = None

    def at_index(self, page_index: int) -> "PageBuilder":
        if page_index is None:
            raise ValidationException("Page index cannot be null")
        if page_index < 0:
            raise ValidationException("Page index must be greater than or equal to 0")
        self._page_index = int(page_index)
        return self

    def orientation(self, orientation: Orientation) -> "PageBuilder":
        if orientation is None:
            raise ValidationException("Orientation cannot be null")
        if isinstance(orientation, str):
            normalized = orientation.strip().upper()
            orientation = Orientation(normalized)
        self._orientation = orientation
        return self

    def portrait(self) -> "PageBuilder":
        self._orientation = Orientation.PORTRAIT
        return self

    def landscape(self) -> "PageBuilder":
        self._orientation = Orientation.LANDSCAPE
        return self

    def page_size(self, page_size: PageSize) -> "PageBuilder":
        if page_size is None:
            raise ValidationException("Page size cannot be null")
        self._page_size = PageSize.coerce(page_size)
        return self

    def a4(self) -> "PageBuilder":
        self._page_size = PageSize.A4
        return self

    def letter(self) -> "PageBuilder":
        self._page_size = PageSize.LETTER
        return self

    def a3(self) -> "PageBuilder":
        self._page_size = PageSize.A3
        return self

    def a5(self) -> "PageBuilder":
        self._page_size = PageSize.A5
        return self

    def legal(self) -> "PageBuilder":
        self._page_size = PageSize.LEGAL
        return self

    def custom_size(self, width: float, height: float) -> "PageBuilder":
        self._page_size = PageSize(name=None, width=width, height=height)
        return self

    def add(self) -> PageRef:
        request = self._build_request()
        return self._client._add_page(request)

    def _build_request(self) -> Optional[AddPageRequest]:
        if (
            self._page_index is None
            and self._orientation is None
            and self._page_size is None
        ):
            return None
        return AddPageRequest(
            page_index=self._page_index,
            orientation=self._orientation,
            page_size=self._page_size,
        )
