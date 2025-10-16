"""
PDFDancer Python Client

A Python client library for the PDFDancer PDF manipulation API.
Provides a clean, Pythonic interface for PDF operations that closely
mirrors the Java client structure and functionality.
"""

from .exceptions import (
    PdfDancerException, FontNotFoundException, ValidationException,
    HttpClientException, SessionException
)
from .models import (
    ObjectRef, Position, ObjectType, Font, Color, Image, BoundingRect, Paragraph, FormFieldRef,
    PositionMode, ShapeType, Point, StandardFonts
)
from .paragraph_builder import ParagraphBuilder

__version__ = "1.0.0"
__all__ = [
    "PDFDancer",
    "ParagraphBuilder",
    "ObjectRef",
    "Position",
    "ObjectType",
    "Font",
    "Color",
    "Image",
    "BoundingRect",
    "Paragraph",
    "FormFieldRef",
    "PositionMode",
    "ShapeType",
    "Point",
    "StandardFonts",
    "PdfDancerException",
    "FontNotFoundException",
    "ValidationException",
    "HttpClientException",
    "SessionException"
]

from .pdfdancer_v1 import PDFDancer
