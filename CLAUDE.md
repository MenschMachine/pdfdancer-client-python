# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the PDFDancer Python client.

## Project Overview

This is a **Python client library** for the PDFDancer PDF manipulation API. It uses a **100% manual implementation**
that:

- **Mirrors Java client structure exactly** - Same methods, validation, and patterns
- **Pure Python implementation** - Uses `requests` for HTTP calls, no code generation
- **Pythonic conventions** - Snake_case methods, type hints, context managers
- **Strict validation** - Matches Java client validation exactly

## Essential Commands

### Development

- `python -m venv venv` - Create virtual environment
- `venv/bin/pip install -e .` - Install in development mode
- `venv/bin/pip install -r requirements-dev.txt` - Install dev dependencies

### Testing

- `venv/bin/python -m pytest tests/ -v` - Run all tests (123 tests)
- `venv/bin/python -m pytest tests/e2e/ -v` - Run end-to-end tests
- `venv/bin/python -m pytest tests/test_models.py -v` - Run model tests

### Building & Publishing

- `venv/bin/python -m build` - Build distribution packages
- `venv/bin/python -m twine check dist/*` - Validate packages
- `venv/bin/python -m twine upload dist/*` - Publish to PyPI

## Architecture

### Manual Implementation

The client is a pure manual implementation that closely mirrors the Java client:

```python
# Open existing PDF
pdf = PDFDancer.open(pdf_data="document.pdf")

# Create new blank PDF
pdf = PDFDancer.new(page_size=PageSize.A4, orientation=Orientation.PORTRAIT)

# Select and manipulate objects
paragraphs = pdf.select_paragraphs()
paragraphs[0].delete()

images = pdf.select_images()
images[0].move(Position.at_page_coordinates(0, 100, 200))

# Page-level operations
page = pdf.page(0)
page_paragraphs = page.select_paragraphs()
page.delete()

# Builder pattern for new content
pdf.new_paragraph()
    .from_string("Text content")
    .with_font(Font("Arial", 12))
    .at_page_coordinates(0, 100, 200)
    .add()

# Save modified PDF
pdf.save("output.pdf")
```

### Package Structure

- `src/pdfdancer/` - Main package
    - `pdfdancer_v1.py` - Main PDFDancer class and PageClient
    - `paragraph_builder.py` - ParagraphBuilder and ParagraphPageBuilder for fluent construction
    - `image_builder.py` - ImageBuilder for fluent image construction
    - `models.py` - Model classes (ObjectRef, Position, Font, Color, etc.)
    - `types.py` - Object wrapper types (ParagraphObject, ImageObject, etc.)
    - `exceptions.py` - Exception hierarchy

### Key Features

- **Dual initialization**: `PDFDancer.open()` for existing PDFs, `PDFDancer.new()` for blank PDFs
- **Session-based operations**: All constructors create server session automatically
- **Object-oriented API**: Selected objects (paragraphs, images, etc.) have methods like `.delete()`, `.move()`
- **Page-level operations**: `pdf.page(number)` provides page-scoped selections and operations
- **Builder pattern**: `new_paragraph()` and `new_image()` for fluent construction
- **Strict validation**: All validation matches Java client exactly
- **Exception handling**: FontNotFoundException, ValidationException, HttpClientException, etc.
- **Type safety**: Full type hints throughout
- **E2E testing utilities**: PDFAssertions for comprehensive PDF validation

## API Patterns

### Initialization

```python
# Open existing PDF with token from env var PDFDANCER_TOKEN
pdf = PDFDancer.open(pdf_data="document.pdf")

# Open with explicit token
pdf = PDFDancer.open(pdf_data="document.pdf", token="your-token")

# Create new blank PDF
pdf = PDFDancer.new(
    page_size=PageSize.A4,
    orientation=Orientation.PORTRAIT,
    initial_page_count=5
)
```

### Selection and Manipulation

```python
# Document-level selections
paragraphs = pdf.select_paragraphs()
images = pdf.select_images()
form_fields = pdf.select_form_fields_by_name("fieldName")

# Page-level selections
page = pdf.page(0)
page_paragraphs = page.select_paragraphs_starting_with("Invoice")
page_images = page.select_images_at(100, 200)

# Object manipulation
paragraphs[0].delete()
paragraphs[0].move(Position.at_page_coordinates(1, 50, 50))
paragraphs[0].modify("New text content")

# Pattern-based selections
paragraphs = page.select_paragraphs_matching(r"\d{4}-\d{2}-\d{2}")
text_lines = page.select_text_lines_matching(r"Total: \$\d+")
```

### Building New Content

```python
# Add paragraph to document
pdf.new_paragraph()
    .from_string("Hello World")
    .with_font(Font("Helvetica", 12))
    .with_color(Color(255, 0, 0))
    .at_page_coordinates(0, 100, 200)
    .add()

# Add paragraph to specific page
page.new_paragraph()
    .from_string("Page-specific text")
    .with_font(Font("Arial", 14))
    .at_coordinates(50, 50)
    .add()

# Add image
pdf.new_image()
    .from_file("logo.png")
    .with_width(100)
    .at_page_coordinates(0, 50, 50)
    .add()
```

### Document Operations

```python
# Get PDF bytes
pdf_bytes = pdf.get_bytes()

# Save to file
pdf.save("output.pdf")

# Page operations
pages = pdf.pages()
page = pdf.page(0)
page.delete()
```

## Development Notes

- **Python 3.10+ compatibility** (Python 3.9 has SSL issues with large file uploads)
- **Uses `requests` library** for all HTTP communication
- **No code generation** - pure manual implementation
- **Virtual environment auto-setup** via parent Makefile
- **No code formatter configured** - follow existing style
- **Comprehensive tests** - 123 tests covering all functionality
- **E2E test utilities** - `tests/e2e/pdf_assertions.py` provides PDFAssertions class

## Important Instructions

### API Design

- **Use object-oriented patterns**: Selected objects should have methods (`.delete()`, `.move()`, etc.)
- **Provide page-level operations**: `pdf.page(number)` for page-scoped selections
- **Support fluent builders**: `new_paragraph()` and `new_image()` return builder instances
- **Use snake_case for methods**: `select_paragraphs()`, `select_images_at()`, etc.

### Validation and Exceptions

- **Maintain strict validation**: Don't be more lenient than Java client
- **Preserve exception hierarchy**: ValidationException, FontNotFoundException, HttpClientException, etc.
- **Validate early**: Check parameters in Python before making API calls

### Testing

- **Follow e2e test patterns**: Use PDFAssertions for comprehensive validation
- **Test both document and page operations**: Cover both `pdf.select_*()` and `page.select_*()` patterns
- **Test builder patterns**: Verify fluent interfaces work correctly
- **Always run tests after changes**: `venv/bin/python -m pytest tests/ -v`
