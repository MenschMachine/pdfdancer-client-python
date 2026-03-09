# Bug Report: `/pdf/path-group/clipping/clear` rejects valid `pageIndex` for first page

## Summary
The API endpoint `PUT /pdf/path-group/clipping/clear` appears to reject the documented/path-group-standard request contract when clearing clipping for a path group on the first page.

Client sends:

```json
{"pageIndex": 0, "groupId": "..."}
```

Server responds with HTTP error message:

`Page number must be >= 1 (1-based indexing)`

This conflicts with:
- path-group APIs in v1 that consistently use `pageIndex` (0-based), and
- capability notes describing `clearPathGroupClipping(pageIndex, groupId)`.

## Environment
- Client repo: `pdfdancer-client-python`
- Date: 2026-03-09
- Base URL used: `http://46.225.120.69:8080` (from `.api-url`)
- Auth: `PDFDANCER_API_TOKEN=42`
- Test fixture: `tests/fixtures/examples/clipping/invisible-content-clipping-test.pdf`

## Reproduction
1. Open the clipping fixture and create a path group on page 1.
2. Call clear clipping for that group using `pageIndex: 0`.

From client e2e tests:

- `tests/e2e/test_clipping.py::test_clear_path_group_clipping_via_reference`
- `tests/e2e/test_clipping.py::test_clear_path_group_clipping_via_pdfdancer_api`

Command used:

```bash
source venv/bin/activate && \
PDFDANCER_BASE_URL="$(cat .api-url)" \
PDFDANCER_API_TOKEN=42 \
pytest -q tests/e2e/test_clipping.py
```

## Actual Result
Both path-group clipping tests fail with:

- `HttpClientException: API request failed: Page number must be >= 1 (1-based indexing)`
- request payload observed in traceback:

```json
{"pageIndex": 0, "groupId": "pathgroup-..."}
```

## Expected Result
`PUT /pdf/path-group/clipping/clear` should accept `pageIndex` as a 0-based page selector (same as other path-group endpoints), including `pageIndex: 0` for the first page.

## Impact
- `clear_path_group_clipping` cannot be used for first-page path groups when client follows the page-index contract.
- Path-group clipping behavior is inconsistent with other path-group operations and documented capability semantics.

## Notes for API Team
The validation/error text strongly suggests a 1-based page-number validator is being applied on this endpoint path. Please verify request DTO mapping and validation rules for V1 `clearPathGroupClipping` (`pageIndex` vs `pageNumber`) in controller/service conversion.
