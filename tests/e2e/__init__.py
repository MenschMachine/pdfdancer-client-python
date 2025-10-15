import os
from pathlib import Path

import pytest
import requests


def _get_base_url():
    return os.getenv('PDFDANCER_BASE_URL', 'https://api.pdfdancer.com')


def _read_token() -> str | None:
    token = os.getenv('PDFDANCER_TOKEN')
    if token:
        return token.strip()
    # Try common token files in repo
    repo_root = Path(__file__).resolve().parents[2]
    candidates = list(repo_root.glob('jwt-token-*.txt')) + list(
        (repo_root / 'clients' / 'python').glob('jwt-token-*.txt'))
    for f in candidates:
        try:
            return f.read_text(encoding='utf-8').strip()
        except Exception:
            continue
    return None


def _server_up(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url}/ping", timeout=3)
        return r.status_code == 200 and 'Pong' in r.text
    except Exception:
        return False


def _require_env_and_fixture(pdf_filename: str) -> tuple[str, str, Path]:
    base_url = _get_base_url()
    token = _read_token()
    if not _server_up(base_url):
        pytest.fail(f"PDFDancer server not reachable at {base_url}; set PDFDANCER_BASE_URL or start server")
    if not token:
        pytest.fail("PDFDANCER_TOKEN not set and no token file found; set env or place jwt-token-*.txt in repo")
    pdf_path = Path(__file__).resolve().parent.parent / 'fixtures' / pdf_filename
    if not pdf_path.exists():
        pytest.fail(f"{pdf_filename} fixture not found")
    return base_url, token, pdf_path
