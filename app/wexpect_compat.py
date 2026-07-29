from __future__ import annotations

import importlib
import sys
from importlib.metadata import version
from threading import Lock
from types import ModuleType, SimpleNamespace
from typing import Any

_IMPORT_LOCK = Lock()


def import_wexpect() -> Any:
    """Load Wexpect without restoring Setuptools' removed pkg_resources API."""
    with _IMPORT_LOCK:
        try:
            return importlib.import_module("wexpect")
        except ModuleNotFoundError as exc:
            if exc.name != "pkg_resources":
                raise

        compatibility = ModuleType("pkg_resources")

        def require(requirement: str) -> list[SimpleNamespace]:
            if requirement != "wexpect":
                raise ImportError(f"Unsupported compatibility request: {requirement}")
            return [SimpleNamespace(version=version("wexpect"))]

        compatibility.require = require  # type: ignore[attr-defined]
        sys.modules["pkg_resources"] = compatibility
        try:
            return importlib.import_module("wexpect")
        finally:
            if sys.modules.get("pkg_resources") is compatibility:
                del sys.modules["pkg_resources"]
