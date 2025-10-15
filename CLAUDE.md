# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the PDFDancer Python client.

## Project Overview

This is a **Python client library** for the PDFDancer PDF manipulation API. It uses a **100% manual implementation** that:

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
- `venv/bin/python -m pytest tests/ -v` - Run all tests (77 tests)
- `venv/bin/python -m pytest tests/test_client_v1.py -v` - Run client tests
- `venv/bin/python -m pytest tests/test_paragraph_builder.py -v` - Run builder tests

### Building & Publishing
- `venv/bin/python -m build` - Build distribution packages
- `venv/bin/python -m twine check dist/*` - Validate packages
- `venv/bin/python -m twine upload dist/*` - Publish to PyPI

## Architecture

### Manual Implementation
The client is a pure manual implementation that closely mirrors the Java client:

```python
# Java-like API with Python conventions
client = ClientV1(token="jwt-token", pdf_data="document.pdf")

# Find operations (mirrors Java findParagraphs, findImages, etc.)
paragraphs = client._find_paragraphs(position)
images = client._find_images(position)

# Manipulation operations (mirrors Java delete, move, etc.)
client._delete(paragraphs[0])
client._move(images[0], new_position)

# Builder pattern (mirrors Java ParagraphBuilder)
paragraph = (client._paragraph_builder()
             .from_string("Text content")
             .with_font(Font("Arial", 12))
             .with_position(Position.at_page_coordinates(0, 100, 200))
             .build())

# Context manager support (Python enhancement)
with ClientV1(token="jwt-token", pdf_data=pdf_file) as client:
    client.save_pdf("output.pdf")
```

### Package Structure
- `src/pdfdancer/` - Main package
  - `client_v1.py` - Main ClientV1 class (mirrors Java Client class)
  - `paragraph_builder.py` - ParagraphBuilder for fluent construction
  - `models.py` - All model classes (ObjectRef, Position, Font, etc.)
  - `exceptions.py` - Exception hierarchy matching Java client

### Key Features
- **Session-based operations**: Constructor creates session automatically
- **Strict validation**: All validation matches Java client exactly
- **Builder pattern**: ParagraphBuilder with fluent interface
- **Exception handling**: FontNotFoundException, ValidationException, etc.
- **Type safety**: Full type hints throughout
- **Context manager**: Python enhancement for resource management

## Java Client Mapping

### Constructor Patterns
```python
# Java: new Client(token, pdfFile)
client = ClientV1(token="jwt-token", pdf_data="document.pdf")

# Java: new Client(token, bytesPDF, httpClient)
client = ClientV1(token="jwt-token", pdf_data=pdf_bytes, base_url="http://api.server")
```

### Method Mapping
- `find()` → `find()`
- `findParagraphs()` → `find_paragraphs()`
- `findImages()` → `find_images()`
- `delete()` → `delete()`
- `move()` → `move()`
- `addParagraph()` → `add_paragraph()`
- `getPDFFile()` → `get_pdf_file()`
- `savePDF()` → `save_pdf()`
- `paragraphBuilder()` → `paragraph_builder()`

### Validation Matching
All validation matches Java client exactly:
- Null checks become None checks
- IllegalArgumentException becomes ValidationException
- FontNotFoundException preserved exactly
- Page number validation (must be positive)
- File existence and readability checks

## Development Notes

- **Python 3.8+ compatibility**
- **Uses `requests` library** for all HTTP communication
- **No code generation** - pure manual implementation
- **Virtual environment auto-setup** via parent Makefile
- **No code formatter configured** - follow existing style
- **Comprehensive tests** - 77 tests covering all functionality

## Important Instructions

- **ALWAYS mirror Java client behavior exactly** - same validation, same patterns
- **Use snake_case for method names** but preserve Java logic
- **Maintain strict validation** - don't be more lenient than Java client
- **Follow existing test patterns** when adding new functionality
- **Keep exception hierarchy matching Java client**
- **Preserve builder pattern fluent interface**