# Bug Report: Redact Creates Unexpected Placeholder Paths

## Summary

When redacting paths from a PDF, the server creates placeholder rectangles that appear as new paths in subsequent `select_paths()` calls. This causes the path count to be higher than expected after redaction.

## Environment

- **API PR**: #72 (feat/read-write-path-color)
- **Python SDK**: pdfdancer-client-python
- **Test File**: `tests/e2e/test_redact.py::test_redact_multiple_paths`
- **API Server**: Running at `http://localhost:32770` (PR #72 image)
- **Test Fixture**: `basic-paths.pdf` (9 paths)

## Steps to Reproduce

1. Open `basic-paths.pdf` with 9 paths
2. Select first 3 paths (PATH_0_000001, PATH_0_000002, PATH_0_000003)
3. Call `pdf.redact(to_redact)` with those 3 paths
4. Server returns `{"success": true, "count": 3}`
5. Call `pdf.select_paths()` - returns 8 paths instead of expected 6

## Expected Behavior

After redacting 3 paths from a PDF with 9 paths, the resulting PDF should have 6 paths.

## Actual Behavior

After redacting 3 paths:
- The 3 targeted paths are correctly removed
- 2 new placeholder paths appear:
  - PATH_0_000010 at (80.0, 740.0)
  - PATH_0_000011 at (80.0, 640.0)
- Total paths: 8 (not 6)

## Request/Response Details

**Request sent to `POST /pdf/redact`:**
```json
{
  "targets": [
    {"id": "PATH_0_000001", "replacement": "[REDACTED]"},
    {"id": "PATH_0_000002", "replacement": "[REDACTED]"},
    {"id": "PATH_0_000003", "replacement": "[REDACTED]"}
  ],
  "defaultReplacement": "[REDACTED]",
  "placeholderColor": {"r": 0, "g": 0, "b": 0, "a": 255}
}
```

**Response:**
```json
{"success": true, "count": 3}
```

## Analysis

The redaction itself works correctly (the 3 targeted paths are removed), but the server creates 2 placeholder rectangles that become new path objects. This appears to be unintended behavior - placeholder graphics should not appear as selectable path objects in subsequent queries.

## Test Code

```python
def test_redact_multiple_paths():
    """Test batch redacting multiple paths"""
    base_url, token, pdf_path = _require_env_and_fixture("basic-paths.pdf")

    with PDFDancer.open(pdf_path, token=token, base_url=base_url, timeout=30.0) as pdf:
        all_paths = pdf.select_paths()
        assert len(all_paths) == 9

        # Redact first 3 paths
        to_redact = all_paths[:3]
        result = pdf.redact(to_redact)

        assert result.success is True
        assert result.count == 3

        # Should have 6 paths remaining
        assertions = PDFAssertions(pdf)
        assertions.assert_number_of_paths(6)  # FAILS - got 8 paths
```

## Severity

Medium - The redaction functionally works (content is removed), but the path count assertion fails due to unexpected placeholder paths appearing.

## Recommended Fix

The server should either:
1. Not create placeholder path objects that are queryable via `select_paths()`, OR
2. Document this behavior so clients can account for it