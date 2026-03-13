"""Agent 43 – CompositionRuleExtractor tool (AI Semantic Layer Crew, Phase 5).

Reads composition rules from ``reports/composition-audit.json`` with a
fallback to deriving rules from ``specs/*.spec.yaml`` when the audit
report is absent.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from daf.tools.spec_indexer import index_specs


def extract_composition_rules(output_dir: str) -> list[dict[str, Any]]:
    """Extract composition rules from audit report or spec YAML fallback.

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        List of composition rule dicts with ``component``, ``allowed_children``,
        and ``forbidden_children`` keys.
    """
    od = Path(output_dir)
    audit_path = od / "reports" / "composition-audit.json"

    if audit_path.exists():
        try:
            data = json.loads(audit_path.read_text(encoding="utf-8"))
            rules = data.get("rules") or []
            if rules:
                return rules
        except (OSError, json.JSONDecodeError):
            pass

    # Fallback: derive rules from spec YAML composition annotations
    specs = index_specs(output_dir)
    rules: list[dict[str, Any]] = []
    for comp in specs:
        composition = comp.get("composition") or {}
        if not composition:
            continue
        rules.append({
            "component": comp["name"],
            "allowed_children": composition.get("allowed_children") or [],
            "forbidden_children": composition.get("forbidden_children") or [],
            "required_slots": composition.get("required_slots") or [],
            "max_depth": composition.get("max_depth"),
        })
    return rules


class _CompositionRuleExtractorInput(BaseModel):
    output_dir: str


class CompositionRuleExtractor(BaseTool):
    """Extract composition rules from audit or spec YAML (Agent 43, AI Semantic Layer Crew, Phase 5)."""

    name: str = "composition_rule_extractor"
    description: str = (
        "Read composition rules from reports/composition-audit.json. "
        "Falls back to spec YAML composition annotations if the audit is absent. "
        "Returns a list of rule dicts with component, allowed_children, and forbidden_children."
    )
    args_schema: type[BaseModel] = _CompositionRuleExtractorInput

    def _run(self, output_dir: str, **kwargs: Any) -> list[dict[str, Any]]:
        return extract_composition_rules(output_dir)
