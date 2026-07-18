import os
from pathlib import Path
from typing import Tuple

import httpx
import pytest

from pdfdancer.pdfdancer_v2 import _execute_request_with_retries


def _get_base_url():
    return os.getenv("PDFDANCER_BASE_URL", "https://api.pdfdancer.com")


def _read_token() -> str | None:
    # Check PDFDANCER_API_TOKEN first (preferred), then PDFDANCER_TOKEN (legacy)
    token = os.getenv("PDFDANCER_API_TOKEN") or os.getenv("PDFDANCER_TOKEN")
    if token:
        return token.strip()
    # Try common token files in repo
    repo_root = Path(__file__).resolve().parents[2]
    candidates = list(repo_root.glob("jwt-token-*.txt")) + list(
        (repo_root / "clients" / "python").glob("jwt-token-*.txt")
    )
    for f in candidates:
        try:
            return f.read_text(encoding="utf-8").strip()
        except Exception:
            continue
    return None


def _server_up(base_url: str) -> Tuple[bool, str]:
    try:
        max_attempts = max(1, int(os.getenv("PDFDANCER_MAX_ATTEMPTS", "3")))
        retry_backoff_factor = float(os.getenv("PDFDANCER_RETRY_BACKOFF_FACTOR", "2.0"))
        response = _execute_request_with_retries(
            request_callable=lambda: httpx.get(
                f"{base_url}/ping", timeout=30, verify=False
            ),
            operation="GET /ping",
            max_attempts=max_attempts,
            retry_backoff_factor=retry_backoff_factor,
            retryable_status_codes={408, 429, 500, 502, 503, 504, 520},
        )
        return response.status_code == 200 and "Pong" in response.text, response.text
    except Exception as e:
        return False, str(e)


def _require_env_and_fixture(pdf_filename: str) -> tuple[str, str, Path]:
    base_url, token = _require_env()
    pdf_path = Path(__file__).resolve().parent.parent / "fixtures" / pdf_filename
    if not pdf_path.exists():
        pytest.fail(f"{pdf_filename} fixture not found")
    return base_url, token, pdf_path


def _require_env() -> tuple[str, str | None]:
    base_url = _get_base_url()
    token = _read_token()
    up, msg = _server_up(base_url)
    if not up:
        pytest.fail(
            f"PDFDancer server not reachable at {base_url}, reason: {msg}; set PDFDANCER_BASE_URL or start server"
        )
    if not token:
        pytest.fail(
            "PDFDANCER_API_TOKEN not set and no token file found; set env or place jwt-token-*.txt in repo"
        )
    return base_url, token
