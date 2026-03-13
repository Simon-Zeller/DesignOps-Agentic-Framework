"""JsonDiffEngine — CrewAI BaseTool.

Produces a structured DTCG-aware diff between a prior and current token set.
On initial generation (prior=None), all tokens are classified as added.

Returns:
  {
    is_initial_generation: bool,
    added: [{token_path, value}],
    modified: [{token_path, old_value, new_value}],
    removed: [{token_path, value}],
    deprecated: [{token_path}],
  }
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def _flatten_tokens(data: dict[str, Any], path: str = "") -> dict[str, Any]:
    """Flatten a nested DTCG token dict to {dot-path: token_obj}."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key.startswith("$"):
            continue
        node_path = f"{path}.{key}" if path else key
        if isinstance(value, dict):
            if "$value" in value:
                result[node_path] = value
            else:
                result.update(_flatten_tokens(value, node_path))
    return result


class _DiffInput(BaseModel):
    current: dict[str, Any]
    prior: dict[str, Any] | None = None


class JsonDiffEngine(BaseTool):
    """Generate a structured diff between prior and current DTCG token sets."""

    name: str = "json_diff_engine"
    description: str = (
        "Compute a structured diff between prior and current DTCG token sets. "
        "With prior=None, all tokens are classified as added (initial generation). "
        "Returns {is_initial_generation, added, modified, removed, deprecated}."
    )
    args_schema: type[BaseModel] = _DiffInput

    def _run(
        self,
        current: dict[str, Any],
        prior: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:  # type: ignore[override]
        current_flat = _flatten_tokens(current)

        if prior is None:
            added = [
                {"token_path": path, "value": obj.get("$value")}
                for path, obj in current_flat.items()
            ]
            return {
                "is_initial_generation": True,
                "added": added,
                "modified": [],
                "removed": [],
                "deprecated": [],
            }

        prior_flat = _flatten_tokens(prior)
        is_initial = not bool(prior_flat)

        added: list[dict[str, Any]] = []
        modified: list[dict[str, Any]] = []
        removed: list[dict[str, Any]] = []
        deprecated: list[dict[str, Any]] = []

        for path, obj in current_flat.items():
            if path not in prior_flat:
                added.append({"token_path": path, "value": obj.get("$value")})
            else:
                current_val = obj.get("$value")
                prior_val = prior_flat[path].get("$value")
                if current_val != prior_val:
                    modified.append({
                        "token_path": path,
                        "old_value": prior_val,
                        "new_value": current_val,
                    })
                # Check for deprecated extension
                if obj.get("$extensions", {}).get("com.daf.deprecated"):
                    deprecated.append({"token_path": path})

        for path, obj in prior_flat.items():
            if path not in current_flat:
                removed.append({"token_path": path, "value": obj.get("$value")})

        return {
            "is_initial_generation": is_initial,
            "added": added,
            "modified": modified,
            "removed": removed,
            "deprecated": deprecated,
        }
