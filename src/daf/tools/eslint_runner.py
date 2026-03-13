"""ESLint Runner — runs ESLint on generated TSX files and returns structured lint results."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def run_eslint(file_path: str) -> list[dict[str, Any]]:
    """Run ESLint on *file_path* and return a list of structured violation dicts.

    Each violation dict has ``rule``, ``message``, and ``line`` keys.
    Returns ``[]`` if ESLint is not installed or the file has no violations.

    Args:
        file_path: Absolute path to the TSX file to lint.

    Returns:
        List of violation dicts, empty list if none.
    """
    try:
        result = subprocess.run(
            ["eslint", "--format", "json", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # ESLint not installed or timed out — return no violations
        return []

    stdout = result.stdout.strip()
    if not stdout:
        return []

    try:
        eslint_output: list[dict[str, Any]] = json.loads(stdout)
    except json.JSONDecodeError:
        return []

    violations: list[dict[str, Any]] = []
    for file_result in eslint_output:
        for msg in file_result.get("messages", []):
            violations.append({
                "rule": msg.get("ruleId", "unknown"),
                "message": msg.get("message", ""),
                "line": msg.get("line", 0),
            })

    return violations
