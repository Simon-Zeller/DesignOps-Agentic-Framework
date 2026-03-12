"""StyleDictionaryCompiler — CrewAI BaseTool.

Compiles W3C DTCG semantic token files into per-theme CSS custom property files
following the DAF token compilation strategy spec (p05).

Strategy:
- One CSS file per theme mode + a default variables.css
- Default theme → :root { } selector
- Non-default themes → .theme-<name> { } selector
- Multi-brand: per-brand override merge → .theme-<name>.brand-<name> selectors
- Non-multi-brand archetypes: brand compilation is skipped

Custom transform: daf/theme-resolver — extracts per-theme alias from
  $extensions.com.daf.themes and resolves against global token tier.
Custom format: daf/css-theme-scope — wraps declarations in correct selector.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from daf.tools.theme_utils import ALIAS_INNER_RE as _ALIAS_INNER_RE
from daf.tools.theme_utils import walk_tokens as _walk_tokens_shared


# ---------------------------------------------------------------------------
# Core helpers (daf/theme-resolver and daf/css-theme-scope equivalents)
# ---------------------------------------------------------------------------

def _resolve_token_value(
    token_obj: dict[str, Any],
    theme: str,
    global_tokens: dict[str, str],
) -> str:
    """daf/theme-resolver: extract per-theme value and resolve alias.

    For a given theme, reads $extensions.com.daf.themes[theme] if present,
    otherwise falls back to $value. Resolves alias references against global_tokens.
    Returns the resolved raw value (hex, px, ms, etc.).
    """
    com_daf = token_obj.get("$extensions", {}).get("com.daf.themes", {})
    raw_value = com_daf.get(theme) or token_obj.get("$value", "")

    # Resolve alias reference if needed
    match = _ALIAS_INNER_RE.match(str(raw_value))
    if match:
        alias_key = match.group(1)
        resolved = global_tokens.get(alias_key)
        if resolved is None:
            raise ValueError(
                f"Phantom reference '{raw_value}' for theme '{theme}' — "
                f"'{alias_key}' not found in global token tier"
            )
        return resolved
    return str(raw_value)


def _walk_tokens(data: dict[str, Any], path: str = "") -> list[tuple[str, dict[str, Any]]]:
    return _walk_tokens_shared(data, path)


def _token_path_to_css_var(token_path: str) -> str:
    """Convert dot-path 'color.background.surface' to CSS var '--color-background-surface'."""
    return "--" + token_path.replace(".", "-")


def _compile_css(
    tokens: list[tuple[str, dict[str, Any]]],
    global_tokens: dict[str, str],
    theme: str,
    selector: str,
) -> str:
    """daf/css-theme-scope: compile token list into a CSS block string.

    selector: e.g. ':root', '.theme-dark', '.theme-dark.brand-a'
    """
    lines = [f"{selector} {{"]
    for token_path, token_obj in tokens:
        css_var = _token_path_to_css_var(token_path)
        value = _resolve_token_value(token_obj, theme, global_tokens)
        lines.append(f"  {css_var}: {value};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _merge_tokens(
    base: dict[str, Any],
    override: dict[str, Any],
) -> dict[str, Any]:
    """Shallow-merge override onto base: override values take precedence.

    Both are nested DTCG dicts. Token-level merge: if the override contains a
    leaf token at the same path, it replaces the base leaf token. Groups that
    appear only in base are preserved unchanged.
    """
    result: dict[str, Any] = {}
    all_keys = set(base) | set(override)
    for key in all_keys:
        if key.startswith("$"):
            result[key] = override.get(key, base.get(key))
            continue
        base_val = base.get(key)
        over_val = override.get(key)
        if over_val is None:
            result[key] = base_val
        elif base_val is None:
            result[key] = over_val
        elif isinstance(base_val, dict) and "$value" in base_val:
            # Leaf token — override replaces
            result[key] = over_val if isinstance(over_val, dict) and "$value" in over_val else base_val
        elif isinstance(base_val, dict) and isinstance(over_val, dict):
            result[key] = _merge_tokens(base_val, over_val)
        else:
            result[key] = over_val
    return result


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

class _CompilerInput(BaseModel):
    semantic_tokens: dict[str, Any]
    global_tokens: dict[str, str]
    theme_modes: list[str]
    default_theme: str
    archetype: str
    brands: list[dict[str, Any]] = []  # [{"name": str, "tokens": dict}, ...]
    output_dir: str


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class StyleDictionaryCompiler(BaseTool):
    """Compile DTCG semantic tokens into per-theme CSS custom property files."""

    name: str = "style_dictionary_compiler"
    description: str = (
        "Compile W3C DTCG semantic token files into per-theme CSS custom property files "
        "following the DAF token compilation strategy. Produces variables.css (default theme "
        "with :root selector) and one variables-<theme>.css per theme mode. For multi-brand "
        "archetypes, also compiles brand-scoped CSS with compound .theme-<name>.brand-<name> "
        "selectors. Returns list of written file paths."
    )
    args_schema: type[BaseModel] = _CompilerInput

    def _run(
        self,
        semantic_tokens: dict[str, Any],
        global_tokens: dict[str, str],
        theme_modes: list[str],
        default_theme: str,
        archetype: str,
        brands: list[dict[str, Any]] | None = None,
        output_dir: str = ".",
        **kwargs: Any,
    ) -> list[str]:
        """Run the compiler. Returns list of written file paths."""
        if brands is None:
            brands = []

        compiled_dir = Path(output_dir) / "tokens" / "compiled"
        compiled_dir.mkdir(parents=True, exist_ok=True)

        all_tokens = _walk_tokens(semantic_tokens)
        written: list[str] = []

        # --- Per-theme base compilation ---
        for theme in theme_modes:
            selector = ":root" if theme == default_theme else f".theme-{theme}"
            css_content = _compile_css(all_tokens, global_tokens, theme, selector)

            theme_file = compiled_dir / f"variables-{theme}.css"
            theme_file.write_text(css_content, encoding="utf-8")
            written.append(str(theme_file))

        # --- Default variables.css (alias for default theme) ---
        default_css_path = compiled_dir / "variables.css"
        default_theme_path = compiled_dir / f"variables-{default_theme}.css"
        default_css_path.write_text(default_theme_path.read_text(encoding="utf-8"), encoding="utf-8")
        written.append(str(default_css_path))

        # --- Multi-brand compilation ---
        if archetype == "multi-brand" and brands:
            for brand in brands:
                brand_name: str = brand["name"]
                brand_override: dict[str, Any] = brand.get("tokens", {})
                merged_tokens = _merge_tokens(semantic_tokens, brand_override)
                merged_token_list = _walk_tokens(merged_tokens)

                brand_dir = compiled_dir / brand_name
                brand_dir.mkdir(parents=True, exist_ok=True)

                for theme in theme_modes:
                    selector = (
                        f".theme-{theme}.{brand_name}"
                        if theme != default_theme
                        else f".theme-{theme}.{brand_name}"
                    )
                    css_content = _compile_css(
                        merged_token_list, global_tokens, theme, selector
                    )
                    brand_theme_file = brand_dir / f"variables-{theme}.css"
                    brand_theme_file.write_text(css_content, encoding="utf-8")
                    written.append(str(brand_theme_file))

                # Brand default variables.css
                brand_default = brand_dir / "variables.css"
                brand_default_theme = brand_dir / f"variables-{default_theme}.css"
                brand_default.write_text(
                    brand_default_theme.read_text(encoding="utf-8"), encoding="utf-8"
                )
                written.append(str(brand_default))

        return written
