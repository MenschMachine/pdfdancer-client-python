"""Selector-based text editing models for the PDFDancer v2 API.

The public builders mirror the Java SDK while using Python ``snake_case`` names.
Every request validates before serialization and omits fields whose value is
``None``, matching Jackson's ``NON_NULL`` serialization in the Java client.
"""

from __future__ import annotations

import base64
import math
import warnings
from dataclasses import dataclass, replace
from enum import Enum, EnumMeta
from pathlib import Path
from typing import Any, Optional, Sequence, cast

from typing_extensions import Self

from .exceptions import ValidationException


def _require_finite(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValidationException(f"{name} must be finite")
    return result


def _without_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _validated_pages(pages: Optional[Sequence[int]]) -> Optional[tuple[int, ...]]:
    if pages is None:
        return None
    normalized = tuple(pages)
    if any(
        page is None or isinstance(page, bool) or not isinstance(page, int) or page < 1
        for page in normalized
    ):
        raise ValidationException("pages must contain only page numbers >= 1")
    return normalized


class PdfColorSpace(Enum):
    RGB = "rgb"
    CMYK = "cmyk"
    GRAY = "gray"


@dataclass(frozen=True)
class PdfColorRequest:
    space: PdfColorSpace
    components: tuple[float, ...]
    alpha_value: Optional[float] = None

    @classmethod
    def rgb(cls, red: float, green: float, blue: float) -> "PdfColorRequest":
        return cls(PdfColorSpace.RGB, (red, green, blue)).validated()

    @classmethod
    def cmyk(
        cls, cyan: float, magenta: float, yellow: float, black: float
    ) -> "PdfColorRequest":
        return cls(PdfColorSpace.CMYK, (cyan, magenta, yellow, black)).validated()

    @classmethod
    def gray(cls, gray: float) -> "PdfColorRequest":
        return cls(PdfColorSpace.GRAY, (gray,)).validated()

    def alpha(self, alpha: float) -> "PdfColorRequest":
        return replace(self, alpha_value=alpha).validated()

    def validated(self) -> "PdfColorRequest":
        if not isinstance(self.space, PdfColorSpace):
            raise ValidationException("color space must not be null")
        expected = {
            PdfColorSpace.RGB: 3,
            PdfColorSpace.CMYK: 4,
            PdfColorSpace.GRAY: 1,
        }[self.space]
        if len(self.components) != expected:
            raise ValidationException(
                f"color space {self.space.value} requires {expected} components"
            )
        for component in self.components:
            self._validate_normalized(component, "color component")
        if self.alpha_value is not None:
            self._validate_normalized(self.alpha_value, "alpha")
        return self

    @staticmethod
    def _validate_normalized(value: float, name: str) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValidationException(f"{name} must be finite and between 0.0 and 1.0")
        value = float(value)
        if not math.isfinite(value) or value < 0.0 or value > 1.0:
            raise ValidationException(f"{name} must be finite and between 0.0 and 1.0")

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return _without_none(
            {
                "space": self.space.value,
                "components": [float(value) for value in self.components],
                "alpha": self.alpha_value,
            }
        )


@dataclass(frozen=True)
class PdfAffineTransform:
    """Immutable PDF six-number affine transformation ``[a,b,c,d,e,f]``."""

    a: float
    b: float
    c: float
    d: float
    e: float
    f: float

    def __post_init__(self) -> None:
        for coefficient in self.to_pdf_matrix():
            _require_finite(coefficient, "PDF affine matrix coefficient")

    @classmethod
    def from_pdf_matrix(cls, coefficients: Sequence[float]) -> "PdfAffineTransform":
        if coefficients is None or len(coefficients) != 6:
            raise ValidationException(
                "PDF affine matrix must contain exactly 6 coefficients"
            )
        return cls(*(float(value) for value in coefficients))

    @classmethod
    def builder(cls) -> "PdfAffineTransformBuilder":
        return PdfAffineTransformBuilder()

    def to_pdf_matrix(self) -> tuple[float, float, float, float, float, float]:
        return self.a, self.b, self.c, self.d, self.e, self.f

    def _followed_by(
        self, next_transform: "PdfAffineTransform"
    ) -> "PdfAffineTransform":
        return PdfAffineTransform(
            next_transform.a * self.a + next_transform.c * self.b,
            next_transform.b * self.a + next_transform.d * self.b,
            next_transform.a * self.c + next_transform.c * self.d,
            next_transform.b * self.c + next_transform.d * self.d,
            next_transform.a * self.e + next_transform.c * self.f + next_transform.e,
            next_transform.b * self.e + next_transform.d * self.f + next_transform.f,
        )


class PdfAffineTransformBuilder:
    """Build a six-value PDF affine transformation matrix."""

    def __init__(self) -> None:
        self._transform = PdfAffineTransform(1, 0, 0, 1, 0, 0)

    def scale(self, scale_x: float, scale_y: float) -> "PdfAffineTransformBuilder":
        self._transform = self._transform._followed_by(
            PdfAffineTransform(scale_x, 0, 0, scale_y, 0, 0)
        )
        return self

    def shear(self, shear_x: float, shear_y: float) -> "PdfAffineTransformBuilder":
        self._transform = self._transform._followed_by(
            PdfAffineTransform(1, shear_y, shear_x, 1, 0, 0)
        )
        return self

    def rotate_degrees(self, degrees: float) -> "PdfAffineTransformBuilder":
        degrees = _require_finite(degrees, "rotation degrees")
        radians = math.radians(degrees)
        cosine, sine = math.cos(radians), math.sin(radians)
        self._transform = self._transform._followed_by(
            PdfAffineTransform(cosine, sine, -sine, cosine, 0, 0)
        )
        return self

    def translate(
        self, translate_x: float, translate_y: float
    ) -> "PdfAffineTransformBuilder":
        self._transform = self._transform._followed_by(
            PdfAffineTransform(1, 0, 0, 1, translate_x, translate_y)
        )
        return self

    def build(self) -> PdfAffineTransform:
        return self._transform


@dataclass(frozen=True)
class TextSelectorRequest:
    literal: Optional[str] = None
    regex: Optional[str] = None
    case_sensitive: Optional[bool] = None
    whole_words: Optional[bool] = None
    max_matches: Optional[int] = None

    def validated(self) -> "TextSelectorRequest":
        if (self.literal is None) == (self.regex is None):
            raise ValidationException(
                "Exactly one of literal or regex must be provided"
            )
        selected = self.literal if self.literal is not None else self.regex
        if selected is None or not selected.strip():
            name = "literal" if self.literal is not None else "regex"
            raise ValidationException(f"{name} must not be blank")
        if self.max_matches is not None and self.max_matches <= 0:
            raise ValidationException("maxMatches must be positive")
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return _without_none(
            {
                "literal": self.literal,
                "regex": self.regex,
                "caseSensitive": self.case_sensitive,
                "wholeWords": self.whole_words,
                "maxMatches": self.max_matches,
            }
        )


class TextLayoutMode(Enum):
    SOURCE_ANCHORED = "sourceAnchored"
    REFLOW_WHEN_SUPPORTED = "reflowWhenSupported"
    REQUIRE_REFLOW = "requireReflow"


class _TextLayoutProfileMeta(EnumMeta):
    """Keeps the deprecated ``NO_REFLOW`` name working, with a DeprecationWarning."""

    _DEPRECATED = {"NO_REFLOW": "KEEP_LINE_BREAKS"}

    def _warn_deprecated(cls, name: str) -> str:
        replacement = cls._DEPRECATED[name]
        warnings.warn(
            f"TextLayoutProfile.{name} is deprecated; use "
            f"TextLayoutProfile.{replacement} instead",
            DeprecationWarning,
            stacklevel=3,
        )
        return replacement

    def __getattr__(cls, name: str) -> Any:
        if name in cls._DEPRECATED:
            return getattr(cls, cls._warn_deprecated(name))
        parent = getattr(super(), "__getattr__", None)  # only present before 3.12
        if parent is not None:
            return parent(name)
        raise AttributeError(name)

    def __getitem__(cls, name: str) -> Any:
        if name in cls._DEPRECATED:
            name = cls._warn_deprecated(name)
        return super().__getitem__(name)


class TextLayoutProfile(Enum, metaclass=_TextLayoutProfileMeta):
    """Layout profile for a reflow mode.

    ``KEEP_LINE_BREAKS`` keeps every existing line break. Each line is still
    recomposed horizontally: following text shifts along the line to make room,
    nothing wraps onto a new line, and a line may grow beyond its original width.
    It is sent to the API as ``noReflow``.

    ``NO_REFLOW`` is a deprecated alias of ``KEEP_LINE_BREAKS``: its name
    contradicted the ``reflow_when_supported`` and ``require_reflow`` modes it is
    used with. It still works and emits a ``DeprecationWarning``.
    """

    DEFAULT = "default"
    BODY_TEXT = "bodyText"
    KEEP_LINE_BREAKS = "noReflow"


class TextAlignment(Enum):
    """Explicit alignment of each edited line. Valid only for text replace.

    Each edited line keeps its original visible text extent as the reference:
    ``LEFT`` keeps the left edge, ``RIGHT`` keeps the right edge, ``CENTERED``
    keeps the midpoint, and ``JUSTIFIED`` keeps both edges by changing the word
    gaps (the last line of a paragraph stays left-aligned).
    """

    LEFT = "left"
    RIGHT = "right"
    CENTERED = "centered"
    JUSTIFIED = "justified"


@dataclass(frozen=True)
class TextLayoutRequest:
    """Layout policy of a text edit.

    An omitted ``mode`` means ``reflowWhenSupported``, as in the API. That mode
    needs a ``profile``. When ``mode`` and ``profile`` are both omitted, the SDK
    uses the ``KEEP_LINE_BREAKS`` profile.
    """

    mode: Optional[TextLayoutMode] = None
    profile: Optional[TextLayoutProfile] = None
    hyphenation_enabled: Optional[bool] = None
    alignment: Optional[TextAlignment] = None

    @classmethod
    def source_anchored(cls) -> "TextLayoutRequest":
        return cls(mode=TextLayoutMode.SOURCE_ANCHORED)

    @classmethod
    def reflow_when_supported(cls, profile: TextLayoutProfile) -> "TextLayoutRequest":
        return cls(mode=TextLayoutMode.REFLOW_WHEN_SUPPORTED, profile=profile)

    @classmethod
    def require_reflow(cls, profile: TextLayoutProfile) -> "TextLayoutRequest":
        return cls(mode=TextLayoutMode.REQUIRE_REFLOW, profile=profile)

    def with_hyphenation_enabled(self, enabled: bool) -> "TextLayoutRequest":
        return replace(self, hyphenation_enabled=enabled)

    def with_alignment(self, alignment: TextAlignment) -> "TextLayoutRequest":
        """Set the explicit alignment. Valid only for text replace."""
        return replace(self, alignment=alignment)

    def _effective_profile(self) -> Optional[TextLayoutProfile]:
        """Return the profile to send. A layout with no mode and no profile gets ``KEEP_LINE_BREAKS``."""
        if self.profile is None and self.mode is None:
            return TextLayoutProfile.KEEP_LINE_BREAKS
        return self.profile

    def validated(self) -> "TextLayoutRequest":
        # The API treats an omitted mode as reflowWhenSupported.
        mode = self.mode or TextLayoutMode.REFLOW_WHEN_SUPPORTED
        if self.alignment is not None and not isinstance(self.alignment, TextAlignment):
            raise ValidationException("layout.alignment must be a TextAlignment")
        if mode is TextLayoutMode.SOURCE_ANCHORED and self.profile is not None:
            raise ValidationException("sourceAnchored layout must not specify profile")
        if (
            mode is TextLayoutMode.SOURCE_ANCHORED
            and self.hyphenation_enabled is not None
        ):
            raise ValidationException(
                "layout.hyphenationEnabled is not valid when layout.mode is sourceAnchored"
            )
        if mode is TextLayoutMode.SOURCE_ANCHORED and self.alignment is not None:
            raise ValidationException(
                "layout.alignment is not valid when layout.mode is sourceAnchored"
            )
        if (
            mode
            in (
                TextLayoutMode.REFLOW_WHEN_SUPPORTED,
                TextLayoutMode.REQUIRE_REFLOW,
            )
            and self._effective_profile() is None
        ):
            raise ValidationException(
                f"{mode.value} profile must be one of DEFAULT, BODY_TEXT, KEEP_LINE_BREAKS"
            )
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        profile = self._effective_profile()
        return _without_none(
            {
                "mode": self.mode.value if self.mode else None,
                "profile": profile.value if profile else None,
                "hyphenationEnabled": self.hyphenation_enabled,
                "alignment": self.alignment.value if self.alignment else None,
            }
        )


def _reject_alignment(layout: Optional[TextLayoutRequest]) -> None:
    """Reject ``layout.alignment`` on operations other than text replace."""
    if layout is not None and layout.alignment is not None:
        raise ValidationException("layout.alignment is valid only for text replace")


@dataclass(frozen=True)
class TextStyleNumericFilterRequest:
    eq: float
    tolerance: Optional[float] = None

    @classmethod
    def equal_to(
        cls, eq: float, tolerance: Optional[float] = None
    ) -> "TextStyleNumericFilterRequest":
        return cls(eq, tolerance).validated()

    def validated(self) -> "TextStyleNumericFilterRequest":
        _require_finite(self.eq, "eq")
        if self.tolerance is not None:
            _require_finite(self.tolerance, "tolerance")
            if self.tolerance < 0:
                raise ValidationException("tolerance must be >= 0")
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return _without_none({"eq": self.eq, "tolerance": self.tolerance})


@dataclass(frozen=True)
class TextStyleRunFilterRequest:
    text_contains: Optional[str] = None
    font: Optional[str] = None
    size: Optional[TextStyleNumericFilterRequest] = None
    fill_color: Optional[PdfColorRequest] = None
    stroke_color: Optional[PdfColorRequest] = None
    character_spacing: Optional[TextStyleNumericFilterRequest] = None
    word_spacing: Optional[TextStyleNumericFilterRequest] = None
    contains_unmapped_glyphs: Optional[bool] = None

    def validated(self) -> "TextStyleRunFilterRequest":
        if not any(value is not None for value in self.__dict__.values()):
            raise ValidationException("runs.where must set at least one field")
        if self.text_contains is not None and not self.text_contains.strip():
            raise ValidationException("textContains must not be blank")
        if self.font is not None and not self.font.strip():
            raise ValidationException("font must not be blank")
        for numeric_filter in (self.size, self.character_spacing, self.word_spacing):
            if numeric_filter is not None:
                numeric_filter.validated()
        for color in (self.fill_color, self.stroke_color):
            if color is not None:
                color.validated()
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return _without_none(
            {
                "textContains": self.text_contains,
                "font": self.font,
                "size": self.size.to_dict() if self.size else None,
                "fillColor": self.fill_color.to_dict() if self.fill_color else None,
                "strokeColor": (
                    self.stroke_color.to_dict() if self.stroke_color else None
                ),
                "characterSpacing": (
                    self.character_spacing.to_dict() if self.character_spacing else None
                ),
                "wordSpacing": (
                    self.word_spacing.to_dict() if self.word_spacing else None
                ),
                "containsUnmappedGlyphs": self.contains_unmapped_glyphs,
            }
        )


@dataclass(frozen=True)
class TextStyleRunsSelectorRequest:
    where: TextStyleRunFilterRequest
    max_matches: Optional[int] = None

    def validated(self) -> "TextStyleRunsSelectorRequest":
        if self.where is None:
            raise ValidationException("runs.where must not be null")
        self.where.validated()
        if self.max_matches is not None and self.max_matches <= 0:
            raise ValidationException("runs.maxMatches must be positive")
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return _without_none(
            {"where": self.where.to_dict(), "maxMatches": self.max_matches}
        )


@dataclass(frozen=True)
class TextStyleSelectorRequest:
    literal: Optional[str] = None
    regex: Optional[str] = None
    case_sensitive: Optional[bool] = None
    whole_words: Optional[bool] = None
    max_matches: Optional[int] = None
    runs: Optional[TextStyleRunsSelectorRequest] = None

    @classmethod
    def from_text_selector(
        cls, selector: TextSelectorRequest
    ) -> "TextStyleSelectorRequest":
        return cls(
            literal=selector.literal,
            regex=selector.regex,
            case_sensitive=selector.case_sensitive,
            whole_words=selector.whole_words,
            max_matches=selector.max_matches,
        )

    def validated(self) -> "TextStyleSelectorRequest":
        text_selector = self.literal is not None or self.regex is not None
        if text_selector == (self.runs is not None):
            raise ValidationException(
                "Exactly one of literal, regex, or runs must be provided"
            )
        if text_selector:
            TextSelectorRequest(
                self.literal,
                self.regex,
                self.case_sensitive,
                self.whole_words,
                self.max_matches,
            ).validated()
        else:
            assert self.runs is not None
            self.runs.validated()
            if any(
                value is not None
                for value in (
                    self.case_sensitive,
                    self.whole_words,
                    self.max_matches,
                )
            ):
                raise ValidationException(
                    "caseSensitive, wholeWords, and top-level maxMatches are not valid with runs"
                )
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return _without_none(
            {
                "literal": self.literal,
                "regex": self.regex,
                "caseSensitive": self.case_sensitive,
                "wholeWords": self.whole_words,
                "maxMatches": self.max_matches,
                "runs": self.runs.to_dict() if self.runs else None,
            }
        )


@dataclass(frozen=True)
class _TextStyleFields:
    font: Optional[str] = None
    size: Optional[float] = None
    fill_color: Optional[PdfColorRequest] = None
    stroke_color: Optional[PdfColorRequest] = None
    character_spacing: Optional[float] = None
    word_spacing: Optional[float] = None

    def _validate_optional_fields(self) -> None:
        if self.font is not None and not self.font.strip():
            raise ValidationException("font must not be blank")
        if self.size is not None:
            _require_finite(self.size, "size")
            if self.size <= 0:
                raise ValidationException("size must be > 0")
        for name, value in (
            ("characterSpacing", self.character_spacing),
            ("wordSpacing", self.word_spacing),
        ):
            if value is not None:
                _require_finite(value, name)
        for color in (self.fill_color, self.stroke_color):
            if color is not None:
                color.validated()

    def _fields_dict(self) -> dict[str, Any]:
        return _without_none(
            {
                "font": self.font,
                "size": self.size,
                "fillColor": self.fill_color.to_dict() if self.fill_color else None,
                "strokeColor": (
                    self.stroke_color.to_dict() if self.stroke_color else None
                ),
                "characterSpacing": self.character_spacing,
                "wordSpacing": self.word_spacing,
            }
        )


@dataclass(frozen=True)
class TextStylePatchRequest(_TextStyleFields):
    @classmethod
    def builder(cls) -> "TextStylePatchBuilder":
        return TextStylePatchBuilder()

    def validated(self) -> "TextStylePatchRequest":
        if not any(value is not None for value in self.__dict__.values()):
            raise ValidationException("style patch must set at least one field")
        self._validate_optional_fields()
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return self._fields_dict()


@dataclass(frozen=True)
class TextStyleSetRequest(_TextStyleFields):
    reset_spacing_overrides: Optional[bool] = None

    @classmethod
    def builder(cls) -> "TextStyleSetBuilder":
        return TextStyleSetBuilder()

    def validated(self) -> "TextStyleSetRequest":
        self._validate_optional_fields()
        if not any(value is not None for value in self.__dict__.values()):
            raise ValidationException("style must set at least one field")
        if self.reset_spacing_overrides is False:
            raise ValidationException("resetSpacingOverrides must be true when present")
        if self.reset_spacing_overrides is True and (
            self.character_spacing is not None or self.word_spacing is not None
        ):
            raise ValidationException(
                "resetSpacingOverrides cannot be combined with characterSpacing or wordSpacing"
            )
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return _without_none(
            {
                **self._fields_dict(),
                "resetSpacingOverrides": self.reset_spacing_overrides,
            }
        )


class _TextStyleBuilderBase:
    def __init__(self) -> None:
        self._font: Optional[str] = None
        self._size: Optional[float] = None
        self._fill_color: Optional[PdfColorRequest] = None
        self._stroke_color: Optional[PdfColorRequest] = None
        self._character_spacing: Optional[float] = None
        self._word_spacing: Optional[float] = None

    def font(self, font: str) -> Self:
        self._font = font
        return self

    def size(self, size: float) -> Self:
        self._size = size
        return self

    def fill_color(self, color: PdfColorRequest) -> Self:
        self._fill_color = color
        return self

    def stroke_color(self, color: PdfColorRequest) -> Self:
        self._stroke_color = color
        return self

    def character_spacing(self, spacing: float) -> Self:
        self._character_spacing = spacing
        return self

    def word_spacing(self, spacing: float) -> Self:
        self._word_spacing = spacing
        return self

    def _kwargs(self) -> dict[str, Any]:
        return {
            "font": self._font,
            "size": self._size,
            "fill_color": self._fill_color,
            "stroke_color": self._stroke_color,
            "character_spacing": self._character_spacing,
            "word_spacing": self._word_spacing,
        }


class TextStylePatchBuilder(_TextStyleBuilderBase):
    @classmethod
    def from_style(
        cls, style: Optional[TextStylePatchRequest]
    ) -> "TextStylePatchBuilder":
        builder = cls()
        if style is not None:
            builder._font = style.font
            builder._size = style.size
            builder._fill_color = style.fill_color
            builder._stroke_color = style.stroke_color
            builder._character_spacing = style.character_spacing
            builder._word_spacing = style.word_spacing
        return builder

    def build(self) -> TextStylePatchRequest:
        return TextStylePatchRequest(**self._kwargs()).validated()


class TextStyleSetBuilder(_TextStyleBuilderBase):
    def __init__(self) -> None:
        super().__init__()
        self._reset_spacing_overrides: Optional[bool] = None

    @classmethod
    def from_style(cls, style: Optional[TextStyleSetRequest]) -> "TextStyleSetBuilder":
        builder = cls()
        if style is not None:
            builder._font = style.font
            builder._size = style.size
            builder._fill_color = style.fill_color
            builder._stroke_color = style.stroke_color
            builder._character_spacing = style.character_spacing
            builder._word_spacing = style.word_spacing
            builder._reset_spacing_overrides = style.reset_spacing_overrides
        return builder

    def reset_spacing_overrides(self) -> Self:
        self._reset_spacing_overrides = True
        return self

    def build(self) -> TextStyleSetRequest:
        return TextStyleSetRequest(
            **self._kwargs(), reset_spacing_overrides=self._reset_spacing_overrides
        ).validated()


@dataclass(frozen=True)
class TextReplacementImageRequest:
    data: bytes
    transformation: PdfAffineTransform

    def validated(self) -> "TextReplacementImageRequest":
        if not self.data:
            raise ValidationException(
                "replaceWithImage image data is required and must not be empty"
            )
        if self.transformation is None:
            raise ValidationException("replaceWithImage transformation is required")
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return {
            "data": base64.b64encode(self.data).decode("ascii"),
            "transformationMatrix": list(self.transformation.to_pdf_matrix()),
        }


class _SelectorLayoutBuilder:
    def __init__(self) -> None:
        self._pages: Optional[tuple[int, ...]] = None
        self._literal: Optional[str] = None
        self._regex: Optional[str] = None
        self._case_sensitive: Optional[bool] = None
        self._whole_words: Optional[bool] = None
        self._max_matches: Optional[int] = None
        self._layout: Optional[TextLayoutRequest] = None
        self._hyphenation_enabled: Optional[bool] = None

    def pages(self, *pages: int | Sequence[int]) -> Self:
        values: Sequence[int]
        if (
            len(pages) == 1
            and isinstance(pages[0], Sequence)
            and not isinstance(pages[0], (str, bytes))
        ):
            values = pages[0]
        else:
            values = cast(Sequence[int], pages)
        self._pages = tuple(values)
        return self

    def literal(self, literal: str) -> Self:
        self._literal, self._regex = literal, None
        return self

    def regex(self, regex: str) -> Self:
        self._regex, self._literal = regex, None
        return self

    def case_sensitive(self, case_sensitive: bool) -> Self:
        self._case_sensitive = case_sensitive
        return self

    def whole_words(self, whole_words: bool) -> Self:
        self._whole_words = whole_words
        return self

    def max_matches(self, max_matches: int) -> Self:
        self._max_matches = max_matches
        return self

    def source_anchored(self) -> Self:
        self._layout = TextLayoutRequest.source_anchored()
        self._hyphenation_enabled = None
        return self

    def reflow_when_supported(self, profile: TextLayoutProfile) -> Self:
        self._layout = TextLayoutRequest.reflow_when_supported(profile)
        return self

    def require_reflow(self, profile: TextLayoutProfile) -> Self:
        self._layout = TextLayoutRequest.require_reflow(profile)
        return self

    def hyphenation_enabled(self, enabled: bool) -> Self:
        self._hyphenation_enabled = enabled
        return self

    def layout(self, layout: Optional[TextLayoutRequest]) -> Self:
        self._layout = layout
        self._hyphenation_enabled = (
            None if layout is None else layout.hyphenation_enabled
        )
        return self

    def _selector(self) -> TextSelectorRequest:
        return TextSelectorRequest(
            self._literal,
            self._regex,
            self._case_sensitive,
            self._whole_words,
            self._max_matches,
        )

    def _resolved_layout(self) -> Optional[TextLayoutRequest]:
        if self._layout is None:
            return (
                None
                if self._hyphenation_enabled is None
                else TextLayoutRequest(hyphenation_enabled=self._hyphenation_enabled)
            )
        return replace(self._layout, hyphenation_enabled=self._hyphenation_enabled)


@dataclass(frozen=True)
class TextReplaceRequest:
    pages: Optional[tuple[int, ...]]
    select: TextSelectorRequest
    replace_with: Optional[str] = None
    replace_with_image: Optional[TextReplacementImageRequest] = None
    style: Optional[TextStyleSetRequest] = None
    layout: Optional[TextLayoutRequest] = None

    @classmethod
    def literal(cls, text: str, replace_with: str) -> "TextReplaceBuilder":
        return TextReplaceBuilder().literal(text).replace_with(replace_with)

    @classmethod
    def regex(cls, regex: str, replace_with: str) -> "TextReplaceBuilder":
        return TextReplaceBuilder().regex(regex).replace_with(replace_with)

    @classmethod
    def builder(cls) -> "TextReplaceBuilder":
        return TextReplaceBuilder()

    def with_pages(self, pages: Sequence[int]) -> "TextReplaceRequest":
        return replace(self, pages=tuple(pages)).validated()

    def validated(self) -> "TextReplaceRequest":
        """Validate the request.

        ``replaceWithImage`` needs a ``sourceAnchored`` layout. When ``layout`` is
        ``None``, the returned request has ``TextLayoutRequest.source_anchored()``.
        """
        _validated_pages(self.pages)
        self.select.validated()
        if (self.replace_with is None) == (self.replace_with_image is None):
            raise ValidationException(
                "Exactly one of replaceWith or replaceWithImage is required"
            )
        request = self
        if self.replace_with_image is not None:
            self.replace_with_image.validated()
            if self.style is not None:
                raise ValidationException("style is not valid with replaceWithImage")
            if self.layout is not None and self.layout.alignment is not None:
                raise ValidationException(
                    "layout.alignment is not valid with replaceWithImage"
                )
            if self.layout is None:
                request = replace(self, layout=TextLayoutRequest.source_anchored())
            elif self.layout.mode is not TextLayoutMode.SOURCE_ANCHORED:
                raise ValidationException(
                    "replaceWithImage supports only sourceAnchored layout"
                )
        if self.style is not None:
            self.style.validated()
        if request.layout is not None:
            request.layout.validated()
        return request

    def to_dict(self) -> dict[str, Any]:
        request = self.validated()
        return _without_none(
            {
                "pages": list(request.pages) if request.pages is not None else None,
                "select": request.select.to_dict(),
                "replaceWith": request.replace_with,
                "replaceWithImage": (
                    request.replace_with_image.to_dict()
                    if request.replace_with_image
                    else None
                ),
                "style": request.style.to_dict() if request.style else None,
                "layout": request.layout.to_dict() if request.layout else None,
            }
        )


class TextReplaceBuilder(_SelectorLayoutBuilder, _TextStyleBuilderBase):
    """Build a validated text-replacement request."""

    def __init__(self) -> None:
        _SelectorLayoutBuilder.__init__(self)
        _TextStyleBuilderBase.__init__(self)
        self._replace_with: Optional[str] = None
        self._replace_with_image: Optional[TextReplacementImageRequest] = None
        self._style: Optional[TextStyleSetRequest] = None
        self._reset_spacing_overrides: Optional[bool] = None
        self._alignment: Optional[TextAlignment] = None

    def alignment(self, alignment: TextAlignment) -> "TextReplaceBuilder":
        """Align each edited line explicitly. Valid only for text replace.

        Without a layout, this selects ``reflowWhenSupported`` with the
        ``KEEP_LINE_BREAKS`` profile, the API default for an omitted layout. It can be
        combined with ``reflow_when_supported(...)`` and ``require_reflow(...)``
        in any order. ``source_anchored()`` and ``replace_with_image(...)`` are
        rejected at ``build()``.

        ``layout(...)`` keeps this alignment, unless the layout that it gets has
        its own alignment.

        The API reports an alignment that it cannot apply as an error with code
        ``TextOperationDiagnostic.ALIGNMENT_NOT_HONORED``. The API then does not
        change the text of the unit named in the error. Other matches can still
        change. The response is returned without an exception. Check
        ``response.errors`` together with ``response.changed``.
        """
        self._alignment = alignment
        return self

    def layout(self, layout: Optional[TextLayoutRequest]) -> Self:
        super().layout(layout)
        if layout is not None and layout.alignment is not None:
            self._alignment = layout.alignment
        return self

    def _resolved_layout(self) -> Optional[TextLayoutRequest]:
        layout = super()._resolved_layout()
        if self._alignment is None:
            return layout
        if layout is None:
            layout = TextLayoutRequest.reflow_when_supported(
                TextLayoutProfile.KEEP_LINE_BREAKS
            )
        return replace(layout, alignment=self._alignment)

    def replace_with(self, value: str) -> "TextReplaceBuilder":
        self._replace_with, self._replace_with_image = value, None
        return self

    def replace_with_image(
        self,
        image: bytes | bytearray | Path | str,
        transformation: PdfAffineTransform,
    ) -> "TextReplaceBuilder":
        if isinstance(image, (str, Path)):
            data = Path(image).read_bytes()
        else:
            data = bytes(image)
        self._replace_with = None
        self._replace_with_image = TextReplacementImageRequest(data, transformation)
        return self

    def style(self, style: TextStyleSetRequest) -> "TextReplaceBuilder":
        self._style = style
        self._font = style.font
        self._size = style.size
        self._fill_color = style.fill_color
        self._stroke_color = style.stroke_color
        self._character_spacing = style.character_spacing
        self._word_spacing = style.word_spacing
        self._reset_spacing_overrides = style.reset_spacing_overrides
        return self

    def reset_spacing_overrides(self) -> "TextReplaceBuilder":
        self._reset_spacing_overrides = True
        return self

    def build(self) -> TextReplaceRequest:
        style_values = {
            **self._kwargs(),
            "reset_spacing_overrides": self._reset_spacing_overrides,
        }
        style = (
            TextStyleSetRequest(**style_values)
            if any(value is not None for value in style_values.values())
            else None
        )
        return TextReplaceRequest(
            self._pages,
            self._selector(),
            self._replace_with,
            self._replace_with_image,
            style,
            self._resolved_layout(),
        ).validated()


@dataclass(frozen=True)
class TextDeleteRequest:
    pages: Optional[tuple[int, ...]]
    select: TextSelectorRequest
    layout: Optional[TextLayoutRequest] = None

    @classmethod
    def literal(cls, text: str) -> "TextDeleteBuilder":
        return TextDeleteBuilder().literal(text)

    @classmethod
    def regex(cls, regex: str) -> "TextDeleteBuilder":
        return TextDeleteBuilder().regex(regex)

    @classmethod
    def builder(cls) -> "TextDeleteBuilder":
        return TextDeleteBuilder()

    def with_pages(self, pages: Sequence[int]) -> "TextDeleteRequest":
        return replace(self, pages=tuple(pages)).validated()

    def validated(self) -> "TextDeleteRequest":
        _validated_pages(self.pages)
        self.select.validated()
        _reject_alignment(self.layout)
        if self.layout:
            self.layout.validated()
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return _without_none(
            {
                "pages": list(self.pages) if self.pages is not None else None,
                "select": self.select.to_dict(),
                "layout": self.layout.to_dict() if self.layout else None,
            }
        )


class TextDeleteBuilder(_SelectorLayoutBuilder):
    """Build a validated text-deletion request."""

    def build(self) -> TextDeleteRequest:
        return TextDeleteRequest(
            self._pages, self._selector(), self._resolved_layout()
        ).validated()


class TextInsertCaret(Enum):
    BEFORE = "before"
    AFTER = "after"


class TextInsertStyleFrom(Enum):
    ANCHOR = "anchor"


@dataclass(frozen=True)
class TextInsertAnchorTargetRequest:
    pages: Optional[tuple[int, ...]]
    select: TextSelectorRequest
    caret: TextInsertCaret

    def to_dict(self) -> dict[str, Any]:
        _validated_pages(self.pages)
        self.select.validated()
        if self.caret is None:
            raise ValidationException("target.anchor.caret must not be null")
        return _without_none(
            {
                "pages": list(self.pages) if self.pages is not None else None,
                "select": self.select.to_dict(),
                "caret": self.caret.value,
            }
        )


@dataclass(frozen=True)
class TextInsertCoordinateTargetRequest:
    page: Optional[int]
    x: float
    y: float
    rotation_degrees: Optional[float] = None

    def validated(
        self, allow_missing_page: bool = False
    ) -> "TextInsertCoordinateTargetRequest":
        if self.page is None and not allow_missing_page:
            raise ValidationException("target.coordinate.page must be >= 1")
        if self.page is not None and self.page < 1:
            raise ValidationException("target.coordinate.page must be >= 1")
        _require_finite(self.x, "target.coordinate.x")
        _require_finite(self.y, "target.coordinate.y")
        if self.rotation_degrees is not None:
            _require_finite(self.rotation_degrees, "target.coordinate.rotationDegrees")
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return _without_none(
            {
                "page": self.page,
                "x": self.x,
                "y": self.y,
                "rotationDegrees": self.rotation_degrees,
            }
        )


@dataclass(frozen=True)
class TextInsertTargetRequest:
    anchor: Optional[TextInsertAnchorTargetRequest] = None
    coordinate: Optional[TextInsertCoordinateTargetRequest] = None

    def to_dict(self) -> dict[str, Any]:
        if (self.anchor is None) == (self.coordinate is None):
            raise ValidationException(
                "Exactly one of target.anchor or target.coordinate must be provided"
            )
        return _without_none(
            {
                "anchor": self.anchor.to_dict() if self.anchor else None,
                "coordinate": self.coordinate.to_dict() if self.coordinate else None,
            }
        )


@dataclass(frozen=True)
class TextInsertStyleRequest:
    from_style: Optional[TextInsertStyleFrom]
    patch: Optional[TextStylePatchRequest]

    def to_dict(self) -> dict[str, Any]:
        if self.patch is not None:
            self.patch.validated()
        return _without_none(
            {
                "from": self.from_style.value if self.from_style else None,
                "patch": self.patch.to_dict() if self.patch else None,
            }
        )


@dataclass(frozen=True)
class TextInsertRequest:
    target: TextInsertTargetRequest
    insert: str
    style: TextInsertStyleRequest
    layout: Optional[TextLayoutRequest] = None

    @classmethod
    def after(cls, anchor_literal: str, insert: str) -> "TextInsertBuilder":
        return TextInsertBuilder().literal(anchor_literal).insert(insert).after()

    @classmethod
    def before(cls, anchor_literal: str, insert: str) -> "TextInsertBuilder":
        return TextInsertBuilder().literal(anchor_literal).insert(insert).before()

    @classmethod
    def after_regex(cls, anchor_regex: str, insert: str) -> "TextInsertBuilder":
        return TextInsertBuilder().regex(anchor_regex).insert(insert).after()

    @classmethod
    def before_regex(cls, anchor_regex: str, insert: str) -> "TextInsertBuilder":
        return TextInsertBuilder().regex(anchor_regex).insert(insert).before()

    @classmethod
    def at(cls, page: int, x: float, y: float, insert: str) -> "TextInsertBuilder":
        return TextInsertBuilder().coordinate(page, x, y).insert(insert)

    @classmethod
    def builder(cls) -> "TextInsertBuilder":
        return TextInsertBuilder()

    def with_pages(self, pages: Sequence[int]) -> "TextInsertRequest":
        normalized = _validated_pages(pages)
        assert normalized is not None
        if self.target.anchor is not None:
            target = replace(
                self.target, anchor=replace(self.target.anchor, pages=normalized)
            )
        elif len(normalized) == 1 and self.target.coordinate is not None:
            target = replace(
                self.target,
                coordinate=replace(self.target.coordinate, page=normalized[0]),
            )
        else:
            target = self.target
        return replace(self, target=target).validated()

    def validated(self) -> "TextInsertRequest":
        return self._validated(allow_missing_coordinate_page=False)

    def _validated(self, allow_missing_coordinate_page: bool) -> "TextInsertRequest":
        if self.target is None:
            raise ValidationException("target must not be null")
        has_anchor = self.target.anchor is not None
        if has_anchor == (self.target.coordinate is not None):
            raise ValidationException(
                "Exactly one of target.anchor or target.coordinate must be provided"
            )
        if has_anchor:
            assert self.target.anchor is not None
            self.target.anchor.to_dict()
        else:
            assert self.target.coordinate is not None
            self.target.coordinate.validated(allow_missing_coordinate_page)
        if self.insert is None or self.insert == "":
            raise ValidationException("insert must not be null or empty")
        if self.style is None:
            raise ValidationException("style must not be null")
        if has_anchor and self.style.from_style is not TextInsertStyleFrom.ANCHOR:
            raise ValidationException("style.from must be anchor")
        if not has_anchor and self.style.from_style is not None:
            raise ValidationException(
                "style.from is not valid for coordinate insertion"
            )
        patch = self.style.patch
        if patch is not None:
            patch.validated()
        if not has_anchor and patch is None:
            raise ValidationException(
                "style.patch must not be null for coordinate insertion"
            )
        if (
            not has_anchor
            and patch is not None
            and (patch.font is None or patch.size is None)
        ):
            raise ValidationException(
                "coordinate insertion style.patch requires font and size"
            )
        _reject_alignment(self.layout)
        if self.layout:
            self.layout.validated()
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return _without_none(
            {
                "target": self.target.to_dict(),
                "insert": self.insert,
                "style": self.style.to_dict(),
                "layout": self.layout.to_dict() if self.layout else None,
            }
        )


class TextInsertBuilder(_SelectorLayoutBuilder, _TextStyleBuilderBase):
    """Build a validated text-insertion request."""

    def __init__(self) -> None:
        _SelectorLayoutBuilder.__init__(self)
        _TextStyleBuilderBase.__init__(self)
        self._caret: Optional[TextInsertCaret] = None
        self._coordinate: Optional[TextInsertCoordinateTargetRequest] = None
        self._insert: Optional[str] = None

    def before(self) -> "TextInsertBuilder":
        self._caret, self._coordinate = TextInsertCaret.BEFORE, None
        return self

    def after(self) -> "TextInsertBuilder":
        self._caret, self._coordinate = TextInsertCaret.AFTER, None
        return self

    def caret(self, caret: TextInsertCaret) -> "TextInsertBuilder":
        self._caret, self._coordinate = caret, None
        return self

    def coordinate(self, *args: float) -> "TextInsertBuilder":
        if len(args) == 3:
            page, x, y = args
            self._coordinate = TextInsertCoordinateTargetRequest(int(page), x, y)
        elif len(args) == 2:
            x, y = args
            self._coordinate = TextInsertCoordinateTargetRequest(None, x, y)
        else:
            raise TypeError("coordinate() requires (page, x, y) or (x, y)")
        self._caret = None
        return self

    def rotation_degrees(self, degrees: float) -> "TextInsertBuilder":
        if self._coordinate is None:
            raise ValidationException("coordinate target must be set before rotation")
        self._coordinate = replace(self._coordinate, rotation_degrees=degrees)
        return self

    def insert(self, insert: str) -> "TextInsertBuilder":
        self._insert = insert
        return self

    def style_patch(self, patch: TextStylePatchRequest) -> "TextInsertBuilder":
        self._font = patch.font
        self._size = patch.size
        self._fill_color = patch.fill_color
        self._stroke_color = patch.stroke_color
        self._character_spacing = patch.character_spacing
        self._word_spacing = patch.word_spacing
        return self

    def build(self) -> TextInsertRequest:
        if self._coordinate is not None:
            coordinate = self._coordinate
            if coordinate.page is None and self._pages and len(self._pages) == 1:
                coordinate = replace(coordinate, page=self._pages[0])
            target = TextInsertTargetRequest(coordinate=coordinate)
            from_style = None
        else:
            target = TextInsertTargetRequest(
                anchor=TextInsertAnchorTargetRequest(
                    self._pages, self._selector(), self._caret  # type: ignore[arg-type]
                )
            )
            from_style = TextInsertStyleFrom.ANCHOR
        patch_values = self._kwargs()
        patch = (
            TextStylePatchRequest(**patch_values)
            if any(value is not None for value in patch_values.values())
            else None
        )
        style = TextInsertStyleRequest(from_style, patch)
        request = TextInsertRequest(
            target, self._insert, style, self._resolved_layout()  # type: ignore[arg-type]
        )
        return request._validated(
            allow_missing_coordinate_page=(
                self._coordinate is not None and self._coordinate.page is None
            )
        )


@dataclass(frozen=True)
class TextStyleRequest:
    pages: Optional[tuple[int, ...]]
    select: TextStyleSelectorRequest
    style: TextStyleSetRequest
    layout: Optional[TextLayoutRequest] = None

    @classmethod
    def literal(cls, text: str) -> "TextStyleBuilder":
        return TextStyleBuilder().literal(text)

    @classmethod
    def regex(cls, regex: str) -> "TextStyleBuilder":
        return TextStyleBuilder().regex(regex)

    @classmethod
    def runs_where(cls) -> "TextStyleBuilder":
        return TextStyleBuilder().runs_where()

    @classmethod
    def builder(cls) -> "TextStyleBuilder":
        return TextStyleBuilder()

    def with_pages(self, pages: Sequence[int]) -> "TextStyleRequest":
        return replace(self, pages=tuple(pages)).validated()

    def validated(self) -> "TextStyleRequest":
        _validated_pages(self.pages)
        if self.select is None:
            raise ValidationException("select must not be null")
        self.select.validated()
        if self.style is None:
            raise ValidationException("style must not be null")
        self.style.validated()
        _reject_alignment(self.layout)
        if self.layout:
            self.layout.validated()
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validated()
        return _without_none(
            {
                "pages": list(self.pages) if self.pages is not None else None,
                "select": self.select.to_dict(),
                "style": self.style.to_dict(),
                "layout": self.layout.to_dict() if self.layout else None,
            }
        )


class TextStyleBuilder(_SelectorLayoutBuilder, _TextStyleBuilderBase):
    """Build a validated request that changes existing text appearance."""

    def __init__(self) -> None:
        _SelectorLayoutBuilder.__init__(self)
        _TextStyleBuilderBase.__init__(self)
        self._runs_where = False
        self._where_text_contains: Optional[str] = None
        self._where_font: Optional[str] = None
        self._where_size: Optional[TextStyleNumericFilterRequest] = None
        self._where_fill_color: Optional[PdfColorRequest] = None
        self._where_stroke_color: Optional[PdfColorRequest] = None
        self._where_character_spacing: Optional[TextStyleNumericFilterRequest] = None
        self._where_word_spacing: Optional[TextStyleNumericFilterRequest] = None
        self._where_contains_unmapped_glyphs: Optional[bool] = None
        self._reset_spacing_overrides: Optional[bool] = None

    def literal(self, literal: str) -> "TextStyleBuilder":
        super().literal(literal)
        self._runs_where = False
        return self

    def regex(self, regex: str) -> "TextStyleBuilder":
        super().regex(regex)
        self._runs_where = False
        return self

    def runs_where(self) -> "TextStyleBuilder":
        self._runs_where = True
        self._literal = self._regex = None
        return self

    def where_text_contains(self, text: str) -> "TextStyleBuilder":
        self.runs_where()
        self._where_text_contains = text
        return self

    def where_font(self, font: str) -> "TextStyleBuilder":
        self.runs_where()
        self._where_font = font
        return self

    def where_size(
        self, eq: float, tolerance: Optional[float] = None
    ) -> "TextStyleBuilder":
        self.runs_where()
        self._where_size = TextStyleNumericFilterRequest.equal_to(eq, tolerance)
        return self

    def where_fill_color(self, color: PdfColorRequest) -> "TextStyleBuilder":
        self.runs_where()
        self._where_fill_color = color
        return self

    def where_stroke_color(self, color: PdfColorRequest) -> "TextStyleBuilder":
        self.runs_where()
        self._where_stroke_color = color
        return self

    def where_character_spacing(
        self, eq: float, tolerance: Optional[float] = None
    ) -> "TextStyleBuilder":
        self.runs_where()
        self._where_character_spacing = TextStyleNumericFilterRequest.equal_to(
            eq, tolerance
        )
        return self

    def where_word_spacing(
        self, eq: float, tolerance: Optional[float] = None
    ) -> "TextStyleBuilder":
        self.runs_where()
        self._where_word_spacing = TextStyleNumericFilterRequest.equal_to(eq, tolerance)
        return self

    def where_contains_unmapped_glyphs(self, value: bool) -> "TextStyleBuilder":
        self.runs_where()
        self._where_contains_unmapped_glyphs = value
        return self

    def reset_spacing_overrides(self, value: bool = True) -> "TextStyleBuilder":
        self._reset_spacing_overrides = value
        return self

    def build(self) -> TextStyleRequest:
        if self._runs_where:
            run_filter = TextStyleRunFilterRequest(
                self._where_text_contains,
                self._where_font,
                self._where_size,
                self._where_fill_color,
                self._where_stroke_color,
                self._where_character_spacing,
                self._where_word_spacing,
                self._where_contains_unmapped_glyphs,
            )
            selector = TextStyleSelectorRequest(
                runs=TextStyleRunsSelectorRequest(run_filter, self._max_matches)
            )
        else:
            selector = TextStyleSelectorRequest.from_text_selector(self._selector())
        style = TextStyleSetRequest(
            **self._kwargs(), reset_spacing_overrides=self._reset_spacing_overrides
        )
        return TextStyleRequest(
            self._pages, selector, style, self._resolved_layout()
        ).validated()


@dataclass(frozen=True)
class TextOperationDiagnostic:
    # Error code of a requested ``layout.alignment`` that the API could not
    # apply. The API does not change the text of the unit named in the error.
    # Other matches can still change. No exception is raised; check
    # ``TextEditResponse.errors`` together with ``TextEditResponse.changed``.
    ALIGNMENT_NOT_HONORED = "TEXT_ALIGNMENT_NOT_HONORED"

    page: Optional[int]
    code: Optional[str]
    message: Optional[str]
    element_ids: Optional[tuple[str, ...]]
    reflow_unit_ids: Optional[tuple[str, ...]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TextOperationDiagnostic":
        return cls(
            data.get("page"),
            data.get("code"),
            data.get("message"),
            None if data.get("elementIds") is None else tuple(data["elementIds"]),
            (
                None
                if data.get("reflowUnitIds") is None
                else tuple(data["reflowUnitIds"])
            ),
        )


@dataclass(frozen=True)
class TextEditChangeDiagnostic:
    page: Optional[int]
    operation: Optional[str]
    source_text: Optional[str]
    result_text: Optional[str]
    requested_layout_mode: Optional[str]
    requested_layout_profile: Optional[str]
    effective_hyphenation_enabled: bool
    applied_layout_mode: Optional[str]
    element_ids: Optional[tuple[str, ...]]
    generated_element_ids: Optional[tuple[str, ...]]
    reflow_unit_ids: Optional[tuple[str, ...]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TextEditChangeDiagnostic":
        return cls(
            data.get("page"),
            data.get("operation"),
            data.get("sourceText"),
            data.get("resultText"),
            data.get("requestedLayoutMode"),
            data.get("requestedLayoutProfile"),
            bool(data.get("effectiveHyphenationEnabled", False)),
            data.get("appliedLayoutMode"),
            None if data.get("elementIds") is None else tuple(data["elementIds"]),
            (
                None
                if data.get("generatedElementIds") is None
                else tuple(data["generatedElementIds"])
            ),
            (
                None
                if data.get("reflowUnitIds") is None
                else tuple(data["reflowUnitIds"])
            ),
        )


@dataclass(frozen=True)
class TextEditResponse:
    matched: Optional[int]
    changed: Optional[int]
    pages_changed: Optional[tuple[int, ...]]
    change: Optional[tuple[TextEditChangeDiagnostic, ...]]
    warnings: Optional[tuple[TextOperationDiagnostic, ...]]
    errors: Optional[tuple[TextOperationDiagnostic, ...]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TextEditResponse":
        return cls(
            data.get("matched"),
            data.get("changed"),
            (None if data.get("pagesChanged") is None else tuple(data["pagesChanged"])),
            (
                None
                if data.get("change") is None
                else tuple(
                    TextEditChangeDiagnostic.from_dict(item) for item in data["change"]
                )
            ),
            (
                None
                if data.get("warnings") is None
                else tuple(
                    TextOperationDiagnostic.from_dict(item) for item in data["warnings"]
                )
            ),
            (
                None
                if data.get("errors") is None
                else tuple(
                    TextOperationDiagnostic.from_dict(item) for item in data["errors"]
                )
            ),
        )


TextLayoutRequest.Mode = TextLayoutMode  # type: ignore[attr-defined]
TextLayoutRequest.Profile = TextLayoutProfile  # type: ignore[attr-defined]
TextLayoutRequest.Alignment = TextAlignment  # type: ignore[attr-defined]


__all__ = [
    name for name in globals() if name.startswith("Text") or name.startswith("Pdf")
]
