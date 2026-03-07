# Clear Clipping Capability

Most of the PDF model classes including container classes like PDFParagraph/PDFTextLine/PDFPathGroup now implement ClippingDetachable with the method clearClipping().
This removes any clipping path which was active for this element.

This is useful in case clients want to move an element but the new position is hidden by the clipping path. clearing it makes the element visible again.

The new backend is version 1.8.6-rc2, available in the local m2 repository

## Api Docs

Explain for all elements and under the clipping-section.

## Website and Marketing

Not to mention there.

## What's new Newsletter

include

## Changelog

include

## Implementation in pdfdancer-client-python

This capability is implemented for both regular PDF objects and path groups.

- Changed files:
  - `src/pdfdancer/models.py`: added `ClearClippingRequest` and `ClearPathGroupClippingRequest` request models with OpenAPI-style `to_dict()` serialization.
  - `src/pdfdancer/pdfdancer_v1.py`: added internal client methods `_clear_clipping(object_ref)` and `_clear_path_group_clipping(page_number, group_id)`.
  - `src/pdfdancer/types.py`: exposed `clear_clipping()` on `PDFObjectBase` subclasses and on `PathGroupObject`.
  - `README.md`: documented `clear_clipping()` in the selector helper list.
  - `tests/test_openapi_compliance.py`: added serialization tests for both new request wrappers.
  - `tests/e2e/pdf_assertions.py`: added rendered-text assertions (`mutool draw -F text`) used to validate visual clipping outcomes in end-to-end tests.

- How it works in this repo:
  - For typed objects (paragraphs, text lines, images, etc.), `clear_clipping()` builds an `ObjectRef` and sends `PUT /pdf/clipping/clear` with `{"objectRef": ...}`.
  - For path groups, `clear_clipping()` converts 0-based page index to 1-based page number and sends `PUT /pdf/path-group/clipping/clear` with `{"pageNumber": ..., "groupId": ...}`.
  - Both flows validate inputs, return `bool` success, and invalidate cached snapshots when a clear operation succeeds.

- Repo-specific details:
  - Path-group operations are explicitly 1-based at API boundary (`page_number >= 1`).
  - Empty/blank `group_id` and null object refs are rejected via `ValidationException`.
