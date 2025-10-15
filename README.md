# PDFDancer Python Client

A Python client library for the PDFDancer PDF manipulation API that closely mirrors the Java client structure and functionality.

## Features

- **100% Manual Implementation** - Pure Python, no code generation
- **Java Client Compatibility** - Same methods, validation, and patterns
- **Session-based Operations** - Automatic session management
- **Builder Pattern** - Fluent ParagraphBuilder interface
- **Strict Validation** - Matches Java client validation exactly
- **Python Enhancements** - Type hints, context managers, Pathlib support
- **Comprehensive Testing** - 77 tests covering all functionality

## Installation

```bash
pip install pdfdancer-client-python
# Or for development:
pip install -e .
```

## Quick Start

```python
from pdfdancer import ClientV1, Position, Font, Color

# Create client (mirrors Java: new Client(token, pdfFile))
client = ClientV1(token="your-jwt-token", pdf_data="document.pdf")

# Find operations (mirrors Java client methods)
paragraphs = client.find_paragraphs(None)
images = client.find_images(Position.at_page(0))

# Manipulation operations (mirrors Java client methods)
client._delete(paragraphs[0])
client._move(images[0], Position.at_page_coordinates(0, 100, 200))

# Builder pattern (mirrors Java ParagraphBuilder)
paragraph = (client._paragraph_builder()
             .from_string("Hello World")
             .with_font(Font("Arial", 12))
             .with_color(Color(255, 0, 0))
             .with_position(Position.at_page(0))
             .build())

client._add_paragraph(paragraph)

# Save result (mirrors Java savePDF)
client.save_pdf("output.pdf")
```

## Context Manager (Python Enhancement)

```python
from pdfdancer import ClientV1

# Automatic resource management
with ClientV1(token="jwt-token", pdf_data="input.pdf") as client:
    paragraphs = client.find_paragraphs(None)
    client._delete(paragraphs[0])
    client.save_pdf("output.pdf")
    # Session automatically cleaned up
```

## API Methods

### Constructor Patterns
```python
# File path (Java: new Client(token, new File("pdf")))
client = ClientV1(token="jwt-token", pdf_data="document.pdf")

# Bytes (Java: new Client(token, pdfBytes, httpClient))
client = ClientV1(token="jwt-token", pdf_data=pdf_bytes)

# Custom server
client = ClientV1(token="jwt-token", pdf_data=pdf_file, base_url="https://api.server")
```

### Find Operations

```python
# Generic find (Java: client.find())
objects = client._find(ObjectType.PARAGRAPH, position)

# Specific finders (Java: client.findParagraphs(), etc.)
paragraphs = client._find_paragraphs(position)
images = client._find_images(position)
forms = client._find_form_x_objects(position)
paths = client._find_paths(position)
text_lines = client._find_text_lines(position)

# Page operations (Java: client.getPages(), client.getPage())
pages = client.get_pages()
page = client._get_page(1)  # 1-based indexing
```

### Manipulation Operations

```python
# Delete (Java: client.delete(), client.deletePage())
result = client._delete(object_ref)
result = client._delete_page(page_ref)

# Move (Java: client.move())
result = client._move(object_ref, new_position)

# Add (Java: client.addImage(), client.addParagraph())
result = client._add_image(image, position)
result = client._add_paragraph(paragraph)

# Modify (Java: client.modifyParagraph(), client.modifyTextLine())
result = client._modify_paragraph(ref, new_paragraph)
result = client.modify_text_line(ref, "new text")
```

### Builder Pattern

```python
# Java: client.paragraphBuilder()
builder = client._paragraph_builder()

# Fluent interface (mirrors Java ParagraphBuilder)
paragraph = (builder
             .from_string("Text content")  # Java: fromString()
             .with_font(Font("Arial", 12))  # Java: withFont()
             .with_color(Color(255, 0, 0))  # Java: withColor()
             .with_line_spacing(1.5)  # Java: withLineSpacing()
             .with_position(position)  # Java: withPosition()
             .build())  # Java: build()

# Font file registration (Java: withFont(File, double))
paragraph = (builder
             .with_font_file("custom.ttf", 14.0)  # Java: withFont(File, double)
             .from_string("Custom font text")
             .with_position(position)
             .build())
```

### Position API

```python
from pdfdancer import Position

# Factory methods (Java: Position.fromPageNumber(), Position.onPageCoordinates())
position = Position.at_page(0)
position = Position.at_page_coordinates(0, 100, 200)

# Coordinate access (Java: position.getX(), position.getY())
x = position.x()
y = position.y()

# Movement (Java: position.moveX(), position.moveY())
position.move_x(50.0)
position.move_y(-25.0)

# Copy (Java: position.copy())
position_copy = position.copy()
```

### Font Operations
```python
# Find fonts (Java: client.findFonts())
fonts = client.find_fonts("Arial", 12)

# Register custom font (Java: client.registerFont())
font_name = client.register_font("custom.ttf")
font_name = client.register_font(Path("font.ttf"))
font_name = client.register_font(font_bytes)
```

### Document Operations
```python
# Get PDF content (Java: client.getPDFFile())
pdf_bytes = client.get_pdf_file()

# Save PDF (Java: client.savePDF())
client.save_pdf("output.pdf")
client.save_pdf(Path("output.pdf"))
```

## Exception Handling

```python
from pdfdancer import (
    PdfDancerException, ValidationException,
    FontNotFoundException, HttpClientException
)

try:
    client = ClientV1(token="", pdf_data=b"pdf")
except ValidationException as e:  # Java: IllegalArgumentException
    print(f"Validation error: {e}")

try:
    fonts = client.find_fonts("NonExistentFont", 12)
except FontNotFoundException as e:  # Java: FontNotFoundException
    print(f"Font not found: {e}")
```

## Data Models

```python
from pdfdancer import ObjectRef, Position, Font, Color, ObjectType

# Object reference (Java: ObjectRef)
obj_ref = ObjectRef(internal_id="obj-123", position=position, type=ObjectType.PARAGRAPH)

# Font (Java: Font)
font = Font(name="Arial", size=12.0)

# Color (Java: Color) - RGB values 0-255
color = Color(r=255, g=128, b=0)

# Position with bounding rectangle (Java: Position, BoundingRect)
position = Position.at_page_coordinates(page=0, x=100.0, y=200.0)
```

## Development

### Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
pip install -r requirements-dev.txt
```

### Testing
```bash
# Run all tests (77 tests)
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_client_v1.py -v
python -m pytest tests/test_paragraph_builder.py -v
python -m pytest tests/test_models.py -v
```

### Build Package
```bash
python -m build
python -m twine check dist/*
```

## Java Client Mapping

| Java Method | Python Method | Description |
|-------------|---------------|-------------|
| `new Client(token, file)` | `ClientV1(token="", pdf_data="")` | Constructor |
| `findParagraphs(position)` | `find_paragraphs(position)` | Find paragraphs |
| `findImages(position)` | `find_images(position)` | Find images |
| `delete(objectRef)` | `delete(object_ref)` | Delete object |
| `move(objectRef, position)` | `move(object_ref, position)` | Move object |
| `addParagraph(paragraph)` | `add_paragraph(paragraph)` | Add paragraph |
| `getPDFFile()` | `get_pdf_file()` | Get PDF bytes |
| `savePDF(path)` | `save_pdf(path)` | Save to file |
| `paragraphBuilder()` | `paragraph_builder()` | Create builder |
| `findFonts(name, size)` | `find_fonts(name, size)` | Find fonts |
| `registerFont(ttfFile)` | `register_font(ttf_file)` | Register font |

## Architecture

- **Pure Manual Implementation** - No code generation, uses `requests` for HTTP
- **Session-based** - Constructor creates session, all operations use session ID
- **Strict Validation** - Matches Java client validation exactly
- **Type Safety** - Full type hints throughout
- **Error Handling** - Complete exception hierarchy
- **Python Conventions** - snake_case methods, context managers, Pathlib support

## Requirements

- Python 3.8+
- `requests` library for HTTP communication
- `pathlib` for file handling (built-in)

## License

[Add your license information here]