# Clear Clipping Capability

Most of the PDF model classes including container classes like PDFParagraph/PDFTextLine/PDFPathGroup now implement ClippingDetachable with the method clearClipping().
This removes any clipping path which was active for this element.

This is useful in case clients want to move an element but the new position is hidden by the clipping path. clearing it makes the element visible again.

The new backend is version 1.8.6-rc2, available in the local m2 repository

## Test PDFs to use

examples/clipping/invisible-content-clipping-test.pdf

- A PDF where content is present but not visible due to clipping paths that exclude the content areas. Contains an image clipped away by one clipping path and vector paths clipped away by another clipping path.


## Api Docs

Explain for all elements and under the clipping-section.

## Website and Marketing

Not to mention there.

## What's new Newsletter

include

## Changelog

include

## Implementation in pdfdancer-api

- Updated backend dependency to `com.tfc.pdf:pdfdancer-backend:1.8.6-rc2` in `build.gradle.kts` to use the clipping-detach support.
- Added client-facing helpers:
  - `BaseReference.clearClipping()` for any object reference implementing clipping detach semantics via the API.
  - `PathGroupReference.clearClipping()` for grouped vector paths.
  - `PDFDancer.clearClipping(ObjectRef)` calling `PUT /pdf/clipping/clear`.
  - `PDFDancer.clearPathGroupClipping(pageIndex, groupId)` calling `PUT /pdf/path-group/clipping/clear`.
  - Both client calls invalidate local snapshot caches after mutation.
- Added server endpoints in both controllers:
  - `PDFController` and `PDFControllerV1` expose `PUT /pdf/clipping/clear` and `PUT /pdf/path-group/clipping/clear`.
  - V1 uses `ClearClippingRequestV1` and `ClearPathGroupClippingRequestV1`, converting both to internal requests via `toInternal()`.
- Added controller orchestration in `ControllerOps`:
  - `clearClipping(...)` validates `objectRef`, executes `ClearObjectClippingCommand`, and publishes `PDF_OBJECT_MODIFIED` metric with operation `clear_clipping`.
  - `clearPathGroupClipping(...)` validates `groupId` and `pageIndex`, executes `ClearPathGroupClippingCommand`, and publishes `VECTOR_MANIPULATION` metric with operation `clear_path_group_clipping`.
- Wired session and replay support:
  - `Session.clearClipping(...)` and `Session.clearPathGroupClipping(...)` execute commands inside `SessionContext` and record commands for session history.
  - `CommandDeserializer` now reconstructs `ClearObjectClippingCommand` and `ClearPathGroupClippingCommand` for debug archive replay.
- Added tests and assertions:
  - `ClippingTest` verifies clearing clipping on `PathReference`, `PathGroupReference`, and `TextLineReference`.
  - `DirectPDFAssertions`/`PDFAssertions` gained helpers to detect clipped paths and assert clipping present/removed.

## Implementation in pdfdancer-client-python

- Added `PDFDancer.clear_clipping(object_ref)` and internal `_clear_clipping(...)` in `src/pdfdancer/pdfdancer_v1.py`. These validate `object_ref`, call `PUT /pdf/clipping/clear` with `{"objectRef": ...}`, and invalidate snapshot caches on success.
- Added `PDFDancer.clear_path_group_clipping(page_number, group_id)` and internal `_clear_path_group_clipping(...)` in `src/pdfdancer/pdfdancer_v1.py`. These validate a 1-based page number and non-empty group ID, call `PUT /pdf/path-group/clipping/clear`, and invalidate snapshot caches on success.
- Added convenience methods in `src/pdfdancer/types.py`: `PDFObjectBase.clear_clipping()` forwards the current object's `object_ref`, and `PathGroupObject.clear_clipping()` clears clipping for a grouped path set using `self._page_index + 1` to match the API's 1-based page numbering.
- Updated `README.md` to list `clear_clipping()` alongside other selector helper methods so the feature is discoverable from the public API docs.
- Added `_require_env_and_examples_fixture(...)` in `tests/e2e/__init__.py` so clipping tests can load fixtures from `tests/fixtures/examples/...`.
- Expanded `tests/e2e/pdf_assertions.py` with clipping-aware assertions implemented via `pypdf` (`PdfReader` + `ContentStream`) that parse clipping and paint operators to verify clipped/unclipped path and image draw events in saved output PDFs.
- Added end-to-end coverage in `tests/e2e/test_clipping.py` for all client entry points: `path.clear_clipping()`, `image.clear_clipping()`, `pdf.clear_clipping(path.object_ref())`, `group.clear_clipping()`, and `pdf.clear_path_group_clipping(1, group_id)`.
- Added `pypdf>=6.0.0` to dev dependencies in `pyproject.toml` to support operator-level clipping assertions in e2e tests.
