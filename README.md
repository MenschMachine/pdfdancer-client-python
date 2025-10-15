# PDFDancer Python Client

Automate PDF clean-up, redaction, form filling, and content injection against the PDFDancer API from Python. The client gives you page-scoped selectors, fluent editors, and builders so you can read, modify, and export PDFs programmatically in just a few lines.

## Highlights

- Locate anything inside a PDF—paragraphs, text lines, images, vector paths, pages, AcroForm fields—by page, coordinates, or text prefixes
- Edit or delete existing content with fluent paragraph/text editors and safe apply-on-exit context managers
- Fill or update form fields and propagate the changes back to the document instantly
- Add brand-new content with paragraph/image builders, custom fonts, and precise page positioning
- Download results as bytes for downstream processing or save directly to disk with one method call

## Core Capabilities

- Clean up layout by moving or deleting paragraphs, text lines, or shapes on specific pages
- Search and filter content (e.g., paragraphs starting with "Invoice") to drive custom workflows
- Redact or replace text in bulk with chained editor operations
- Populate AcroForms for contract generation or onboarding flows
- Insert logos, signatures, and generated paragraphs at deterministic coordinates
- Export modified PDFs as bytes for APIs, S3 uploads, or direct file saves

## Requirements

- Python 3.9 or newer
- A PDFDancer API token (set `PDFDANCER_TOKEN` or pass `token=...`)
- Network access to a PDFDancer service (defaults to `https://api.pdfdancer.com`; override with `PDFDANCER_BASE_URL`)

## Installation

```bash
pip install pdfdancer-client-python

# Editable install for local development
pip install -e .
```

## Getting Started

```python
from pathlib import Path
from pdfdancer import Color, PDFDancer

with PDFDancer.open(
    pdf_data=Path("input.pdf"),
    token="your-api-token",  # optional when PDFDANCER_TOKEN is set
    base_url="https://api.pdfdancer.com",
) as pdf:
    # Locate existing content
    heading = pdf.page(0).select_paragraphs_starting_with("Executive Summary")[0]
    heading.edit().replace("Overview").apply()

    # Add a new paragraph using the fluent builder
    pdf.new_paragraph() \
        .text("Generated with PDFDancer") \
        .font("Helvetica", 12) \
        .color(Color(70, 70, 70)) \
        .line_spacing(1.4) \
        .at(page_index=0, x=72, y=520) \
        .add()

    # Persist the modified document
    pdf.save("output.pdf")
```

### Authentication Tips

- Prefer setting `PDFDANCER_TOKEN` in your environment for local development.
- Override the API host by setting `PDFDANCER_BASE_URL` or passing `base_url="https://sandbox.pdfdancer.com"`.
- Use the `timeout` parameter on `PDFDancer.open()` to adjust HTTP read timeouts.

## Selecting PDF Content

```python
with PDFDancer.open("report.pdf") as pdf:  # environment variables provide token/URL
    all_paragraphs = pdf.select_paragraphs()
    page_zero_images = pdf.page(0).select_images()
    form_fields = pdf.page(2).select_form_fields()
    paths_at_cursor = pdf.page(3).select_paths_at(x=150, y=320)

    page = pdf.page(0).get()
    print(page.internal_id, page.position.bounding_rect)
```

Selectors return rich objects (`ParagraphObject`, `TextLineObject`, `ImageObject`, `FormFieldObject`, etc.) with helpers such as `delete()`, `move_to(x, y)`, or `edit()` depending on the object type.

## Editing Text and Forms

```python
with PDFDancer.open("report.pdf") as pdf:
    paragraph = pdf.page(0).select_paragraphs_starting_with("Disclaimer")[0]

    # Chain updates explicitly…
    paragraph.edit() \
        .replace("Updated disclaimer text") \
        .font("Roboto-Regular", 11) \
        .line_spacing(1.1) \
        .move_to(72, 140) \
        .apply()

    # …or use the context manager to auto-apply on success
    with paragraph.edit() as edit:
        edit.replace("Context-managed update").color(Color(120, 0, 0))

    # Update an AcroForm field
    field = pdf.page(1).select_form_fields_by_name("signature")[0]
    field.edit().value("Signed by Jane Doe").apply()
```

## Adding New Content

```python
with PDFDancer.open("report.pdf") as pdf:
    # Register fonts from the service
    fonts = pdf.find_fonts("Roboto", 12)
    pdf.register_font("/path/to/custom.ttf")

    # Paragraphs
    pdf.new_paragraph() \
        .text("Greetings from PDFDancer!") \
        .font(fonts[0].name, fonts[0].size) \
        .at(page_index=0, x=220, y=480) \
        .add()

    # Raster images
    pdf.new_image() \
        .from_file(Path("logo.png")) \
        .at(page=0, x=48, y=700) \
        .add()
```

## Downloading Results

- `pdf.get_pdf_file()` returns the modified PDF as `bytes` (ideal for storage services or HTTP responses).
- `pdf.save("output.pdf")` writes directly to disk, creating directories when needed.

## Error Handling

Most operations raise subclasses of `PdfDancerException`:

- `ValidationException` for client-side validation issues (missing token, invalid coordinates, etc.).
- `FontNotFoundException` when the service cannot locate a requested font.
- `HttpClientException` for transport or server errors with detailed messages.
- `SessionException` when session creation fails.

Wrap complex workflows in `try/except` blocks to surface actionable errors to your users.

## Local Development

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
pip install -r requirements-dev.txt

pytest -q          # run the fast unit suite
pytest tests/e2e   # integration tests (requires live API + fixtures)
```

Package builds are handled by `python -m build`, and release artifacts are published via `python release.py`.

## License

MIT © The Famous Cat Ltd.
