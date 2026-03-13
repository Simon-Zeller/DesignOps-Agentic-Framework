"""Shared internal helpers for Documentation Crew agents.

Not part of the public API — use the agent run_* functions directly.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_file(path: Path, content: str) -> None:
    """Create parent directories and write *content* to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    """Load and parse a JSON file, returning *default* on any error."""
    if default is None:
        default = {}
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return default
    return default
