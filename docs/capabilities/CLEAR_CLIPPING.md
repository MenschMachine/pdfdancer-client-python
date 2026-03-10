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

- Added top-level client methods in `src/pdfdancer/pdfdancer_v1.py`: `PDFDancer.clear_clipping(object_ref)` calls `PUT /pdf/clipping/clear`, and `PDFDancer.clear_path_group_clipping(page_number, group_id)` calls `PUT /pdf/path-group/clipping/clear`.
- The Python client validates required inputs before sending the request: `object_ref` must be present, `page_number` is a 1-based integer for path groups, and `group_id` must be non-empty. Both methods coerce the API response to `bool` and invalidate cached snapshots after a successful mutation.
- Added object-level convenience methods in `src/pdfdancer/types.py`. `PDFObjectBase.clear_clipping()` makes the capability available on typed selections that expose `object_ref()` such as paths, images, and text lines, while `PathGroupObject.clear_clipping()` forwards to the path-group API using `self._page_index + 1` to convert the internal 0-based index to the public 1-based page number.
- Updated `README.md` to list `clear_clipping()` alongside other typed-object helper methods so the feature is discoverable from the main usage guide.
- Added end-to-end coverage in `tests/e2e/test_clipping.py` for direct object calls and top-level client calls on paths, grouped paths, images, and clipped text lines, including a case where clipping spans multiple content streams. `tests/e2e/pdf_assertions.py` was extended with PDF draw-event inspection helpers that assert whether clipping is present or removed.
