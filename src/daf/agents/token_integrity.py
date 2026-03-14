"""Token Integrity Agent (Agent 10, Token Engine Crew).

Checks cross-tier reference integrity: graph cycles, orphans, phantom references,
and tier-skip violations (component → base, bypassing semantic). Writes an
integrity-report.json always, and appends fatal violations to the
validation-rejection.json when issues are found.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from daf.tools.reference_graph_walker import ReferenceGraphWalker
from daf.tools.circular_ref_detector import CircularRefDetector
from daf.tools.orphan_scanner import OrphanScanner
from daf.tools.phantom_ref_scanner import PhantomRefScanner
from daf.tools._rejection_file import write_rejection

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
        current_path = f"{path}.{key}" if path else key
        if isinstance(value, dict) and "$value" in value:
            results.append((current_path, value))
        elif isinstance(value, dict):
            results.extend(_walk_leaf_tokens(value, current_path))
    return results


def _load_staged(output_dir: str) -> dict[str, dict[str, Any]]:
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


def _collect_all_keys(data: dict[str, Any]) -> set[str]:
    return {path for path, _ in _walk_leaf_tokens(data)}


def _collect_all_references(data: dict[str, Any]) -> dict[str, str]:
    """Return {source_path: target_ref_path} for all DTCG reference values."""
    refs: dict[str, str] = {}
    for path, obj in _walk_leaf_tokens(data):
        raw = str(obj.get("$value", ""))
        m = _DTCG_REF_RE.match(raw)
        if m:
            refs[path] = m.group(1)
    return refs


def _detect_tier_skips(
    component_data: dict[str, Any],
    base_keys: set[str],
    semantic_keys: set[str],
) -> list[dict[str, Any]]:
    """Detect component tokens that reference base tokens directly (bypassing semantic)."""
    failures: list[dict[str, Any]] = []
    for path, obj in _walk_leaf_tokens(component_data):
        raw = str(obj.get("$value", ""))
        m = _DTCG_REF_RE.match(raw)
        if not m:
            continue
        ref_target = m.group(1)
        if ref_target in base_keys and ref_target not in semantic_keys:
            failures.append({
                "check": "tier_skip",
                "severity": "fatal",
                "token_path": path,
                "detail": (
                    f"Component token '{path}' references base token '{ref_target}' directly, "
                    "bypassing the semantic tier. Component tokens must only reference semantic tokens."
                ),
                "suggestion": (
                    f"Create a semantic alias for '{ref_target}' and have '{path}' "
                    "reference that semantic token instead."
                ),
            })
    return failures


def _check_integrity(output_dir: str) -> None:
    """Run full reference integrity checks on staged tokens.

    Always writes tokens/integrity-report.json.
    Appends fatal violations to tokens/validation-rejection.json when found.
    """
    tiers = _load_staged(output_dir)
    base_data = tiers.get("base.tokens.json", {})
    semantic_data = tiers.get("semantic.tokens.json", {})
    component_data = tiers.get("component.tokens.json", {})

    failures: list[dict[str, Any]] = []

    # Build reference graph across all tiers
    walker = ReferenceGraphWalker()
    graph = walker._run(base=base_data, semantic=semantic_data, component=component_data)

    # Cycle detection
    cycle_detector = CircularRefDetector()
    cycles = cycle_detector._run(graph=graph)
    for cycle in cycles:
        failures.append({
            "check": "circular_reference",
            "severity": "fatal",
            "token_path": cycle[0] if cycle else "",
            "detail": f"Circular reference detected: {' → '.join(cycle + [cycle[0]])}",
            "suggestion": "Break the cycle by replacing one reference with a direct value.",
        })

    # Orphan detection — only flag base-tier tokens that are never referenced
    # (semantic and component tokens are expected to be terminal consumers)
    orphan_scanner = OrphanScanner()
    all_orphans = orphan_scanner._run(graph=graph)
    base_keys = _collect_all_keys(base_data)
    for orphan in all_orphans:
        if orphan in base_keys:
            failures.append({
                "check": "orphan_token",
                "severity": "warning",
                "token_path": orphan,
                "detail": f"Base token '{orphan}' is defined but never referenced by any semantic token.",
                "suggestion": "Verify the token is intentional; remove it if unused.",
            })

    # Phantom reference detection
    merged_namespace: set[str] = (
        _collect_all_keys(base_data)
        | _collect_all_keys(semantic_data)
        | _collect_all_keys(component_data)
    )
    all_refs: dict[str, str] = {}
    all_refs.update(_collect_all_references(base_data))
    all_refs.update(_collect_all_references(semantic_data))
    all_refs.update(_collect_all_references(component_data))

    phantom_scanner = PhantomRefScanner()
    phantoms = phantom_scanner._run(merged_namespace=merged_namespace, references=all_refs)
    for phantom in phantoms:
        failures.append({
            "check": "phantom_reference",
            "severity": "fatal",
            "token_path": phantom["token_path"],
            "detail": (
                f"Token '{phantom['token_path']}' references '{phantom['missing_ref']}' "
                "which does not exist in any tier."
            ),
            "suggestion": "Define the referenced token or correct the reference path.",
        })

    # Tier-skip detection
    semantic_keys = _collect_all_keys(semantic_data)
    tier_skips = _detect_tier_skips(component_data, base_keys, semantic_keys)
    failures.extend(tier_skips)

    fatal_count = sum(1 for f in failures if f.get("severity") == "fatal")
    warning_count = sum(1 for f in failures if f.get("severity") == "warning")

    # Always write integrity report
    report_dir = Path(output_dir) / "tokens"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "fatal_count": fatal_count,
        "warning_count": warning_count,
        "failures": failures,
    }
    (report_dir / "integrity-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    # Append fatal violations to rejection file (merges with Agent 8's file)
    if fatal_count > 0:
        fatal_failures = [f for f in failures if f.get("severity") == "fatal"]
        write_rejection(
            output_dir=output_dir,
            agent=10,
            phase="token-integrity",
            failures=fatal_failures,
        )


def create_token_integrity_agent() -> Agent:
    """Instantiate the Token Integrity Agent (Agent 10 — Tier 2, Sonnet)."""
    import os

    model = os.environ.get("DAF_TIER2_MODEL", "anthropic/claude-sonnet-4-20250514")
    return Agent(
        role="Token Integrity Specialist",
        goal=(
            "Verify that design token references are structurally sound: no circular "
            "references, no phantom references to non-existent tokens, no tier-skip "
            "violations where component tokens bypass the semantic tier."
        ),
        backstory=(
            "You are a systems thinker focused on structural correctness. You audit the "
            "token reference graph to ensure all references resolve cleanly across the "
            "base → semantic → component tier hierarchy."
        ),
        verbose=False,
        allow_delegation=False,
        llm=model,
    )


def create_token_integrity_task(
    output_dir: str,
    context_tasks: list[Task] | None = None,
) -> Task:
    """Build the integrity-check task for the Token Engine Crew."""
    agent = create_token_integrity_agent()
    task = Task(
        description=(
            f"Audit token reference integrity in '{output_dir}/tokens/staged/'. "
            "Check for circular references, phantom references, orphaned tokens, and "
            "tier-skip violations. Write integrity-report.json and append any fatal "
            "violations to validation-rejection.json."
        ),
        expected_output=(
            "Integrity check complete. integrity-report.json written. "
            "If fatal violations found, validation-rejection.json updated."
        ),
        agent=agent,
        context=context_tasks or [],
    )
    task._check_integrity = _check_integrity  # type: ignore[attr-defined]
    task._output_dir = output_dir  # type: ignore[attr-defined]
    return task
