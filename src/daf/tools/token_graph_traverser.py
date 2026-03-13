"""Agent 42 – TokenGraphTraverser tool (AI Semantic Layer Crew, Phase 5).

Reads ``tokens/*.tokens.json`` (compiled DTCG files), traverses reference
chains, and returns a flat list of tokens with their resolved values.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

# Matches DTCG reference syntax: {some.token.path}
_REF_RE = re.compile(r"^\{(.+)\}$")


def _flatten_tokens(
    obj: dict[str, Any],
    prefix: str = "",
) -> list[dict[str, Any]]:
    """Recursively flatten a DTCG token object into a list of token dicts."""
    tokens: list[dict[str, Any]] = []
    for key, value in obj.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            if "$value" in value:
                tokens.append({
                    "name": full_key,
                    "value": value["$value"],
                    "type": value.get("$type", "unknown"),
                    "extensions": value.get("$extensions", {}),
                })
            else:
                tokens.extend(_flatten_tokens(value, full_key))
    return tokens


def _build_lookup(tokens: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a name→value lookup for reference resolution."""
    return {t["name"]: t["value"] for t in tokens}


def _resolve_value(value: Any, lookup: dict[str, Any], depth: int = 0) -> Any:
    """Resolve a DTCG reference to its final value."""
    if depth > 20 or not isinstance(value, str):
        return value
    match = _REF_RE.match(value)
    if not match:
        return value
    ref_key = match.group(1)
    resolved = lookup.get(ref_key, value)
    return _resolve_value(resolved, lookup, depth + 1)


def traverse_token_graph(output_dir: str) -> list[dict[str, Any]]:
    """Traverse compiled DTCG token files and return a flat resolved token list.

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        List of token dicts with ``name``, ``value``, and ``type`` keys.
    """
    od = Path(output_dir)
    tokens_dir = od / "tokens"
    if not tokens_dir.exists():
        return []

    all_tokens: list[dict[str, Any]] = []
    for token_file in sorted(tokens_dir.glob("*.tokens.json")):
        try:
            data = json.loads(token_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        all_tokens.extend(_flatten_tokens(data))

    if not all_tokens:
        return []

    lookup = _build_lookup(all_tokens)
    for token in all_tokens:
        token["value"] = _resolve_value(token["value"], lookup)

    return all_tokens


class _TokenGraphTraverserInput(BaseModel):
    output_dir: str


class TokenGraphTraverser(BaseTool):
    """Traverse compiled DTCG token files and return a flat resolved list (Agent 42, AI Semantic Layer Crew, Phase 5)."""

    name: str = "token_graph_traverser"
    description: str = (
        "Read tokens/*.tokens.json, resolve all DTCG reference chains, and return "
        "a flat list of tokens with their resolved values, types, and metadata."
    )
    args_schema: type[BaseModel] = _TokenGraphTraverserInput

    def _run(self, output_dir: str, **kwargs: Any) -> list[dict[str, Any]]:
        return traverse_token_graph(output_dir)
