"""TokenUsageMapper — maps DTCG token keys against TSX CSS variable references.

Loads all ``tokens/*.tokens.json`` files, collects defined token keys, then
scans TSX files for ``var(--<slug>)`` references.  Returns three sets:

- ``dead_tokens``: defined but never referenced in any TSX file.
- ``phantom_refs``: referenced in TSX but not defined in any token file.
- ``used_tokens``: referenced AND defined.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

# Matches var(--some-token-slug)
_VAR_RE = re.compile(r"var\(--([a-z][a-z0-9-]*)\)")


def _collect_token_keys(tokens_dir: Path) -> set[str]:
    """Recursively collect all leaf token keys from DTCG JSON files."""
    keys: set[str] = set()
    if not tokens_dir.exists():
        return keys
    for json_file in tokens_dir.glob("*.tokens.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        keys.update(_extract_keys(data, ""))
    return keys


def _extract_keys(obj: Any, prefix: str) -> list[str]:
    """Flatten a DTCG token dict into a list of hyphen-separated keys."""
    collected: list[str] = []
    if not isinstance(obj, dict):
        return collected
    for k, v in obj.items():
        full_key = f"{prefix}-{k}" if prefix else k
        if isinstance(v, dict) and "$value" in v:
            collected.append(full_key)
        elif isinstance(v, dict):
            collected.extend(_extract_keys(v, full_key))
    return collected


def map_token_usage(output_dir: str) -> dict[str, Any]:
    """Run token usage mapping for *output_dir*.

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        Dict with keys ``dead_tokens``, ``phantom_refs``, ``used_tokens``.
    """
    od = Path(output_dir)
    defined_keys = _collect_token_keys(od / "tokens")

    referenced: set[str] = set()
    for tsx_file in (od / "src").rglob("*.tsx") if (od / "src").exists() else []:
        try:
            source = tsx_file.read_text(encoding="utf-8", errors="replace")
            referenced.update(_VAR_RE.findall(source))
        except OSError:
            continue

    used = defined_keys & referenced
    dead = defined_keys - referenced
    phantom = referenced - defined_keys

    return {
        "dead_tokens": sorted(dead),
        "phantom_refs": sorted(phantom),
        "used_tokens": sorted(used),
    }


class _MapperInput(BaseModel):
    output_dir: str


class TokenUsageMapper(BaseTool):
    """Map DTCG token key definitions against TSX CSS variable references."""

    name: str = "token_usage_mapper"
    description: str = (
        "Load defined token keys from tokens/*.tokens.json and scan TSX files for "
        "var(--slug) references. Returns {dead_tokens, phantom_refs, used_tokens}."
    )
    args_schema: type[BaseModel] = _MapperInput

    def _run(self, output_dir: str, **kwargs: Any) -> dict[str, Any]:
        return map_token_usage(output_dir)
