"""Agent 24 — Decision Record Agent.

Generates one ADR per significant generation decision found in
``reports/generation-summary.json``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from daf.tools.decision_extractor import extract_decisions
from daf.tools.adr_template_generator import generate_adr, slugify_title


def _call_llm(prompt: str) -> str:  # pragma: no cover
    """Placeholder LLM call — patchable in tests."""
    return prompt


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def run_decision_records(output_dir: str) -> None:
    """Generate ADR files for all decisions in the generation summary.

    Reads:
        ``{output_dir}/reports/generation-summary.json``

    Writes:
        ``{output_dir}/docs/decisions/adr-{slug}.md`` (one per decision)
        ``{output_dir}/docs/decisions/adr-no-decisions.md`` (if no decisions)

    Args:
        output_dir: Root pipeline output directory.
    """
    od = Path(output_dir)
    summary = _load_json(od / "reports" / "generation-summary.json")
    decisions = extract_decisions(summary)

    decisions_dir = od / "docs" / "decisions"

    if not decisions:
        content = (
            "# ADR: No Decisions Recorded\n\n"
            "No explicit generation decisions were recorded in the generation summary."
        )
        _write_file(decisions_dir / "adr-no-decisions.md", content)
        return

    for decision in decisions:
        adr_md = generate_adr(decision)

        # Optionally enrich consequences via LLM
        enrich_prompt = (
            f"Expand the consequences of this architectural decision in 2-3 sentences:\n"
            f"Decision: {decision.get('decision', '')}\n"
            f"Consequences: {decision.get('consequences', '')}"
        )
        enriched = _call_llm(enrich_prompt)
        if enriched:
            # Append enrichment as an addendum
            adr_md = adr_md.rstrip("\n") + f"\n\n### Notes\n\n{enriched}\n"

        title = decision.get("title", "untitled")
        slug = slugify_title(title) or "untitled"
        _write_file(decisions_dir / f"adr-{slug}.md", adr_md)
