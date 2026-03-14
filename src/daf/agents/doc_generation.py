"""Agent 21 — Doc Generation Agent.

Generates per-component Markdown docs and the project ``docs/README.md``.
Reads ``specs/*.spec.yaml`` and ``tokens/semantic.tokens.json``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from daf.tools.spec_to_doc_renderer import render_spec_to_sections
from daf.tools.prop_table_generator import generate_prop_table
from daf.tools.example_code_generator import generate_example_stub
from daf.tools.readme_template import render_readme
from daf.tools.token_value_resolver import resolve_token
from daf.agents._doc_helpers import write_file as _write_file, load_json as _load_json_helper


def _call_llm(prompt: str) -> str:  # pragma: no cover
    """Placeholder LLM call — patchable in tests."""
    return prompt


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], _load_json_helper(path))


def run_doc_generation(output_dir: str) -> None:
    """Generate component docs and README for all specs in *output_dir*.

    Reads:
        ``{output_dir}/specs/*.spec.yaml``
        ``{output_dir}/tokens/semantic.tokens.json``

    Writes:
        ``{output_dir}/docs/components/<Name>.md`` (one per spec)
        ``{output_dir}/docs/README.md``

    Args:
        output_dir: Root pipeline output directory.
    """
    od = Path(output_dir)
    specs_dir = od / "specs"
    compiled_tokens = _load_json(od / "tokens" / "semantic.tokens.json")

    component_names: list[str] = []
    token_categories: list[str] = sorted(
        {path.split(".")[0] for path in compiled_tokens}
    )

    spec_files = sorted(specs_dir.glob("*.spec.yaml")) if specs_dir.exists() else []

    for spec_file in spec_files:
        try:
            raw = yaml.safe_load(spec_file.read_text(encoding="utf-8")) or {}
        except Exception:
            continue

        sections = render_spec_to_sections(raw)
        name: str = sections["name"] or spec_file.stem
        if not name:
            continue

        component_names.append(name)

        prop_table = generate_prop_table(sections["props"])

        # Variant showcase
        variants = sections["variants"]
        variant_blocks: list[str] = []
        for variant in variants:
            stub = generate_example_stub(name, variant)
            variant_blocks.append(f"### {variant}\n\n{stub}")
        variants_section = (
            "\n\n".join(variant_blocks)
            if variant_blocks
            else "No variants declared."
        )

        # Usage examples via LLM
        basic_prompt = f"Write a minimal TSX usage example for the {name} component."
        advanced_prompt = (
            f"Write an advanced TSX usage example for the {name} component "
            f"using all significant props."
        )
        basic_example = _call_llm(basic_prompt) or f"```tsx\n<{name} />\n```"
        advanced_example = _call_llm(advanced_prompt) or f"```tsx\n<{name} label='Hello' />\n```"

        # Token binding table
        token_bindings = sections["token_bindings"]
        token_rows: list[str] = []
        if token_bindings:
            token_rows.append("| Role | Token Path | Resolved Value |")
            token_rows.append("|------|------------|----------------|")
            for role, token_path in token_bindings.items():
                value = resolve_token(token_path, compiled_tokens) or "(unresolved)"
                token_rows.append(f"| {role} | {token_path} | {value} |")
        token_table = "\n".join(token_rows) if token_rows else "No token bindings declared."

        doc_content = "\n\n".join([
            f"# {name}",
            "## Props",
            prop_table,
            "## Variants",
            variants_section,
            "## Usage",
            "### Basic",
            basic_example,
            "### Advanced",
            advanced_example,
            "## Token Bindings",
            token_table,
        ])

        _write_file(od / "docs" / "components" / f"{name}.md", doc_content)

    readme_content = render_readme(component_names, token_categories)
    _write_file(od / "docs" / "README.md", readme_content)

    # Build docs/component-index.json for downstream crews (Governance, Analytics)
    component_index: dict[str, Any] = {}
    for spec_file in spec_files:
        try:
            raw = yaml.safe_load(spec_file.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        name = raw.get("component", spec_file.stem)
        deps: list[str] = []
        comp_rules = raw.get("compositionRules", {})
        if isinstance(comp_rules, dict):
            composes_from = comp_rules.get("composesFrom", [])
            if isinstance(composes_from, list):
                deps = [str(d) for d in composes_from]
        component_index[name] = {"dependencies": deps}
    import json as _json
    _write_file(od / "docs" / "component-index.json", _json.dumps(component_index, indent=2))
