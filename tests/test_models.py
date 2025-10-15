"""
Tests for model classes - mirrors Java model test patterns.
"""

import pytest

from pdfdancer import (
    ObjectRef, Position, ObjectType, Font, Color, Image, Paragraph, BoundingRect,
    PositionMode, ShapeType
)
# Import Point class for tests
from pdfdancer.models import Point


class TestPosition:
    """Test Position class functionality."""

    def test_from_page_index_creates_position(self):
        """Test Position.from_page_index() factory method."""
        position = Position.at_page(2)

        assert position.page_index == 2
        assert position.mode == PositionMode.CONTAINS
        assert position.shape is None
        assert position.bounding_rect is None

    def test_on_page_coordinates_creates_point_position(self):
        """Test Position.on_page_coordinates() factory method."""
        position = Position.at_page_coordinates(1, 100.5, 200.7)

        assert position.page_index == 1
        assert position.mode == PositionMode.CONTAINS
        assert position.shape == ShapeType.POINT
        assert position.bounding_rect.x == 100.5
        assert position.bounding_rect.y == 200.7
        assert position.bounding_rect.width == 0
        assert position.bounding_rect.height == 0

    def test_set_point_configures_position(self):
        """Test set_point() method configures position correctly."""
        position = Position()
        point = Point(50.0, 75.0)

        position.at_coordinates(point)

        assert position.mode == PositionMode.CONTAINS
        assert position.shape == ShapeType.POINT
        assert position.bounding_rect.x == 50.0
        assert position.bounding_rect.y == 75.0
        assert position.bounding_rect.width == 0
        assert position.bounding_rect.height == 0

    def test_get_x_y_coordinates(self):
        """Test get_x() and get_y() methods."""
        position = Position.at_page_coordinates(0, 123.45, 678.90)

        assert position.x() == 123.45
        assert position.y() == 678.90

    def test_get_x_y_returns_none_without_bounding_rect(self):
        """Test get_x() and get_y() return None without bounding rect."""
        position = Position()

        assert position.x() is None
        assert position.y() is None

    def test_move_x_updates_position(self):
        """Test move_x() updates x coordinate."""
        position = Position.at_page_coordinates(0, 100.0, 200.0)

        position.move_x(50.0)

        assert position.x() == 150.0
        assert position.y() == 200.0  # Unchanged

    def test_move_y_updates_position(self):
        """Test move_y() updates y coordinate."""
        position = Position.at_page_coordinates(0, 100.0, 200.0)

        position.move_y(-25.0)

        assert position.x() == 100.0  # Unchanged
        assert position.y() == 175.0

    def test_copy_creates_independent_copy(self):
        """Test copy() creates independent copy of position."""
        original = Position.at_page_coordinates(1, 50.0, 75.0)
        original = original.with_text_starts("Test")

        copy = original.copy()

        # Verify copy has same values
        assert copy.page_index == original.page_index
        assert copy.mode == original.mode
        assert copy.shape == original.shape
        assert copy.text_starts_with == original.text_starts_with
        assert copy.bounding_rect.x == original.bounding_rect.x

        # Verify they are independent objects
        assert copy is not original
        assert copy.bounding_rect is not original.bounding_rect


class TestObjectRef:
    """Test ObjectRef class functionality."""

    def test_constructor_sets_properties(self):
        """Test ObjectRef constructor sets all properties."""
        position = Position.at_page(0)
        obj_ref = ObjectRef("obj-123", position, ObjectType.PARAGRAPH)

        assert obj_ref.internal_id == "obj-123"
        assert obj_ref.position == position
        assert obj_ref.type == ObjectType.PARAGRAPH

    def test_getter_methods(self):
        """Test getter methods match Java patterns."""
        position = Position.at_page(1)
        obj_ref = ObjectRef("ref-456", position, ObjectType.IMAGE)

        assert obj_ref.get_internal_id() == "ref-456"
        assert obj_ref.get_position() == position
        assert obj_ref.get_type() == ObjectType.IMAGE

    def test_set_position_updates_position(self):
        """Test set_position() updates position reference."""
        original_position = Position.at_page(0)
        new_position = Position.at_page(1)
        obj_ref = ObjectRef("test", original_position, ObjectType.FORM_X_OBJECT)

        obj_ref.set_position(new_position)

        assert obj_ref.get_position() == new_position
        assert obj_ref.position == new_position


class TestColor:
    """Test Color class functionality."""

    def test_constructor_sets_rgb_values(self):
        """Test Color constructor sets RGB values."""
        color = Color(255, 128, 64)

        assert color.r == 255
        assert color.g == 128
        assert color.b == 64

    def test_validation_enforces_valid_range(self):
        """Test Color validates RGB values are in 0-255 range."""
        # Valid values should work
        Color(0, 128, 255)

        # Invalid values should raise ValueError
        with pytest.raises(ValueError, match="Color component must be between 0 and 255"):
            Color(-1, 0, 0)

        with pytest.raises(ValueError, match="Color component must be between 0 and 255"):
            Color(0, 256, 0)

        with pytest.raises(ValueError, match="Color component must be between 0 and 255"):
            Color(0, 0, 300)


class TestFont:
    """Test Font class functionality."""

    def test_constructor_sets_name_and_size(self):
        """Test Font constructor sets name and size."""
        font = Font("Arial", 12.5)

        assert font.name == "Arial"
        assert font.size == 12.5

    def test_validation_enforces_positive_size(self):
        """Test Font validates size is positive."""
        # Valid size should work
        Font("Times", 10.0)

        # Invalid sizes should raise ValueError
        with pytest.raises(ValueError, match="Font size must be positive"):
            Font("Arial", 0)

        with pytest.raises(ValueError, match="Font size must be positive"):
            Font("Arial", -5.0)


class TestImage:
    """Test Image class functionality."""

    def test_default_constructor(self):
        """Test Image default constructor."""
        image = Image()

        assert image.position is None

    def test_get_set_position(self):
        """Test Image position getter and setter."""
        image = Image()
        position = Position.at_page_coordinates(0, 100.0, 150.0)

        assert image.get_position() is None

        image.set_position(position)

        assert image.get_position() == position


class TestParagraph:
    """Test Paragraph class functionality."""

    def test_default_constructor(self):
        """Test Paragraph default constructor."""
        paragraph = Paragraph()

        assert paragraph.position is None
        assert paragraph.text_lines is None
        assert paragraph.font is None
        assert paragraph.color is None
        assert paragraph.line_spacing == 1.2  # Default value

    def test_get_set_position(self):
        """Test Paragraph position getter and setter."""
        paragraph = Paragraph()
        position = Position.at_page(2)

        assert paragraph.get_position() is None

        paragraph.set_position(position)

        assert paragraph.get_position() == position

    def test_constructor_with_parameters(self):
        """Test Paragraph constructor with all parameters."""
        position = Position.at_page(1)
        text_lines = ["Line 1", "Line 2"]
        font = Font("Arial", 14.0)
        color = Color(255, 0, 0)
        line_spacing = 1.5

        paragraph = Paragraph(position, text_lines, font, color, line_spacing)

        assert paragraph.position == position
        assert paragraph.text_lines == text_lines
        assert paragraph.font == font
        assert paragraph.color == color
        assert paragraph.line_spacing == line_spacing


class TestBoundingRect:
    """Test BoundingRect class functionality."""

    def test_constructor_sets_properties(self):
        """Test BoundingRect constructor sets all properties."""
        rect = BoundingRect(10.5, 20.7, 100.0, 50.0)

        assert rect.x == 10.5
        assert rect.y == 20.7
        assert rect.width == 100.0
        assert rect.height == 50.0

    def test_getter_methods(self):
        """Test getter methods match Java patterns."""
        rect = BoundingRect(1.0, 2.0, 3.0, 4.0)

        assert rect.get_x() == 1.0
        assert rect.get_y() == 2.0
        assert rect.get_width() == 3.0
        assert rect.get_height() == 4.0


class TestPoint:
    """Test Point class functionality."""

    def test_constructor_sets_coordinates(self):
        """Test Point constructor sets x and y coordinates."""
        point = Point(123.45, 678.90)

        assert point.x == 123.45
        assert point.y == 678.90
