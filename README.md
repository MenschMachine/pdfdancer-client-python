# PDFDancer Python Client

![PDFDancer logo](media/logo-silver-60h.webp)

## Overview

### PDF used to be read-only. We fixed that.

Edit text in real-world PDFs—even ones you didn't create. Move images, reposition headers, and change fonts with
pixel-perfect control from Python. The same API is also available for TypeScript and Java.

### What Makes PDFDancer Different

- **Edit text in real-world PDFs**: Work with documents from customers, governments, or vendors—even ones you didn't create.
- **Pixel-perfect positioning**: Move or add elements at exact coordinates and keep the original layout intact.
- **Selector-based text editing**: Apply literal or regular-expression replacements with page scoping and explicit layout policy.
- **Form manipulation**: Inspect, fill, and update AcroForm fields programmatically.
- **Coordinate-based selection**: Select objects by position, bounding box, or text patterns.
- **Vector graphics**: Draw lines, rectangles, and Bezier curves with full control over stroke and fill properties.
- **Real PDF editing**: Modify the underlying PDF structure instead of merely stamping overlays.

## Highlights

- Replace, insert, delete, and style text with selector-based v2 operations.
- Locate images, vector paths, form fields, and pages by page number or coordinates; inspect text-line data through snapshots.
- Programmatically control third-party PDFs—modify invoices, contracts, and reports you did not author.
- Add images and vector paths with precise XY positioning.
- Draw lines, rectangles, and Bezier curves with configurable stroke width, dash patterns, and fill colors.
- Export results as bytes for downstream processing or save directly to disk with one call.

## Installation

```bash
pip install pdfdancer-client-python

# Editable install for local development
pip install -e .
```

## Requirements

- Python 3.10 or newer.
- A PDFDancer API token, supplied explicitly or through `PDFDANCER_API_TOKEN` or `PDFDANCER_TOKEN`.
- Access to the PDFDancer API host. The default is `https://api.pdfdancer.com`.

## Quick Start

### Edit an Existing PDF

```python
from pathlib import Path
from pdfdancer import PDFDancer, PdfColorRequest, TextReplaceRequest, TextStyleRequest

with PDFDancer.open(
    pdf_data=Path("input.pdf"),
    token="your-api-token",             # optional when PDFDANCER_API_TOKEN is set
    base_url="https://api.pdfdancer.com",
) as pdf:
    result = pdf.page(1).text().replace(
        TextReplaceRequest.literal("Executive Summary", "Overview").build()
    )
    assert result.changed == 1

    pdf.text().style(
        TextStyleRequest.literal("Overview")
        .fill_color(PdfColorRequest.rgb(0.2, 0.2, 0.6))
        .build()
    )

    # Persist the modified document
    pdf.save("output.pdf")
    # or keep it in memory
    pdf_bytes = pdf.get_bytes()
```

## Create a Blank PDF

```python
from pathlib import Path
from pdfdancer import PDFDancer

with PDFDancer.new(token="your-api-token") as pdf:
    pdf.new_image() \
        .from_file(Path("logo.png")) \
        .at(page=1, x=420, y=710) \
        .add()

    pdf.save("summary.pdf")
```

## Page API

Page numbers are 1-based. `pdf.page(1)` returns a page-scoped client, while `pdf.pages()` returns page clients for the
document. Use `get_snapshot()` on a page client for a read-only page snapshot.

```python
first_page = pdf.page(1)
pages = pdf.pages()
snapshot = first_page.get_snapshot()
```

Page-scoped selectors, text editing, and builders automatically restrict the operation to that page.

## Selection

Document- and page-scoped selectors return typed objects for images, paths, form XObjects, and form fields. Position
selectors use PDF coordinates and a default tolerance of `0.01` point. Singular selectors return the first match or
`None`; plural selectors return lists.

```python
document_images = pdf.select_images()
logo = pdf.page(1).select_image_at(72, 680)
page_paths = pdf.page(1).select_paths()
```

Document and page snapshots provide read-only text-line data. Use the selector-based text API for mutations.

## Builders and Vector Paths

All five dedicated builders are available at document and page scope: image, path, line, Bezier, and rectangle. Add
lines, curves, and shapes with fluent builders:

```python
from pdfdancer import PDFDancer, Color, Point

with PDFDancer.open("document.pdf") as pdf:
    page = pdf.page(1)

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

`PathBuilder` also provides cursor-based `move_to(...)`, `line_to(...)`, and `bezier_to(...)` operations plus
`close_path()`, `rectangle(...)`, `circle(...)`, and `solid()` conveniences. A circle is a `PathBuilder` convenience,
not a separate builder type.

## Images

Create images at document scope with an explicit page or directly from a page client:

```python
from pathlib import Path

pdf.new_image().from_file(Path("logo.png")).at(page=1, x=72, y=700).add()
pdf.page(1).new_image().from_file(Path("stamp.png")).at(x=300, y=700).add()
```

`ImageObject` exposes `width`, `height`, and `aspect_ratio`. It supports replacement from a filesystem path or `Image`,
proportional or explicit scaling, cropping, opacity, horizontal and vertical flips, region filling, and rotation.
Positive rotation angles are clockwise. Image transformations return `CommandResult`, which exposes `success`,
`message`, `warning`, and `element_id`.

## Form Fields

Form-field selection uses the same names at document and page scope. Mutate a selected field directly with
`set_value(...)`:

```python
signature = pdf.select_form_fields_by_name("signature")[0]
changed = signature.set_value("Signed by Jane Doe")
```

Selectors return typed objects (`ImageObject`, `FormFieldObject`, `PathObject`, `PageClient`, …) with generic helpers
such as `delete()`, `move_to(x, y)`, and `clear_clipping()` where supported by the selected object type.

## Text Editing

Text editing is selector-based and is available through `pdf.text()` and `pdf.page(page_number).text()`. It supports
replace, delete, insert, and style operations:

```python
from pdfdancer import TextDeleteRequest, TextInsertRequest, TextReplaceRequest

pdf.text().replace(
    TextReplaceRequest.literal("Old product", "New product")
    .whole_words(True)
    .max_matches(5)
    .build()
)

pdf.page(2).text().delete(
    TextDeleteRequest.regex(r"Confidential\s+draft")
    .case_sensitive(False)
    .build()
)

pdf.text().insert(
    TextInsertRequest.before("Terms", "Updated ").whole_words(True).build()
)
```

Each mutation returns `TextEditResponse`, including match and change counts, changed page numbers, per-change
diagnostics, warnings, and errors.

## Shared Models

`Color` requires integral RGBA components in the inclusive range 0–255. Alpha defaults to 255; `BLACK`, `WHITE`, and
`RED` are provided as constants.

`PageSize` provides A0–A6, B4–B5, Letter, Legal, Tabloid, Executive, Postcard, and 3×5 Index sizes.
`PageSize.from_dimensions(...)` recognizes both portrait and rotated standard dimensions; custom dimensions must be
finite and positive.

The exported `ObjectType` enum covers every object type returned by the v2 snapshot and selection APIs.

## Configuration

- Set `PDFDANCER_API_TOKEN` for authentication (preferred). `PDFDANCER_TOKEN` is also supported for backwards compatibility.
- Override the API host with `PDFDANCER_BASE_URL` (e.g., sandbox or local environments). Defaults to `https://api.pdfdancer.com`.
- Tune HTTP read timeouts via the `timeout` argument on `PDFDancer.open()` and `PDFDancer.new()` (default: 30 seconds).
- Configure total request attempts with `max_attempts` or `PDFDANCER_MAX_ATTEMPTS`; the initial request counts as one attempt.
- For testing against self-signed certificates, call `pdfdancer.set_ssl_verify(False)` to temporarily disable TLS verification.

## Retry and Error Handling

The default HTTP policy makes three total attempts, including the initial request. It uses exponential backoff starting
at one second, a multiplier of two, and a five-second delay cap. Statuses 408, 429, 500, 502, 503, 504, and 520 are
retryable, as are timeout and connection failures. `Retry-After` is honored only for HTTP 429; retry delays do not use
jitter. Configure the total attempt count with `max_attempts` and the multiplier with `retry_backoff_factor`.

Operations raise subclasses of `PdfDancerException`:

- `ValidationException`: input validation problems (missing token, invalid coordinates, etc.).
- `FontNotFoundException`: requested font unavailable on the service.
- `HttpClientException`: transport or server errors with detailed context.
- `SessionException`: session creation and lifecycle failures.
- `RateLimitException`: API rate limit exceeded; includes retry-after timing.

Wrap automated workflows in `try/except` blocks to surface actionable errors to your users.

## Development and Testing

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

#### 2. Create a Virtual Environment and Install Dependencies

```bash
# Create `venv` and install the package with development dependencies
make install-dev
```

The Makefile creates the local `venv` when needed and runs all developer targets with its Python interpreter. Activating
the environment is optional; activate it if you also want to run commands directly:

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

This installs:
- The `pdfdancer` package in editable mode (changes reflect immediately)
- Development tooling including `pytest`, `pytest-cov`, `pytest-mock`, `black`, `isort`, `flake8`, `mypy`, `build`, and `twine`.

To install runtime dependencies without development tools, use `make install`.

#### 3. Configure API Token

Set your PDFDancer API token as an environment variable:

```bash
# On macOS/Linux:
export PDFDANCER_API_TOKEN="your-api-token-here"

# On Windows (Command Prompt):
set PDFDANCER_API_TOKEN=your-api-token-here

# On Windows (PowerShell):
$env:PDFDANCER_API_TOKEN="your-api-token-here"
```

For permanent configuration, add this to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.).

#### 4. Verify Installation

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

Run `make help` to list all developer targets and their configurable variables.

#### Running Tests

```bash
# Run all tests with verbose output
make test

# Run tests that do not require API access
make test-unit

# Run end-to-end tests only
make test-e2e

# Run a specific test file or pass additional pytest arguments
make test TEST_PATH=tests/test_models.py
make test PYTEST_ARGS="-v -x"

# Run all tests with a coverage report
make coverage
```

#### Building Distribution Packages

```bash
# Clean, build, and verify the wheel and source distribution
make package
```

Artifacts will be created in the `dist/` directory. Package versions are derived from Git tags via `setuptools-scm`.

#### Publishing to PyPI

Releases are published automatically to PyPI when a `v*` tag is pushed to GitHub (via GitHub Actions with Trusted Publishers).

```bash
# Create and push a release tag — GitHub Actions handles the rest
git tag v2.0.0
git push origin v2.0.0
```

#### Code Quality

```bash
# Format code
make format

# Check formatting without changing files
make format-check

# Lint
make lint

# Type-check
make typecheck

# Run formatting checks, linting, type checking, and non-E2E tests
make check
```

### Project Structure

```
pdfdancer-client-python/
├── src/pdfdancer/           # Main package source
│   ├── __init__.py          # Package exports
│   ├── pdfdancer_v2.py      # Core PDFDancer and PageClient classes
│   ├── text_editing.py      # Selector-based v2 text request builders
│   ├── image_builder.py     # Fluent image builders
│   ├── path_builder.py      # Vector path builders (lines, beziers, rectangles)
│   ├── page_builder.py      # Page creation builder
│   ├── models.py            # Data models (Position, Font, Color, etc.)
│   ├── types.py             # Live object-reference wrappers
│   └── exceptions.py        # Exception hierarchy
├── tests/                   # Test suite
│   ├── test_models.py       # Model unit tests
│   ├── e2e/                 # End-to-end integration tests
│   └── fixtures/            # Test fixtures and sample PDFs
├── docs/                    # Documentation
├── dist/                    # Build artifacts (created after packaging)
├── pyproject.toml           # Project metadata and dependencies
└── README.md                # This file
```

## Troubleshooting

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

- Ensure `PDFDANCER_API_TOKEN` is set for e2e tests
- Check network connectivity to the PDFDancer API
- Verify you're using Python 3.10 or higher

## Contributing

Contributions are welcome via pull request. Please:

1. Create a feature branch from `main`
2. Add tests for new functionality
3. Ensure all tests pass: `pytest tests/ -v`
4. Follow existing code style and patterns
5. Update documentation as needed

## Helpful Links

- [API documentation](https://docs.pdfdancer.com?utm_source=github&utm_medium=readme&utm_campaign=pdfdancer-python)
- [Product overview](https://www.pdfdancer.com?utm_source=github&utm_medium=readme&utm_campaign=pdfdancer-python)
- [PyPI](https://pypi.org/project/pdfdancer-client-python/)
- [Changelog](https://www.pdfdancer.com/changelog/?utm_source=github&utm_medium=readme&utm_campaign=pdfdancer-python)
- [Status](https://status.pdfdancer.com?utm_source=github&utm_medium=readme&utm_campaign=pdfdancer-python)
- [Issue tracker](https://github.com/MenschMachine/pdfdancer)

## Related SDKs

- TypeScript client: https://github.com/MenschMachine/pdfdancer-client-typescript
- Java client: https://github.com/MenschMachine/pdfdancer-client-java

## License

Apache License 2.0 © 2025 The Famous Cat Ltd. See `LICENSE` and `NOTICE` for details.
