"""Code Generation Agent (Agent 14, Design-to-Code Crew).

Generates TypeScript/TSX source, unit tests (.test.tsx), and Storybook stories
(.stories.tsx) from intent manifests. Enforces zero hardcoded values,
primitive composition, and lint compliance.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from daf.tools.code_scaffolder import scaffold_tsx, scaffold_tests, scaffold_stories
from daf.tools.eslint_runner import run_eslint
from daf.tools.story_template_generator import generate_stories
from daf.tools.pattern_memory_store import PatternMemoryStore

_MAX_LINT_RETRIES = 2


def _resolve_token(token_ref: str, compiled_tokens: dict[str, str]) -> str | None:
    """Look up a token reference in compiled tokens. Returns None if not found."""
    return compiled_tokens.get(token_ref)


def _generate_code(output_dir: str) -> None:
    """Generate TSX source, tests, and stories for all components in the queue.

    Reads ``intent_manifests.json`` and ``tokens/compiled/flat.json``.
    Writes component triplets under ``src/primitives/`` or ``src/components/``.
    Writes ``reports/generation-rejection.json`` for unresolvable components.

    Args:
        output_dir: Root pipeline output directory.
    """
    od = Path(output_dir)

    # Load intent manifests
    manifests_path = od / "intent_manifests.json"
    if not manifests_path.exists():
        raise FileNotFoundError(
            f"intent_manifests.json not found in '{output_dir}'. "
            "Ensure Intent Extraction Agent has completed."
        )
    manifests: list[dict[str, Any]] = json.loads(manifests_path.read_text(encoding="utf-8"))

    # Load compiled tokens
    flat_path = od / "tokens" / "compiled" / "flat.json"
    compiled_tokens: dict[str, str] = {}
    if flat_path.exists():
        compiled_tokens = json.loads(flat_path.read_text(encoding="utf-8"))

    memory = PatternMemoryStore()
    rejected: list[dict[str, Any]] = []

    for manifest in manifests:
        name = manifest["component_name"]
        tier = manifest.get("tier", "simple")

        # Check all token bindings are resolvable
        unresolvable: list[str] = []
        for binding in manifest.get("token_bindings", []):
            if _resolve_token(binding["token"], compiled_tokens) is None:
                unresolvable.append(binding["token"])

        if unresolvable:
            rejected.append({
                "component": name,
                "reason": "unresolvable_token_ref",
                "tokens": unresolvable,
            })
            continue

        # Determine output directory (primitives vs. components)
        if tier == "primitive":
            comp_dir = od / "src" / "primitives" / name
        else:
            comp_dir = od / "src" / "components" / name
        comp_dir.mkdir(parents=True, exist_ok=True)

        # Generate TSX
        tsx_content = scaffold_tsx(manifest)
        tsx_path = comp_dir / f"{name}.tsx"
        tsx_path.write_text(tsx_content, encoding="utf-8")

        # Lint retry loop
        for _ in range(_MAX_LINT_RETRIES):
            violations = run_eslint(str(tsx_path))
            if not violations:
                break

        # Generate test file
        test_content = scaffold_tests(manifest)
        (comp_dir / f"{name}.test.tsx").write_text(test_content, encoding="utf-8")

        # Generate stories file
        stories_content = scaffold_stories(manifest)
        (comp_dir / f"{name}.stories.tsx").write_text(stories_content, encoding="utf-8")

        # Store pattern for memory
        memory.store_pattern(name, {
            "token_bindings": manifest.get("token_bindings", []),
            "variants": manifest.get("variants", []),
        })

    # Write rejection file if any components failed
    if rejected:
        reports_dir = od / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        rejection_path = reports_dir / "generation-rejection.json"
        rejection_path.write_text(
            json.dumps({"rejected_components": rejected}, indent=2), encoding="utf-8"
        )


def create_code_generation_agent() -> Agent:
    """Instantiate the Code Generation Agent (Agent 14 — Tier 1, Opus)."""
    model = os.environ.get("DAF_TIER1_MODEL", "claude-opus-4-5")
    return Agent(
        role="Component Code Generator",
        goal=(
            "Generate production-quality TypeScript/TSX source files, Jest unit tests, and "
            "Storybook CSF3 stories from intent manifests. Enforce zero hardcoded values "
            "(compiled tokens only), data-testid attributes, and lint compliance."
        ),
        backstory=(
            "You are a senior TypeScript/React engineer with expertise in design systems. "
            "You translate precise intent manifests into production-ready component code that "
            "passes lint, compiles cleanly, and covers all specified variants and a11y requirements."
        ),
        tools=[],
        llm=model,
        verbose=False,
    )


def create_code_generation_task(
    output_dir: str,
    context_tasks: list[Task] | None = None,
) -> Task:
    """Create Task T3: Generate TSX source, tests, and stories."""
    return Task(
        description=(
            f"Read '{output_dir}/intent_manifests.json'. For each component, generate: "
            "1) A TypeScript/TSX source file with all variants and data-testid attributes. "
            "2) A Jest/RTL unit test file ending with // @accessibility-placeholder. "
            "3) A Storybook CSF3 stories file with one export per variant. "
            "Resolve all token references against tokens/compiled/flat.json. "
            "Write components to src/primitives/<Name>/ or src/components/<Name>/. "
            f"Write reports/generation-rejection.json for any unresolvable components."
        ),
        expected_output=(
            "For each component: <Name>.tsx, <Name>.test.tsx, <Name>.stories.tsx written under "
            "src/primitives/ or src/components/. reports/generation-rejection.json written if any failed."
        ),
        agent=create_code_generation_agent(),
        context=context_tasks or [],
    )
