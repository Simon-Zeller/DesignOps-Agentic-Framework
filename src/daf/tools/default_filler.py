"""DefaultFiller — merges archetype defaults into a brand profile dict."""
from __future__ import annotations

import copy
from typing import Any

from crewai.tools import BaseTool


class DefaultFiller(BaseTool):
    """Merges archetype defaults into a raw brand profile.

    User-specified values always take precedence over defaults.  
    Fields filled from defaults are recorded in ``_filled_fields``.

    Returns the merged profile dict (plain dict, not a BrandProfile model).
    """

    name: str = "default_filler"
    description: str = (
        "Merges archetype default values into a brand profile, filling only fields"
        " the user left unspecified. Returns the merged profile with a '_filled_fields'"
        " list recording which fields received default values."
    )

    def _run(
        self,
        profile: dict[str, Any],
        archetype_defaults: dict[str, Any],
    ) -> dict[str, Any]:
        filled_fields: list[str] = []
        merged = self._deep_merge(profile, archetype_defaults, filled_fields, prefix="")
        merged["_filled_fields"] = filled_fields
        return merged

    # ── helpers ───────────────────────────────────────────────────────────────

    def _deep_merge(
        self,
        user: dict[str, Any],
        defaults: dict[str, Any],
        filled: list[str],
        prefix: str,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for key, default_val in defaults.items():
            field_path = f"{prefix}.{key}" if prefix else key
            user_val = user.get(key)

            if user_val is None:
                # Field absent or explicitly None — fill from defaults
                result[key] = copy.deepcopy(default_val)
                if isinstance(default_val, dict):
                    # Track each sub-field individually
                    for sub_key in default_val:
                        filled.append(f"{field_path}.{sub_key}")
                else:
                    filled.append(field_path)
            elif isinstance(default_val, dict) and isinstance(user_val, dict):
                # Both are dicts — recurse to fill only missing sub-fields
                result[key] = self._deep_merge(
                    user_val, default_val, filled, prefix=field_path
                )
            else:
                # User provided a non-None scalar or mismatched type — keep as-is
                result[key] = user_val

        # Keep any user keys not present in defaults (e.g., name, archetype, _filled_fields)
        for key, user_val in user.items():
            if key not in defaults:
                result[key] = user_val

        return result
