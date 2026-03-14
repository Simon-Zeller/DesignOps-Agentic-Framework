"""Token Validation Agent (Agent 8, Token Engine Crew).

Validates staged token files for DTCG schema compliance, naming conventions,
and WCAG contrast ratios. Writes tokens/validation-rejection.json on failures
and deletes it on clean validation.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from daf.tools.dtcg_schema_validator import DTCGSchemaValidator
from daf.tools.naming_linter import NamingLinter
from daf.tools.contrast_safe_pairer import ContrastSafePairer
from daf.tools._rejection_file import write_rejection, delete_rejection

_DTCG_REF_RE = re.compile(r"^\{([a-z0-9._-]+)\}$")
_TIER_FILES = ("base.tokens.json", "semantic.tokens.json", "component.tokens.json")


def _walk_leaf_tokens(
    data: dict[str, Any],
    path: str = "",
) -> list[tuple[str, dict[str, Any]]]:
    results: list[tuple[str, dict[str, Any]]] = []
    for key, value in data.items():
        if key.startswith("$"):
            continue
        node_path = f"{path}.{key}" if path else key
        if isinstance(value, dict):
            if "$value" in value:
                results.append((node_path, value))
            else:
                results.extend(_walk_leaf_tokens(value, node_path))
    return results


def _load_staged_tokens(output_dir: str) -> dict[str, Any]:
    """Load and merge all staged tier files into one dict keyed by tier filename."""
    staged = Path(output_dir) / "tokens" / "staged"
    result: dict[str, Any] = {}
    for tier_file in _TIER_FILES:
        path = staged / tier_file
        if path.exists():
            result[tier_file] = json.loads(path.read_text(encoding="utf-8"))
        else:
            result[tier_file] = {}
    return result


def _extract_contrast_pairs(
    semantic_tokens: dict[str, Any],
) -> list[tuple[str, str, str, str]]:
    """Extract declared contrast pairs from $extensions.com.daf.contrast-pair annotations.

    Returns list of (fg_path, bg_path, fg_value, bg_value) tuples.
    """
    pairs: list[tuple[str, str, str, str]] = []
    leaf_tokens = _walk_leaf_tokens(semantic_tokens)
    token_values = {path: obj.get("$value", "") for path, obj in leaf_tokens}

    for path, obj in leaf_tokens:
        pair_ext = obj.get("$extensions", {}).get("com.daf.contrast-pair")
        if not pair_ext:
            continue
        bg_ref = pair_ext.get("background")
        if not bg_ref:
            continue
        fg_value = str(obj.get("$value", ""))
        bg_value = str(token_values.get(bg_ref, ""))

        # Resolve references if needed
        if _DTCG_REF_RE.match(fg_value):
            fg_value = token_values.get(fg_value[1:-1], fg_value)
        if _DTCG_REF_RE.match(bg_value):
            bg_value = token_values.get(bg_value[1:-1], bg_value)

        if fg_value and bg_value:
            pairs.append((path, bg_ref, fg_value, bg_value))

    return pairs


def _validate_tokens(output_dir: str) -> None:
    """Run all validation checks on staged tokens.

    Writes validation-rejection.json if fatal failures are found.
    Deletes any stale rejection file if validation passes cleanly.
    """
    tiers = _load_staged_tokens(output_dir)
    failures: list[dict[str, Any]] = []
    has_contrast_pairs = False

    validator = DTCGSchemaValidator()
    linter = NamingLinter()

    for tier_file, token_data in tiers.items():
        # Empty tier detection — only base tier being empty is fatal;
        # semantic and component tiers may legitimately be empty.
        if not token_data:
            if tier_file == "base.tokens.json":
                failures.append({
                    "check": "dtcg_schema",
                    "severity": "fatal",
                    "token_path": tier_file,
                    "detail": f"Token tier file '{tier_file}' is empty (no tokens defined).",
                    "suggestion": "Ensure Agent 2 has written valid token content to this file.",
                })
            continue

        # DTCG schema validation
        schema_result = validator._run(token_dict=token_data)
        failures.extend(schema_result["fatal"])
        failures.extend(schema_result["warnings"])

        # Naming convention lint
        leaf_tokens = _walk_leaf_tokens(token_data)
        keys = [path for path, _ in leaf_tokens]
        if keys:
            lint_result = linter._run(keys=keys)
            failures.extend(lint_result["fatal"])
            failures.extend(lint_result["warnings"])

    # WCAG contrast checking
    semantic_data = tiers.get("semantic.tokens.json", {})
    contrast_pairs = _extract_contrast_pairs(semantic_data)
    if contrast_pairs:
        has_contrast_pairs = True
        pairer = ContrastSafePairer()
        WCAG_AA = 4.5
        for fg_path, bg_path, fg_hex, bg_hex in contrast_pairs:
            try:
                ratio = pairer._wcag_contrast(fg_hex, bg_hex)
                if ratio < WCAG_AA:
                    failures.append({
                        "check": "wcag_contrast",
                        "severity": "fatal",
                        "token_path": fg_path,
                        "detail": (
                            f"Contrast ratio {ratio:.2f}:1 between '{fg_path}' ({fg_hex}) "
                            f"and background '{bg_path}' ({bg_hex}) fails WCAG AA ({WCAG_AA}:1)."
                        ),
                        "suggestion": "Adjust foreground or background colour to achieve ≥4.5:1 ratio.",
                    })
            except (ValueError, KeyError):
                failures.append({
                    "check": "wcag_contrast",
                    "severity": "warning",
                    "token_path": fg_path,
                    "detail": f"Could not compute contrast for pair ({fg_path}, {bg_path}).",
                    "suggestion": "Verify that both colour values are valid hex colours.",
                })

    if not has_contrast_pairs:
        failures.append({
            "check": "wcag_contrast",
            "severity": "warning",
            "token_path": "semantic.tokens.json",
            "detail": "No colour pair annotations found in semantic tokens.",
            "suggestion": "Add $extensions.com.daf.contrast-pair annotations to declare foreground/background pairs for WCAG validation.",
        })

    fatal_failures = [f for f in failures if f.get("severity") == "fatal"]
    if fatal_failures:
        write_rejection(
            output_dir=output_dir,
            agent=8,
            phase="token-validation",
            failures=failures,
        )
    else:
        delete_rejection(output_dir)


def create_token_validation_agent() -> Agent:
    """Instantiate the Token Validation Agent (Agent 8 — Tier 2, Sonnet)."""
    import os

    model = os.environ.get("DAF_TIER2_MODEL", "anthropic/claude-sonnet-4-20250514")
    return Agent(
        role="Token Validation Specialist",
        goal=(
            "Validate staged token files against W3C DTCG schema rules, DAF naming "
            "conventions, and WCAG 2.1 contrast thresholds. Write a structured rejection "
            "file when fatal violations are found; delete any stale rejection files on clean runs."
        ),
        backstory=(
            "You are a senior quality assurance engineer for design token systems. "
            "You enforce the three gates that protect the design system's integrity: "
            "structural correctness (DTCG schema), naming clarity (naming conventions), "
            "and accessibility compliance (WCAG contrast ratios)."
        ),
        tools=[DTCGSchemaValidator(), NamingLinter(), ContrastSafePairer()],
        llm=model,
        verbose=False,
    )


def create_token_validation_task(
    output_dir: str,
    context_tasks: list[Task] | None = None,
) -> Task:
    """Create Task T2: Validate staged token files."""
    return Task(
        description=(
            f"Validate staged token files in '{output_dir}/tokens/staged/'. "
            "Run DTCG schema validation, naming convention linting, and WCAG contrast checks. "
            "Write validation-rejection.json if fatal violations found; delete stale file on success."
        ),
        expected_output=(
            "Either: validation passes and no rejection file exists. "
            "Or: validation fails and tokens/validation-rejection.json is written with "
            "phase, agent, attempt, timestamp, failures, fatal_count, warning_count."
        ),
        agent=create_token_validation_agent(),
        context=context_tasks or [],
    )
