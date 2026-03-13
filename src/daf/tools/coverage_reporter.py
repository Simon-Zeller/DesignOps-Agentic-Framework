"""Coverage Reporter — reads Vitest LCOV/JSON output for a component file."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def get_coverage(component_file: str, coverage_path: str) -> float | None:
    """Return line coverage percentage (0.0–1.0) for *component_file*.

    Reads a Vitest per-file JSON coverage report keyed by filename.

    Args:
        component_file: Filename to look up (e.g. ``"Button.tsx"``).
        coverage_path: Path to the Vitest LCOV JSON file.

    Returns:
        Float 0.0–1.0 if found, or ``None`` if the file is absent or the
        component is not in the coverage data.
    """
    path = Path(coverage_path)
    if not path.exists():
        return None

    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    # Look up by basename to support absolute-path keyed reports
    entry = data.get(component_file)
    if entry is None:
        # Try matching by basename
        for key, value in data.items():
            if Path(key).name == Path(component_file).name:
                entry = value
                break

    if entry is None:
        return None

    lines = entry.get("lines", {})
    pct = lines.get("pct")
    if pct is None:
        # Fallback to statements
        statements = entry.get("statements", {})
        pct = statements.get("pct")

    if pct is None:
        return None

    return float(pct) / 100.0
