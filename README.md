# PDFDancer Python Client

![PDFDancer logo](media/logo-orange-60h.webp)

**Stop fighting PDFs. Start editing them.**

Edit text in real-world PDFs—even ones you didn't create. Move images, reposition headers, and change fonts with
pixel-perfect control from Python. The same API is also available for TypeScript and Java.

> Need the raw API schema? The latest OpenAPI description lives in `docs/openapi.yml` and is published at
> https://bucket.pdfdancer.com/api-doc/development-0.0.yml.

## Highlights

- Locate paragraphs, text lines, images, vector paths, form fields, and pages by page number, coordinates, or text patterns.
- Edit existing content in place with fluent editors and context managers that apply changes safely.
- Programmatically control third-party PDFs—modify invoices, contracts, and reports you did not author.
- Add content with precise XY positioning using paragraph, image, and vector path builders with custom fonts and colors.
- Draw lines, rectangles, and Bezier curves with configurable stroke width, dash patterns, and fill colors.
- Redact sensitive content—replace text, images, or form fields with customizable placeholders.
- Export results as bytes for downstream processing or save directly to disk with one call.

## What Makes PDFDancer Different

- **Edit text in real-world PDFs**: Work with documents from customers, governments, or vendors—even ones you didn't create.
- **Pixel-perfect positioning**: Move or add elements at exact coordinates and keep the original layout intact.
- **Surgical text replacement**: Swap or rewrite paragraphs without reflowing the rest of the page.
- **Form manipulation**: Inspect, fill, and update AcroForm fields programmatically.
- **Coordinate-based selection**: Select objects by position, bounding box, or text patterns.
- **Vector graphics**: Draw lines, rectangles, and Bezier curves with full control over stroke and fill properties.
- **Secure redaction**: Permanently remove sensitive content and replace with customizable markers.
- **Real PDF editing**: Modify the underlying PDF structure instead of merely stamping overlays.

## Installation

```bash
pip install pdfdancer-client-python

# Editable install for local development
pip install -e .
```

Requires Python 3.10+ and a PDFDancer API token.

## Quick Start — Edit an Existing PDF

```python
from pathlib import Path
from pdfdancer import Color, PDFDancer, StandardFonts

with PDFDancer.open(
    pdf_data=Path("input.pdf"),
    token="your-api-token",             # optional when PDFDANCER_TOKEN is set
    base_url="https://api.pdfdancer.com",
) as pdf:
    # Locate and update an existing paragraph
    heading = pdf.page(0).select_paragraphs_starting_with("Executive Summary")[0]
    heading.move_to(72, 680)
    with heading.edit() as editor:
        editor.replace("Overview")

    # Add a new paragraph with precise placement
    pdf.new_paragraph() \
        .text("Generated with PDFDancer") \
        .font(StandardFonts.HELVETICA, 12) \
        .color(Color(70, 70, 70)) \
        .line_spacing(1.4) \
        .at(page_number=1, x=72, y=520) \
        .add()

    # Persist the modified document
    pdf.save("output.pdf")
    # or keep it in memory
    pdf_bytes = pdf.get_bytes()
```

## Create a Blank PDF

```python
from pathlib import Path
from pdfdancer import Color, PDFDancer, StandardFonts

with PDFDancer.new(token="your-api-token") as pdf:
    pdf.new_paragraph() \
        .text("Quarterly Summary") \
        .font(StandardFonts.TIMES_BOLD, 18) \
        .color(Color(10, 10, 80)) \
        .line_spacing(1.2) \
        .at(page_number=1, x=72, y=730) \
        .add()

    pdf.new_image() \
        .from_file(Path("logo.png")) \
        .at(page=0, x=420, y=710) \
        .add()

    pdf.save("summary.pdf")
```

## Work with Forms and Layout

```python
from pdfdancer import PDFDancer

with PDFDancer.open("contract.pdf") as pdf:
    # Inspect global document structure
    pages = pdf.pages()
    print("Total pages:", len(pages))

    # Update form fields
    signature = pdf.select_form_fields_by_name("signature")[0]
    signature.edit().value("Signed by Jane Doe").apply()

    # Trim or move content at specific coordinates
    images = pdf.page(1).select_images()
    for image in images:
        x = image.position.x()
        if x is not None and x < 100:
            image.delete()
```

Selectors return typed objects (`ParagraphObject`, `TextLineObject`, `ImageObject`, `FormFieldObject`, `PageClient`, …)
with helpers such as `delete()`, `move_to(x, y)`, `redact()`, or `edit()` depending on the object type.

**Singular selection methods** return the first match (or `None`) for convenience:

```python
# Instead of: paragraphs = page.select_paragraphs_starting_with("Invoice")[0]
paragraph = page.select_paragraph_starting_with("Invoice")  # Returns first match or None
image = page.select_image_at(100, 200)                      # Returns first match or None
field = pdf.select_form_field_by_name("email")              # Returns first match or None
```

## Draw Vector Paths

Add lines, curves, and shapes to your PDFs with fluent builders:

```python
from pdfdancer import PDFDancer, Color, Point

with PDFDancer.open("document.pdf") as pdf:
    page = pdf.page(0)

    # Draw a simple line
    page.new_line() \
        .from_point(100, 700) \
        .to_point(500, 700) \
        .stroke_color(Color(0, 0, 255)) \
        .stroke_width(2.0) \
        .add()

    # Draw a rectangle
    page.new_rectangle() \
        .at_coordinates(100, 500) \
        .with_size(200, 100) \
        .stroke_color(Color(0, 0, 0)) \
        .fill_color(Color(255, 255, 200)) \
        .add()

    # Draw a bezier curve
    page.new_bezier() \
        .from_point(100, 400) \
        .control_point_1(150, 450) \
        .control_point_2(250, 350) \
        .to_point(300, 400) \
        .stroke_width(1.5) \
        .add()

    # Build complex paths with multiple segments
    page.new_path() \
        .stroke_color(Color(255, 0, 0)) \
        .add_line(Point(50, 200), Point(150, 200)) \
        .add_line(Point(150, 200), Point(100, 280)) \
        .add_line(Point(100, 280), Point(50, 200)) \
        .add()

    pdf.save("annotated.pdf")
```

## Redact Sensitive Content

Remove text, images, or form fields and replace them with redaction markers:

```python
from pdfdancer import PDFDancer, Color

with PDFDancer.open("confidential.pdf") as pdf:
    # Redact paragraphs containing sensitive patterns
    for para in pdf.select_paragraphs():
        if "SSN:" in para.text or "Password:" in para.text:
            para.redact("[REDACTED]")

    # Redact all images on a specific page
    for image in pdf.page(0).select_images():
        image.redact()

    # Bulk redact multiple objects with custom placeholder color
    form_fields = pdf.select_form_fields_by_name("credit_card")
    result = pdf.redact(form_fields, replacement="[REMOVED]", placeholder_color=Color(0, 0, 0))
    print(f"Redacted {result.count} items")

    pdf.save("redacted.pdf")
```

## Configuration

- Set `PDFDANCER_TOKEN` for authentication (preferred for local development and CI).
- Override the API host with `PDFDANCER_BASE_URL` (e.g., sandbox or local environments). Defaults to `https://api.pdfdancer.com`.
- Tune HTTP read timeouts via the `timeout` argument on `PDFDancer.open()` and `PDFDancer.new()` (default: 30 seconds).
- For testing against self-signed certificates, call `pdfdancer.set_ssl_verify(False)` to temporarily disable TLS verification.

## Error Handling

Operations raise subclasses of `PdfDancerException`:

- `ValidationException`: input validation problems (missing token, invalid coordinates, etc.).
- `FontNotFoundException`: requested font unavailable on the service.
- `HttpClientException`: transport or server errors with detailed context.
- `SessionException`: session creation and lifecycle failures.
- `RateLimitException`: API rate limit exceeded; includes retry-after timing.

Wrap automated workflows in `try/except` blocks to surface actionable errors to your users.

## Development Setup

### Prerequisites

- **Python 3.10 or higher** (Python 3.9 has SSL issues with large file uploads)
- **Git** for cloning the repository
- **PDFDancer API token** for running end-to-end tests

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/MenschMachine/pdfdancer-client-python.git
cd pdfdancer-client-python
```

#### 2. Create a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt indicating the virtual environment is active.

#### 3. Install Dependencies

```bash
# Install the package in editable mode with development dependencies
pip install -e ".[dev]"

# Alternatively, install runtime dependencies only:
# pip install -e .
```

This installs:
- The `pdfdancer` package in editable mode (changes reflect immediately)
- Development tooling including `pytest`, `pytest-cov`, `pytest-mock`, `black`, `isort`, `flake8`, `mypy`, `build`, and `twine`.

#### 4. Configure API Token

Set your PDFDancer API token as an environment variable:

```bash
# On macOS/Linux:
export PDFDANCER_TOKEN="your-api-token-here"

# On Windows (Command Prompt):
set PDFDANCER_TOKEN=your-api-token-here

# On Windows (PowerShell):
$env:PDFDANCER_TOKEN="your-api-token-here"
```

For permanent configuration, add this to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.).

#### 5. Verify Installation

```bash
# Run the test suite
pytest tests/ -v

# Run only unit tests (faster)
pytest tests/test_models.py -v

# Run end-to-end tests (requires API token)
pytest tests/e2e/ -v
```

All tests should pass if everything is set up correctly.

### Common Development Tasks

#### Running Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v

# Run end-to-end tests only
pytest tests/e2e/ -v

# Run with coverage report
pytest tests/ --cov=pdfdancer --cov-report=term-missing
```

#### Building Distribution Packages

```bash
# Build wheel and source distribution
python -m build

# Verify the built packages
python -m twine check dist/*
```

Artifacts will be created in the `dist/` directory.

#### Publishing to PyPI

```bash
# Test upload to TestPyPI (recommended first)
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*

# Or use the release script
python release.py
```

#### Code Quality

```bash
# Format code
black src tests
isort src tests

# Lint
flake8 src tests

# Type checking
mypy src/pdfdancer/
```

### Project Structure

```
pdfdancer-client-python/
├── src/pdfdancer/           # Main package source
│   ├── __init__.py          # Package exports
│   ├── pdfdancer_v1.py      # Core PDFDancer and PageClient classes
│   ├── paragraph_builder.py # Fluent paragraph builders
│   ├── text_line_builder.py # Fluent text line builders
│   ├── image_builder.py     # Fluent image builders
│   ├── path_builder.py      # Vector path builders (lines, beziers, rectangles)
│   ├── page_builder.py      # Page creation builder
│   ├── models.py            # Data models (Position, Font, Color, etc.)
│   ├── types.py             # Object wrappers (ParagraphObject, etc.)
│   └── exceptions.py        # Exception hierarchy
├── tests/                   # Test suite
│   ├── test_models.py       # Model unit tests
│   ├── e2e/                 # End-to-end integration tests
│   └── fixtures/            # Test fixtures and sample PDFs
├── docs/                    # Documentation
├── dist/                    # Build artifacts (created after packaging)
├── pyproject.toml           # Project metadata and dependencies
├── release.py               # Helper for publishing releases
└── README.md                # This file
```

### Troubleshooting

#### Virtual Environment Issues

If `python -m venv venv` fails, ensure you have the `venv` module:

```bash
# On Ubuntu/Debian
sudo apt-get install python3-venv

# On macOS (using Homebrew)
brew install python@3.10
```

#### SSL Errors with Large Files

Upgrade to Python 3.10+ if you encounter SSL errors during large file uploads.

#### Import Errors

Ensure the virtual environment is activated and the package is installed in editable mode:

```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .
```

#### Test Failures

- Ensure `PDFDANCER_TOKEN` is set for e2e tests
- Check network connectivity to the PDFDancer API
- Verify you're using Python 3.10 or higher

### Contributing

Contributions are welcome via pull request. Please:

1. Create a feature branch from `main`
2. Add tests for new functionality
3. Ensure all tests pass: `pytest tests/ -v`
4. Follow existing code style and patterns
5. Update documentation as needed

## Related SDKs

- TypeScript client: https://github.com/MenschMachine/pdfdancer-client-js
- Java client: https://github.com/MenschMachine/pdfdancer-client-java

## License

Apache License 2.0 © 2025 The Famous Cat Ltd. See `LICENSE` and `NOTICE` for details.
