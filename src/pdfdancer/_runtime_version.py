from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as get_package_version
from pathlib import Path


def resolve_package_version(default: str = "0.0.0.dev0") -> str:
    try:
        from ._version import version

        return version
    except ImportError:
        pass

    try:
        from setuptools_scm import get_version

        return get_version(root=str(Path(__file__).resolve().parents[2]), relative_to=__file__)
    except Exception:
        pass

    try:
        return get_package_version("pdfdancer-client-python")
    except PackageNotFoundError:
        return default
