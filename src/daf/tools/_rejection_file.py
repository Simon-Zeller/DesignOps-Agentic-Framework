"""Shared rejection file read/write/merge helpers for Token Engine Crew agents.

Used by Token Validation Agent (8) and Token Integrity Agent (10).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _rejection_path(output_dir: str) -> Path:
    return Path(output_dir) / "tokens" / "validation-rejection.json"


def write_rejection(
    output_dir: str,
    agent: int,
    phase: str,
    failures: list[dict[str, Any]],
    attempt: int = 1,
) -> None:
    """Write or merge a rejection file with the given failures."""
    path = _rejection_path(output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, Any] = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}

    combined_failures = list(existing.get("failures", [])) + failures
    fatal_count = sum(1 for f in combined_failures if f.get("severity") == "fatal")
    warning_count = sum(1 for f in combined_failures if f.get("severity") == "warning")

    rejection: dict[str, Any] = {
        "phase": phase,
        "agent": agent,
        "attempt": attempt,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "failures": combined_failures,
        "fatal_count": fatal_count,
        "warning_count": warning_count,
    }
    path.write_text(json.dumps(rejection, indent=2), encoding="utf-8")


def delete_rejection(output_dir: str) -> None:
    """Delete the rejection file if it exists (successful run clean-up)."""
    path = _rejection_path(output_dir)
    if path.exists():
        path.unlink()


def rejection_exists(output_dir: str) -> bool:
    return _rejection_path(output_dir).exists()
