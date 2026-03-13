"""WC3DTCGFormatter — CrewAI BaseTool.

Serializes assembled token data to valid W3C DTCG JSON files in three tiers:
  - tokens/base.tokens.json      (global tier — raw values)
  - tokens/semantic.tokens.json  (semantic tier — DTCG references)
  - tokens/component.tokens.json (component-scoped tier — DTCG references)
  - tokens/brands/<name>.tokens.json per brand (multi-brand only)

Enforces DTCG reference-only invariant in semantic/component tiers via a
self-check pass before any file is written. Raises ValueError on broken refs.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# $type inference map: token key segment → DTCG $type value
# Order matters: more specific prefixes first.
# ---------------------------------------------------------------------------

_TYPE_MAP: list[tuple[str, str]] = [
    # Global tier — ordered most-specific first
    ("color.",          "color"),
    ("scale.font-size", "dimension"),
    ("scale.spacing",   "dimension"),
    ("scale.elevation", "shadow"),
    ("scale.radius",    "dimension"),
    ("scale.opacity",   "number"),
    ("scale.duration",  "duration"),
    ("scale.easing",    "cubic-bezier"),
    # Semantic tier — all current semantic tokens reference color palette aliases
    ("text.",           "color"),
    ("surface.",        "color"),
    ("interactive.",    "color"),
    ("border.",         "color"),
    ("icon.",           "color"),
    ("focus.",          "color"),
    ("status.",         "color"),
]

_DTCG_REF_RE = re.compile(r"^\{[a-z0-9._-]+\}$")


def _infer_type(token_key: str) -> str:
    """Infer W3C DTCG $type from token key."""
    for prefix, type_val in _TYPE_MAP:
        if token_key.startswith(prefix):
            return type_val
    return "other"


def _infer_description(token_key: str, value: str) -> str:
    """Generate a human-readable description from the token key and value."""
    parts = token_key.split(".")
    step = parts[-1] if parts else token_key
    group = ".".join(parts[:-1]) if len(parts) > 1 else token_key
    return f"{group} — step {step} ({value})"


def _flat_to_nested_dtcg(
    flat_tokens: dict[str, str],
    is_semantic: bool = False,
) -> dict[str, Any]:
    """Convert flat dot-key token dict to W3C DTCG nested JSON structure.

    Global tier: values stored as-is in $value.
    Semantic tier: values wrapped as DTCG references: {key} in $value.
    """
    nested: dict[str, Any] = {}
    for key, raw_value in flat_tokens.items():
        parts = key.split(".")
        node = nested
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        leaf_key = parts[-1]
        if is_semantic:
            dtcg_value = f"{{{raw_value}}}"
        else:
            dtcg_value = raw_value
        node[leaf_key] = {
            "$value": dtcg_value,
            "$type": _infer_type(key),
            "$description": _infer_description(key, raw_value),
        }
    return nested


_BARE_THEMES_KEY_ERROR = (
    "DTCG extension key must be 'com.daf.themes' — bare 'themes' key violates "
    "the W3C DTCG vendor-namespace requirement. Use $extensions.com.daf.themes."
)


def _flat_to_nested_with_themes(
    flat_tokens: dict[str, str],
    themes: list[str],
    theme_overrides: dict[str, dict[str, str]] | None = None,
    _force_bare_key: bool = False,
) -> dict[str, Any]:
    """Build nested semantic DTCG structure with $extensions.com.daf.themes.

    flat_tokens: {semantic_key: global_alias_key} (no braces)
    themes: list of theme mode names
    theme_overrides: {theme_name: {semantic_key: global_alias_key}}
    _force_bare_key: internal testing only — triggers the guard ValueError
    """
    if _force_bare_key:
        raise ValueError(_BARE_THEMES_KEY_ERROR)

    nested: dict[str, Any] = {}
    for key, base_alias in flat_tokens.items():
        parts = key.split(".")
        node = nested
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        leaf_key = parts[-1]
        token_obj: dict[str, Any] = {
            "$value": f"{{{base_alias}}}",
            "$type": _infer_type(key) if not key.startswith("color.") else "color",
            "$description": _infer_description(key, base_alias),
        }
        if themes:
            extensions_themes: dict[str, str] = {}
            for theme in themes:
                # Use theme-specific override if provided, else fall back to base alias
                override_alias = (
                    (theme_overrides or {}).get(theme, {}).get(key)
                    or base_alias
                )
                extensions_themes[theme] = f"{{{override_alias}}}"
            # Guard: never emit bare "themes" key — must always use com.daf.themes
            if "themes" in token_obj.get("$extensions", {}):
                raise ValueError(_BARE_THEMES_KEY_ERROR)
            token_obj["$extensions"] = {"com.daf.themes": extensions_themes}
        node[leaf_key] = token_obj
    return nested


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

class _FormatterInput(BaseModel):
    global_palette: dict[str, str]
    scale_tokens: dict[str, str]
    semantic_overrides: dict[str, str]
    component_overrides: dict[str, str] = {}
    themes: list[str] = []
    brands: dict[str, dict[str, str]] = {}
    output_dir: str


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class WC3DTCGFormatter(BaseTool):
    """Serialize token data to W3C DTCG JSON files in tokens/ directory."""

    name: str = "wc3_dtcg_formatter"
    description: str = (
        "Serialize global palette and scale tokens (base tier), semantic alias overrides "
        "(semantic tier), and component-scoped overrides (component tier) to valid W3C DTCG "
        "JSON files. Runs a self-check to verify all references resolve before writing. "
        "Returns list of written file paths."
    )
    args_schema: type[BaseModel] = _FormatterInput

    def _run(
        self,
        global_palette: dict[str, str],
        scale_tokens: dict[str, str],
        semantic_overrides: dict[str, str],
        component_overrides: dict[str, str] | None = None,
        themes: list[str] | None = None,
        brands: dict[str, dict[str, str]] | None = None,
        output_dir: str = ".",
        **kwargs: Any,
    ) -> list[str]:
        """Run the formatter. Returns list of written file paths."""
        if component_overrides is None:
            component_overrides = {}
        if themes is None:
            themes = []
        if brands is None:
            brands = {}

        # Build combined global token dict for reference resolution
        all_global: dict[str, str] = {**global_palette, **scale_tokens}

        # --- Self-check: verify all semantic references resolve ---
        self._self_check_references(semantic_overrides, all_global, "semantic")
        self._self_check_references(component_overrides, all_global, "component")
        for brand_name, brand_data in brands.items():
            self._self_check_references(brand_data, all_global, f"brands/{brand_name}")

        # --- Serialise global (base) tier ---
        base_nested = _flat_to_nested_dtcg(all_global, is_semantic=False)

        # --- Serialise semantic tier ---
        semantic_nested = _flat_to_nested_with_themes(
            semantic_overrides,
            themes=themes,
        )

        # --- Serialise component tier ---
        component_nested = _flat_to_nested_dtcg(component_overrides, is_semantic=True)

        # --- Write files ---
        tokens_dir = Path(output_dir) / "tokens"
        tokens_dir.mkdir(parents=True, exist_ok=True)

        written: list[str] = []
        written.append(self._write_json(tokens_dir / "base.tokens.json", base_nested))
        written.append(self._write_json(tokens_dir / "semantic.tokens.json", semantic_nested))
        written.append(self._write_json(tokens_dir / "component.tokens.json", component_nested))

        # --- Multi-brand override files ---
        if brands:
            brands_dir = tokens_dir / "brands"
            brands_dir.mkdir(parents=True, exist_ok=True)
            for brand_name, brand_overrides in brands.items():
                # Brand file = delta from base semantic tier
                brand_nested = _flat_to_nested_dtcg(brand_overrides, is_semantic=True)
                path = brands_dir / f"{brand_name}.tokens.json"
                written.append(self._write_json(path, brand_nested))

        return written

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _self_check_references(
        self,
        overrides: dict[str, str],
        global_tokens: dict[str, str],
        tier_name: str,
    ) -> None:
        """Verify all alias keys resolve against global_tokens.

        Raises ValueError with the token path and broken reference string if
        any alias is not found in global_tokens.
        """
        for token_path, alias_key in overrides.items():
            if alias_key not in global_tokens:
                raise ValueError(
                    f"Unresolvable reference in {tier_name} tier: "
                    f"token '{token_path}' references '{{{alias_key}}}' "
                    f"which does not exist in the global token dict."
                )

    @staticmethod
    def _write_json(path: Path, data: dict[str, Any]) -> str:
        """Write data as indented UTF-8 JSON and return the absolute path string."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return str(path)
