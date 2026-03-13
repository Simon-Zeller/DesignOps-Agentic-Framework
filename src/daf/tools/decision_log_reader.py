"""Tool: decision_log_reader — reads decision records from a generation summary JSON file."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_decisions(path: str) -> list[dict[str, Any]]:
    """Read the ``decisions`` list from a generation summary JSON file.

    Args:
        path: Absolute or relative path to the ``generation-summary.json`` file.

    Returns:
        The list of decision dicts, or an empty list if the file is missing,
        unreadable, or has no ``decisions`` key.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text)
        return list(data.get("decisions", []))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return []
