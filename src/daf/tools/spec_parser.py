"""Spec Parser — parses *.spec.yaml into structured Python dicts."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)


def parse_spec(path: str) -> dict[str, Any] | None:
    """Parse a spec YAML file into a structured dict.

    Unknown top-level fields are collected under a ``metadata`` passthrough key.
    Returns ``None`` and logs a warning for malformed YAML — never raises.

    Args:
        path: Absolute or relative path to a ``*.spec.yaml`` file.

    Returns:
        Parsed spec dict, or ``None`` on parse failure.
    """
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
        raw: dict[str, Any] = yaml.safe_load(text) or {}
    except Exception as exc:  # noqa: BLE001
        log.warning("Failed to parse spec file '%s': %s", path, exc)
        return None

    known_keys = {
        "component", "description", "variants", "states", "composedOf",
        "allowedChildren", "tokens", "tokenBindings", "layout", "a11y",
        "a11yRequirements", "props", "compositionRules",
    }
    result: dict[str, Any] = {}
    metadata: dict[str, Any] = {}

    for key, value in raw.items():
        if key in known_keys:
            result[key] = value
        else:
            metadata[key] = value

    if metadata:
        result["metadata"] = metadata

    return result
