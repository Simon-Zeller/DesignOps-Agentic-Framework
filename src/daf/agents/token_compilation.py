"""Token Compilation Agent (Agent 9, Token Engine Crew).

Compiles validated staged token files into CSS, SCSS, TypeScript, and JSON
artefacts in tokens/compiled/. Delegates to StyleDictionaryCompiler.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from daf.tools.style_dictionary_compiler import StyleDictionaryCompiler, _walk_tokens

_TIER_FILES = ("base.tokens.json", "semantic.tokens.json", "component.tokens.json")


def _load_staged(output_dir: str) -> dict[str, dict[str, Any]]:
    """Load all three staged tier files and return them by filename."""
    staged = Path(output_dir) / "tokens" / "staged"
    result: dict[str, dict[str, Any]] = {}
    for name in _TIER_FILES:
        path = staged / name
        if path.exists():
            try:
                result[name] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                result[name] = {}
        else:
            result[name] = {}
    return result


def _build_global_tokens(base_data: dict[str, Any]) -> dict[str, str]:
    """Flatten base token tier into a {dot.path: value} mapping."""
    return {
        path: str(obj.get("$value", ""))
        for path, obj in _walk_tokens(base_data)
    }


def _write_scss(compiled_dir: Path, css_path: Path) -> Path:
    """Write variables.scss as a SCSS @use-compatible forwarding stub."""
    scss_content = (
        "// Auto-generated SCSS token variables\n"
        "// Import this file to access DAF design tokens as CSS custom properties.\n\n"
    )
    # Embed the CSS vars as a SCSS map so they can be consumed with @forward
    if css_path.exists():
        scss_content += css_path.read_text(encoding="utf-8")
    out = compiled_dir / "variables.scss"
    out.write_text(scss_content, encoding="utf-8")
    return out


def _write_tokens_json(compiled_dir: Path, flat_tokens: dict[str, str]) -> Path:
    """Write a flat {token.path: value} JSON artefact."""
    out = compiled_dir / "tokens.json"
    out.write_text(json.dumps(flat_tokens, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _write_tokens_ts(compiled_dir: Path, flat_tokens: dict[str, str]) -> Path:
    """Write a typed TypeScript constant export for all token paths."""
    lines = [
        "// Auto-generated — do not edit manually.",
        "export const tokens = {",
    ]
    for path, value in sorted(flat_tokens.items()):
        key = path.replace(".", "_")
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'  {key}: "{escaped}",')
    lines.append("} as const;")
    lines.append("")
    content = "\n".join(lines)
    out = compiled_dir / "tokens.ts"
    out.write_text(content, encoding="utf-8")
    return out


def _compile_tokens(output_dir: str, brand_profile: dict[str, Any]) -> None:
    """Compile staged tokens into CSS, SCSS, TS, and JSON artefacts.

    Reads from tokens/staged/, writes to tokens/compiled/.
    Raises RuntimeError on compiler failure.
    """
    tiers = _load_staged(output_dir)
    base_data = tiers.get("base.tokens.json", {})
    semantic_data = tiers.get("semantic.tokens.json", {})

    global_tokens = _build_global_tokens(base_data)

    themes_cfg = brand_profile.get("themes", {})
    theme_modes: list[str] = themes_cfg.get("modes", ["light"])
    default_theme: str = themes_cfg.get("defaultTheme", theme_modes[0])
    archetype: str = brand_profile.get("archetype", "standard")
    brands: list[dict[str, Any]] = brand_profile.get("brands", [])

    compiler = StyleDictionaryCompiler()

    # May raise RuntimeError — let it propagate to the caller / CrewAI task
    compiler._run(
        semantic_tokens=semantic_data,
        global_tokens=global_tokens,
        theme_modes=theme_modes,
        default_theme=default_theme,
        archetype=archetype,
        brands=brands,
        output_dir=output_dir,
    )

    compiled_dir = Path(output_dir) / "tokens" / "compiled"
    compiled_dir.mkdir(parents=True, exist_ok=True)

    default_css = compiled_dir / "variables.css"
    _write_scss(compiled_dir, default_css)

    # Build flat token map from all tiers for JSON/TS artefacts
    flat: dict[str, str] = {}
    for tier_data in (base_data, semantic_data, tiers.get("component.tokens.json", {})):
        for path, obj in _walk_tokens(tier_data):
            flat[path] = str(obj.get("$value", ""))

    _write_tokens_json(compiled_dir, flat)
    _write_tokens_ts(compiled_dir, flat)


def create_token_compilation_agent() -> Agent:
    """Instantiate the Token Compilation Agent (Agent 9 — Tier 3, Haiku)."""
    import os

    model = os.environ.get("DAF_TIER3_MODEL", "claude-haiku-4-20250514")
    return Agent(
        role="Token Compilation Specialist",
        goal=(
            "Compile validated staged token files into production-ready CSS custom property "
            "files, SCSS variables, TypeScript constants, and JSON artefacts ready for "
            "distribution to consuming applications."
        ),
        backstory=(
            "You are a build-system engineer who transforms design tokens into distributable "
            "artefacts. You ensure all theme modes are compiled, fallback values are correct, "
            "and the output is immediately consumable by frontend engineers."
        ),
        verbose=False,
        allow_delegation=False,
        llm=model,
    )


def create_token_compilation_task(
    output_dir: str,
    brand_profile: dict[str, Any],
    context_tasks: list[Task] | None = None,
) -> Task:
    """Build the compilation task for the Token Engine Crew."""
    agent = create_token_compilation_agent()
    task = Task(
        description=(
            f"Compile staged design tokens in '{output_dir}/tokens/staged/' into "
            f"production artefacts in '{output_dir}/tokens/compiled/'. "
            "Generate variables.css (default theme), per-theme CSS files, variables.scss, "
            "tokens.ts, and tokens.json. Brand profile settings: "
            f"themes={brand_profile.get('themes', {})}, "
            f"archetype={brand_profile.get('archetype', 'standard')}."
        ),
        expected_output=(
            "Compilation complete. All artefacts written to tokens/compiled/: "
            "variables.css, variables.scss, tokens.ts, tokens.json, and one "
            "variables-{theme}.css per declared theme mode."
        ),
        agent=agent,
        context=context_tasks or [],
    )
    task._compile_tokens = _compile_tokens  # type: ignore[attr-defined]
    task._output_dir = output_dir  # type: ignore[attr-defined]
    task._brand_profile = brand_profile  # type: ignore[attr-defined]
    return task
