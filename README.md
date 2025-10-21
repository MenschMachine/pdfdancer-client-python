# PDFDancer Python Client

**Getting Started with PDFDancer**

PDFDancer gives you pixel-perfect programmatic control over any PDF document from Python. Locate existing elements by
coordinates or text, adjust them precisely, add brand-new content, and ship the modified PDF in memory or on disk. The
same API is also available for TypeScript and Java, so teams can orchestrate identical PDF workflows across stacks.

> Need the raw API schema? The latest OpenAPI description lives in `docs/openapi.yml` and is published at
> https://bucket.pdfdancer.com/api-doc/development-0.0.yml.

## Highlights

- Locate paragraphs, text lines, images, vector paths, form fields, and pages by index, coordinates, or text prefixes.
- Edit existing content in place with fluent editors and context managers that apply changes safely.
- Programmatically control third-party PDFs—modify invoices, contracts, and reports you did not author.
- Add content with precise XY positioning using paragraph and image builders, custom fonts, and color helpers.
- Export results as bytes for downstream processing or save directly to disk with one call.

## What Makes PDFDancer Different

- **Edit any PDF**: Work with documents from customers, governments, or vendors—not just ones you generated.
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
- Override the API host with `PDFDANCER_BASE_URL` (e.g., sandbox environments).
- Tune HTTP read timeouts via the `timeout` argument on `PDFDancer.open()` and `PDFDancer.new()`.

## Error Handling

Operations raise subclasses of `PdfDancerException`:

- `ValidationException`: input validation problems (missing token, invalid coordinates, etc.).
- `FontNotFoundException`: requested font unavailable on the service.
- `HttpClientException`: transport or server errors with detailed context.
- `SessionException`: session creation and lifecycle failures.

Wrap automated workflows in `try/except` blocks to surface actionable errors to your users.

## Development

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -e ".[dev]"

pytest -q                           # unit suite
pytest tests/e2e                    # integration tests (requires live API + fixtures)
python -m build                     # produce distribution artifacts
```

Releases are published with `python release.py`. Contributions are welcome via pull request.

## Related SDKs

- TypeScript client: https://github.com/MenschMachine/pdfdancer-client-js
- Java client: https://github.com/MenschMachine/pdfdancer-client-java

## License

Apache License 2.0 © 2025 The Famous Cat Ltd. See `LICENSE` and `NOTICE` for details.
