# PDFDancer Python Client

![PDFDancer logo](media/logo-orange-60h.webp)

**Stop fighting PDFs. Start editing them.**

Edit text in real-world PDFs—even ones you didn't create. Move images, reposition headers, and change fonts with
pixel-perfect control from Python. The same API is also available for TypeScript and Java.

> Need the raw API schema? The latest OpenAPI description lives in `docs/openapi.yml` and is published at
> https://bucket.pdfdancer.com/api-doc/development-0.0.yml.

## Highlights

- Locate paragraphs, text lines, images, vector paths, form fields, and pages by index, coordinates, or text prefixes.
- Edit existing content in place with fluent editors and context managers that apply changes safely.
- Programmatically control third-party PDFs—modify invoices, contracts, and reports you did not author.
- Add content with precise XY positioning using paragraph and image builders, custom fonts, and color helpers.
- Export results as bytes for downstream processing or save directly to disk with one call.

## What Makes PDFDancer Different

- **Edit text in real-world PDFs**: Work with documents from customers, governments, or vendors—even ones you didn't create.
- **Pixel-perfect positioning**: Move or add elements at exact coordinates and keep the original layout intact.
- **Surgical text replacement**: Swap or rewrite paragraphs without reflowing the rest of the page.
- **Form manipulation**: Inspect, fill, and update AcroForm fields programmatically.
- **Coordinate-based selection**: Select objects by position, bounding box, or text patterns.
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
        .at(page_index=0, x=72, y=520) \
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
        .at(page_index=0, x=72, y=730) \
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
with helpers such as `delete()`, `move_to(x, y)`, or `edit()` depending on the object type.

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
cd pdfdancer-client-python/_main
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
pdfdancer-client-python/_main/
├── src/pdfdancer/          # Main package source
│   ├── __init__.py         # Package exports
│   ├── pdfdancer_v1.py     # Core PDFDancer and PageClient classes
│   ├── paragraph_builder.py # Fluent paragraph builders
│   ├── image_builder.py    # Fluent image builders
│   ├── models.py           # Data models (Position, Font, Color, etc.)
│   ├── types.py            # Object wrappers (ParagraphObject, etc.)
│   └── exceptions.py       # Exception hierarchy
├── tests/                  # Test suite
│   ├── test_models.py      # Model unit tests
│   ├── e2e/                # End-to-end integration tests
│   └── fixtures/           # Test fixtures and sample PDFs
├── docs/                   # Documentation
├── dist/                   # Build artifacts (created after packaging)
├── logs/                   # Local execution logs (ignored in VCS)
├── pyproject.toml          # Project metadata and dependencies
├── release.py              # Helper for publishing releases
└── README.md               # This file
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
