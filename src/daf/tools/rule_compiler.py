"""Agent 44 – RuleCompiler tool (AI Semantic Layer Crew, Phase 5).

Reads the component, token, and composition registry files, aggregates
compliance rules into four categories, and writes
``registry/compliance-rules.json``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

_CATEGORIES = ("token_rules", "composition_rules", "a11y_rules", "naming_rules")


def _load_json(path: Path, default: Any = None) -> Any:
    """Load JSON from *path* returning *default* on failure."""
    if default is None:
        default = []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def compile_rules(output_dir: str) -> dict[str, Any]:
    """Compile compliance rules from registry files.

    Reads ``registry/components.json``, ``registry/tokens.json``, and
    ``registry/composition-rules.json``.  Writes the aggregated result to
    ``registry/compliance-rules.json``.

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        The compliance rules dict written to ``registry/compliance-rules.json``.
    """
    od = Path(output_dir)
    registry_dir = od / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)

    components: list[dict[str, Any]] = _load_json(registry_dir / "components.json", [])
    tokens: list[dict[str, Any]] = _load_json(registry_dir / "tokens.json", [])
    comp_rules: list[dict[str, Any]] = _load_json(registry_dir / "composition-rules.json", [])

    # Derive token rules: each defined token may be referenced via CSS var
    token_rules: list[dict[str, Any]] = [
        {
            "rule": "use_design_token",
            "token": t.get("name", ""),
            "description": (
                f"Use the '{t.get('name', '')}' design token instead of hardcoded values."
            ),
        }
        for t in tokens
        if t.get("name")
    ]

    # Derive a11y rules from component prop metadata
    a11y_rules: list[dict[str, Any]] = []
    for comp in components:
        for prop in (comp.get("props") or []):
            prop_name: str = str(prop.get("name", "")) if isinstance(prop, dict) else str(prop)
            if any(kw in prop_name.lower() for kw in ("aria", "role", "alt", "label")):
                a11y_rules.append({
                    "component": comp.get("name", ""),
                    "prop": prop_name,
                    "rule": "required_accessibility_attribute",
                })

    # Derive naming rules
    naming_rules: list[dict[str, Any]] = [
        {
            "rule": "component_pascal_case",
            "description": "All component names must use PascalCase.",
            "pattern": "^[A-Z][A-Za-z0-9]*$",
        },
        {
            "rule": "token_kebab_case",
            "description": "All token names must use kebab-case.",
            "pattern": "^[a-z][a-z0-9-]*$",
        },
    ]

    result: dict[str, Any] = {
        "token_rules": token_rules,
        "composition_rules": comp_rules,
        "a11y_rules": a11y_rules,
        "naming_rules": naming_rules,
    }

    out_path = registry_dir / "compliance-rules.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


class _RuleCompilerInput(BaseModel):
    output_dir: str


class RuleCompiler(BaseTool):
    """Compile all registry rules into ``registry/compliance-rules.json`` (Agent 44, AI Semantic Layer Crew, Phase 5)."""

    name: str = "rule_compiler"
    description: str = (
        "Read registry/components.json, registry/tokens.json, and "
        "registry/composition-rules.json. Aggregate into four rule categories "
        "(token_rules, composition_rules, a11y_rules, naming_rules) and write "
        "registry/compliance-rules.json."
    )
    args_schema: type[BaseModel] = _RuleCompilerInput

    def _run(self, output_dir: str, **kwargs: Any) -> dict[str, Any]:
        return compile_rules(output_dir)
