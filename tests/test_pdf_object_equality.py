"""
Tests for __eq__ implementations on PDFObjectBase subclasses.
"""

from unittest.mock import Mock

import pytest

from pdfdancer import Color, ObjectType, Position, TextObjectRef
from pdfdancer.types import (
    FormFieldObject,
    FormObject,
    ImageObject,
    ParagraphObject,
    PathObject,
    TextLineObject,
)


class TestPDFObjectEquality:
    """Test equality implementations for all PDFObjectBase subclasses."""

    def test_path_object_equality_same_id(self):
        """PathObject instances with same internal_id and type should be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj1 = PathObject(mock_client, "id123", ObjectType.PATH, position)
        obj2 = PathObject(mock_client, "id123", ObjectType.PATH, position)

        assert obj1 == obj2

    def test_path_object_equality_different_id(self):
        """PathObject instances with different internal_id should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj1 = PathObject(mock_client, "id123", ObjectType.PATH, position)
        obj2 = PathObject(mock_client, "id456", ObjectType.PATH, position)

        assert obj1 != obj2

    def test_path_object_equality_different_position(self):
        """PathObject instances with different positions should not be equal."""
        mock_client = Mock()
        position1 = Position.at_page(1)
        position2 = Position.at_page(2)

        obj1 = PathObject(mock_client, "id123", ObjectType.PATH, position1)
        obj2 = PathObject(mock_client, "id123", ObjectType.PATH, position2)

        assert obj1 != obj2

    def test_path_object_equality_different_type(self):
        """PathObject should not equal non-PathObject."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj1 = PathObject(mock_client, "id123", ObjectType.PATH, position)
        obj2 = ImageObject(mock_client, "id123", ObjectType.IMAGE, position)

        assert obj1 != obj2

    def test_image_object_equality_same_id(self):
        """ImageObject instances with same internal_id and type should be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj1 = ImageObject(mock_client, "id123", ObjectType.IMAGE, position)
        obj2 = ImageObject(mock_client, "id123", ObjectType.IMAGE, position)

        assert obj1 == obj2

    def test_image_object_equality_different_id(self):
        """ImageObject instances with different internal_id should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj1 = ImageObject(mock_client, "id123", ObjectType.IMAGE, position)
        obj2 = ImageObject(mock_client, "id456", ObjectType.IMAGE, position)

        assert obj1 != obj2

    def test_form_object_equality_same_id(self):
        """FormObject instances with same internal_id and type should be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj1 = FormObject(mock_client, "id123", ObjectType.FORM_X_OBJECT, position)
        obj2 = FormObject(mock_client, "id123", ObjectType.FORM_X_OBJECT, position)

        assert obj1 == obj2

    def test_form_object_equality_different_id(self):
        """FormObject instances with different internal_id should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj1 = FormObject(mock_client, "id123", ObjectType.FORM_X_OBJECT, position)
        obj2 = FormObject(mock_client, "id456", ObjectType.FORM_X_OBJECT, position)

        assert obj1 != obj2

    def test_paragraph_object_equality_same_all_attributes(self):
        """ParagraphObject instances with same all attributes should be equal."""
        mock_client = Mock()
        position = Position.at_page(1)
        color = Color(255, 0, 0)

        text_ref1 = TextObjectRef(
            "id123",
            position,
            ObjectType.PARAGRAPH,
            text="Hello",
            font_name="Arial",
            font_size=12.0,
            line_spacings=[1.2],
            color=color,
        )
        text_ref2 = TextObjectRef(
            "id123",
            position,
            ObjectType.PARAGRAPH,
            text="Hello",
            font_name="Arial",
            font_size=12.0,
            line_spacings=[1.2],
            color=color,
        )

        obj1 = ParagraphObject(mock_client, text_ref1)
        obj2 = ParagraphObject(mock_client, text_ref2)

        assert obj1 == obj2

    def test_paragraph_object_equality_different_id(self):
        """ParagraphObject instances with different internal_id should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        text_ref1 = TextObjectRef("id123", position, ObjectType.PARAGRAPH)
        text_ref2 = TextObjectRef("id456", position, ObjectType.PARAGRAPH)

        obj1 = ParagraphObject(mock_client, text_ref1)
        obj2 = ParagraphObject(mock_client, text_ref2)

        assert obj1 != obj2

    def test_paragraph_object_equality_different_text(self):
        """ParagraphObject instances with different text should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        text_ref1 = TextObjectRef("id123", position, ObjectType.PARAGRAPH, text="Hello")
        text_ref2 = TextObjectRef("id123", position, ObjectType.PARAGRAPH, text="World")

        obj1 = ParagraphObject(mock_client, text_ref1)
        obj2 = ParagraphObject(mock_client, text_ref2)

        assert obj1 != obj2

    def test_paragraph_object_equality_different_font_name(self):
        """ParagraphObject instances with different font name should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        text_ref1 = TextObjectRef(
            "id123", position, ObjectType.PARAGRAPH, font_name="Arial"
        )
        text_ref2 = TextObjectRef(
            "id123", position, ObjectType.PARAGRAPH, font_name="Helvetica"
        )

        obj1 = ParagraphObject(mock_client, text_ref1)
        obj2 = ParagraphObject(mock_client, text_ref2)

        assert obj1 != obj2

    def test_paragraph_object_equality_different_font_size(self):
        """ParagraphObject instances with different font size should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        text_ref1 = TextObjectRef(
            "id123", position, ObjectType.PARAGRAPH, font_size=12.0
        )
        text_ref2 = TextObjectRef(
            "id123", position, ObjectType.PARAGRAPH, font_size=14.0
        )

        obj1 = ParagraphObject(mock_client, text_ref1)
        obj2 = ParagraphObject(mock_client, text_ref2)

        assert obj1 != obj2

    def test_paragraph_object_equality_different_color(self):
        """ParagraphObject instances with different color should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        text_ref1 = TextObjectRef(
            "id123", position, ObjectType.PARAGRAPH, color=Color(255, 0, 0)
        )
        text_ref2 = TextObjectRef(
            "id123", position, ObjectType.PARAGRAPH, color=Color(0, 255, 0)
        )

        obj1 = ParagraphObject(mock_client, text_ref1)
        obj2 = ParagraphObject(mock_client, text_ref2)

        assert obj1 != obj2

    def test_text_line_object_equality_same_id(self):
        """TextLineObject instances with same internal_id and type should be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        text_ref1 = TextObjectRef("id123", position, ObjectType.TEXT_LINE)
        text_ref2 = TextObjectRef("id123", position, ObjectType.TEXT_LINE)

        obj1 = TextLineObject(mock_client, text_ref1)
        obj2 = TextLineObject(mock_client, text_ref2)

        assert obj1 == obj2

    def test_text_line_object_equality_different_id(self):
        """TextLineObject instances with different internal_id should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        text_ref1 = TextObjectRef("id123", position, ObjectType.TEXT_LINE)
        text_ref2 = TextObjectRef("id456", position, ObjectType.TEXT_LINE)

        obj1 = TextLineObject(mock_client, text_ref1)
        obj2 = TextLineObject(mock_client, text_ref2)

        assert obj1 != obj2

    def test_form_field_object_equality_same_all_attributes(self):
        """FormFieldObject instances with same all attributes should be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj1 = FormFieldObject(
            mock_client, "id123", ObjectType.TEXT_FIELD, position, "name1", "value1"
        )
        obj2 = FormFieldObject(
            mock_client, "id123", ObjectType.TEXT_FIELD, position, "name1", "value1"
        )

        assert obj1 == obj2

    def test_form_field_object_equality_different_id(self):
        """FormFieldObject instances with different internal_id should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj1 = FormFieldObject(
            mock_client, "id123", ObjectType.TEXT_FIELD, position, "name1", "value1"
        )
        obj2 = FormFieldObject(
            mock_client, "id456", ObjectType.TEXT_FIELD, position, "name1", "value1"
        )

        assert obj1 != obj2

    def test_form_field_object_equality_different_name(self):
        """FormFieldObject instances with different name should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj1 = FormFieldObject(
            mock_client, "id123", ObjectType.TEXT_FIELD, position, "name1", "value1"
        )
        obj2 = FormFieldObject(
            mock_client, "id123", ObjectType.TEXT_FIELD, position, "name2", "value1"
        )

        assert obj1 != obj2

    def test_form_field_object_equality_different_value(self):
        """FormFieldObject instances with different value should not be equal."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj1 = FormFieldObject(
            mock_client, "id123", ObjectType.TEXT_FIELD, position, "name1", "value1"
        )
        obj2 = FormFieldObject(
            mock_client, "id123", ObjectType.TEXT_FIELD, position, "name1", "value2"
        )

        assert obj1 != obj2

    def test_equality_with_none(self):
        """PDFObjectBase subclasses should not equal None."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj = PathObject(mock_client, "id123", ObjectType.PATH, position)

        assert obj != None

    def test_equality_with_string(self):
        """PDFObjectBase subclasses should not equal strings."""
        mock_client = Mock()
        position = Position.at_page(1)

        obj = PathObject(mock_client, "id123", ObjectType.PATH, position)

        assert obj != "id123"
