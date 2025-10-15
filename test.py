"""
Comprehensive test showcasing all PDFDancer Python API features.
This file demonstrates the complete functionality of the pdfdancer library.
"""

from pathlib import Path

from pdfdancer import (
    ClientV1, Font, Position, Color, Image, Paragraph, ObjectType,
    Point, BoundingRect, PositionMode, ShapeType,
    FontNotFoundException
)


# noinspection PyUnusedLocal
def find_operations(client):
    """Test all find operations for different object types."""
    # Find all paragraphs
    paragraphs = client._find_paragraphs()

    # Find images
    images = client._find_images()

    # Find forms
    forms = client._find_form_x_objects()

    # Find paths
    paths = client._find_paths()

    # Find text lines
    text_lines = client._find_text_lines()

    # Find with specific object type and position
    specific_position = Position.at_page_coordinates(0, 100, 100)
    paragraphs_at_pos = client._find(ObjectType.PARAGRAPH, specific_position)

    return paragraphs, text_lines  # Keep only what's needed for object_manipulation


# noinspection PyUnusedLocal
def page_management(client):
    """Test page management operations."""
    # Get all pages
    pages = client.get_pages()

    # Get specific page
    first_page = None
    if pages:
        first_page = client._get_page(0)


# noinspection PyUnusedLocal
def position_system(client):
    """Test position and coordinate system operations."""
    # Different ways to create positions
    page_pos = Position.at_page(0)
    coord_pos = Position.at_page_coordinates(0, 50, 100)

    # Position manipulation
    moved_pos = coord_pos.copy()
    moved_pos.move_x(25.0)
    moved_pos.move_y(15.0)

    # Point and BoundingRect
    point = Point(10.0, 20.0)
    bounding_rect = BoundingRect(0.0, 0.0, 100.0, 50.0)


# noinspection PyUnusedLocal
def font_management(client):
    """Test font creation and management operations."""
    # Create fonts
    arial_font = Font("Arial", 12.0)
    times_font = Font("Times New Roman", 14.0)

    # Find fonts in document
    found_fonts = None
    try:
        found_fonts = client.find_fonts("Arial", 12)
    except FontNotFoundException as e:
        pass
    except Exception as e:
        pass


# noinspection PyUnusedLocal
def color_system(client):
    """Test color creation and management operations."""
    # Create colors
    red_color = Color(255, 0, 0)
    blue_color = Color(0, 0, 255, 128)  # With alpha


# noinspection PyUnusedLocal
def paragraph_operations(client):
    """Test paragraph builder and manipulation operations."""
    arial_font = Font("Arial", 12.0)
    arial_font_large = Font("Arial", 14.0)  # Use Arial instead of Times New Roman
    red_color = Color(255, 0, 0)
    blue_color = Color(0, 0, 255, 128)

    # Basic paragraph creation
    basic_paragraph = (client.paragraph_builder()
                       .from_string("Basic paragraph with default settings")
                       .with_font(arial_font)
                       .with_position(Position.at_page_coordinates(0, 50, 200))
                       .build())
    client._add_paragraph(basic_paragraph)

    # Advanced paragraph with all features
    advanced_paragraph = (client.paragraph_builder()
                          .from_string("Advanced paragraph\nwith multiple lines\nand styling", red_color)
                          .with_font(arial_font_large)
                          .with_line_spacing(1.5)
                          .with_color(blue_color)
                          .with_position(Position.at_page_coordinates(0, 50, 250))
                          .build())
    client._add_paragraph(advanced_paragraph)


# noinspection PyUnusedLocal
def object_manipulation(client, paragraphs, text_lines):
    """Test object manipulation operations including delete, move, and modify."""
    arial_font = Font("Arial", 14.0)  # Use Arial instead of Times New Roman
    red_color = Color(255, 0, 0)

    if paragraphs:
        # Delete operation
        first_paragraph = paragraphs[0]
        client._delete(first_paragraph)

        # Move operation (if we have more paragraphs)
        if len(paragraphs) > 1:
            second_paragraph = paragraphs[1]
            new_position = Position.at_page_coordinates(0, 100, 300)
            client._move(second_paragraph, new_position)

        # Modify operations
        if len(paragraphs) > 2:
            third_paragraph = paragraphs[2]

            # Modify with new paragraph object
            modified_paragraph = Paragraph(
                position=Position.at_page_coordinates(0, 50, 350),
                text_lines=["Modified paragraph text"],
                font=arial_font,
                color=red_color
            )
            client._modify_paragraph(third_paragraph, modified_paragraph)

            # Modify with just text
            if len(paragraphs) > 3:
                fourth_paragraph = paragraphs[3]
                client._modify_paragraph(fourth_paragraph, "Simple text modification")

    # Text line modification
    if text_lines:
        client.modify_text_line(text_lines[0], "Modified text line")


# noinspection PyUnusedLocal
def text_line_operations(client):
    """Test text line specific operations and showcases."""
    # Find all text lines in document
    all_text_lines = client._find_text_lines()

    # Find text lines at specific position
    specific_position = Position.at_page_coordinates(0, 100, 100)
    text_lines_at_position = client._find_text_lines(specific_position)

    # Find text lines on entire page
    page_position = Position.at_page(0)
    text_lines_on_page = client._find_text_lines(page_position)

    # Demonstrate text line modification if text lines are found
    modified_text_line = None
    if all_text_lines:
        first_text_line = all_text_lines[0]

        # Get text line properties via ObjectRef
        text_line_id = first_text_line.get_internal_id()
        text_line_type = first_text_line.get_type()
        text_line_position = first_text_line.get_position()

        # Modify text line content
        client.modify_text_line(first_text_line, "Modified text line content")
        modified_text_line = first_text_line

        # Demonstrate position modification for text lines
        if len(all_text_lines) > 1:
            second_text_line = all_text_lines[1]
            new_position = Position.at_page_coordinates(0, 120, 150)
            client._move(second_text_line, new_position)


# noinspection PyUnusedLocal
def form_operations(client):
    """Test form handling operations."""
    # Find all forms in document
    all_forms = client._find_form_x_objects()

    # Find forms at specific position
    specific_position = Position.at_page_coordinates(0, 150, 200)
    forms_at_position = client._find_form_x_objects(specific_position)

    # Find forms on entire page
    page_position = Position.at_page(0)
    forms_on_page = client._find_form_x_objects(page_position)

    # Demonstrate form manipulation if forms are found
    manipulated_form = None
    if all_forms:
        first_form = all_forms[0]

        # Get form properties via ObjectRef
        form_id = first_form.get_internal_id()
        form_type = first_form.get_type()
        form_position = first_form.get_position()

        # Demonstrate position modification for forms
        if len(all_forms) > 1:
            second_form = all_forms[1]
            new_position = Position.at_page_coordinates(0, 180, 250)
            client._move(second_form, new_position)
            manipulated_form = second_form

        # Demonstrate deletion (use last form to preserve others for testing)
        if len(all_forms) > 2:
            last_form = all_forms[-1]
            client._delete(last_form)


# noinspection PyUnusedLocal
def path_operations(client):
    """Test path handling operations."""
    # Find all paths in document
    all_paths = client._find_paths()

    # Find paths at specific position
    specific_position = Position.at_page_coordinates(0, 100, 150)
    paths_at_position = client._find_paths(specific_position)

    # Find paths on entire page
    page_position = Position.at_page(0)
    paths_on_page = client._find_paths(page_position)

    # Demonstrate path manipulation if paths are found
    manipulated_path = None
    if all_paths:
        first_path = all_paths[0]

        # Get path properties via ObjectRef
        path_id = first_path.get_internal_id()
        path_type = first_path.get_type()
        path_position = first_path.get_position()

        # Demonstrate position modification for paths
        if len(all_paths) > 1:
            second_path = all_paths[1]
            new_position = Position.at_page_coordinates(0, 120, 180)
            client._move(second_path, new_position)
            manipulated_path = second_path

        # Demonstrate deletion (use last path to preserve others for testing)
        if len(all_paths) > 2:
            last_path = all_paths[-1]
            client._delete(last_path)


# noinspection PyUnusedLocal
def register_font_operations(client):
    """Test font registration operations using JetBrainsMono-Regular.ttf."""
    # Register font using file path
    font_path = Path("tests/fixtures/JetBrainsMono-Regular.ttf")
    registered_font_name = client.register_font(font_path)

    # Create a Font object using the registered font
    jetbrains_font = Font(registered_font_name, 14.0)

    # Use the registered font in a paragraph
    paragraph_with_custom_font = (client.paragraph_builder()
                                  .from_string("This text uses JetBrains Mono font")
                                  .with_font(jetbrains_font)
                                  .with_position(Position.at_page_coordinates(0, 50, 450))
                                  .build())
    client._add_paragraph(paragraph_with_custom_font)

    # Register font using bytes (alternative method)
    with open(font_path, 'rb') as f:
        font_bytes = f.read()
    registered_font_name_bytes = client.register_font(font_bytes)

    # Create another Font object using the bytes-registered font
    jetbrains_font_bytes = Font(registered_font_name_bytes, 16.0)


# noinspection PyUnusedLocal
def image_operations(client):
    """Test image handling operations using logo-80.png."""
    # Load actual image file
    image_path = Path("tests/fixtures/logo-80.png")
    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    # Create image object with real image data
    logo_image = Image(
        position=Position.at_page_coordinates(0, 200, 400),
        format="image/png",
        width=80.0,
        height=80.0,
        data=image_bytes
    )

    # Add image to PDF
    client._add_image(logo_image)

    # Find images in document
    found_images = client._find_images()

    # Demonstrate image manipulation if images are found
    if found_images:
        first_image = found_images[0]

        # Get image properties via ObjectRef
        image_id = first_image.get_internal_id()
        image_type = first_image.get_type()
        image_position = first_image.get_position()

        # Move image to a new position
        new_image_position = Position.at_page_coordinates(0, 250, 450)
        client._move(first_image, new_image_position)


# noinspection PyUnusedLocal
def objectref_operations(client, paragraphs):
    """Test ObjectRef operations."""
    if paragraphs and len(paragraphs) > 1:  # Use remaining paragraphs after deletion
        obj_ref = paragraphs[1]
        internal_id = obj_ref.get_internal_id()
        obj_type = obj_ref.get_type()
        position = obj_ref.get_position()
        obj_dict = obj_ref.to_dict()

        # Set new position
        new_ref_position = Position.at_page_coordinates(0, 75, 125)
        obj_ref.set_position(new_ref_position)
        updated_position = obj_ref.get_position()


# noinspection PyUnusedLocal
def enumerations(client):
    """Test enumeration demonstrations."""
    object_types = list(ObjectType)
    position_modes = list(PositionMode)
    shape_types = list(ShapeType)


# noinspection PyUnusedLocal
def error_handling(client):
    """Test error handling demonstration."""
    exception_caught = None
    try:
        # This might trigger a font not found error
        client.find_fonts("NonExistentFont", 12)
    except FontNotFoundException as e:
        exception_caught = e
    except Exception as e:
        exception_caught = e


# noinspection PyUnusedLocal
def pdf_operations(client):
    """Test PDF operations."""
    # Get PDF data
    pdf_data = client.get_pdf_file()

    # Save PDF (original functionality + comprehensive output)
    output_path = "comprehensive_output.pdf"
    client.save_pdf(output_path)
    client.save_pdf("output.pdf")  # Keep original output file

    # Verify file exists
    file_exists = Path(output_path).exists()
    file_size = Path(output_path).stat().st_size if file_exists else 0


def context_management():
    """Test context manager capabilities."""
    with open("jwt-token-mlahr-20250829-160417.txt", "r", encoding="utf-8") as f:
        token = f.read()

        # Context manager automatically handles session lifecycle
        with ClientV1(token=token, pdf_data="tests/fixtures/ObviouslyAwesome.pdf") as client:
            paragraphs = client.find_paragraphs()

            # Builder pattern works seamlessly inside context (original functionality preserved)
            paragraph = (client.paragraph_builder()
                         .from_string("Context managed")
                         .with_font(Font("Arial", 12))
                         .with_position(Position.at_page_coordinates(0, 50, 10))
                         .build())

            client._add_paragraph(paragraph)

            return len(paragraphs)


def advanced_positioning():
    """Test advanced positioning features."""
    # Create positions using different methods
    positions = [
        Position.at_page(0),
        Position.at_page_coordinates(1, 100, 200),
        Position.at_page_coordinates(2, 150, 250)
    ]

    modified_positions = []
    for pos in positions:
        # Demonstrate position copying and modification
        copied_pos = pos.copy()
        copied_pos.move_x(25).move_y(35)
        modified_positions.append(copied_pos)

    return positions, modified_positions


def main():
    """Main function demonstrating all API features."""
    with open("jwt-token-mlahr-20250829-160417.txt", "r", encoding="utf-8") as f:
        token = f.read()

        with ClientV1(token=token, pdf_data="tests/fixtures/ObviouslyAwesome.pdf", read_timeout=30.0) as client:
            # Execute all test operations
            paragraphs, text_lines = find_operations(client)
            page_management(client)
            position_system(client)
            font_management(client)
            register_font_operations(client)
            color_system(client)
            paragraph_operations(client)
            object_manipulation(client, paragraphs, text_lines)
            text_line_operations(client)
            form_operations(client)
            path_operations(client)
            image_operations(client)
            objectref_operations(client, paragraphs)
            enumerations(client)
            error_handling(client)
            pdf_operations(client)


if __name__ == "__main__":
    main()
    context_management()
    advanced_positioning()
