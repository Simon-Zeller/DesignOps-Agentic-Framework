"""Agent 23 — Generation Narrative Agent.

Writes ``docs/decisions/generation-narrative.md`` — a human-readable account
of why the design system looks the way it does.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from daf.tools.brand_profile_analyzer import analyze_brand_profile
from daf.tools.decision_log_reader import read_decisions
from daf.tools.prose_generator import build_narrative_prompt


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


def run_generation_narrative(output_dir: str) -> None:
    """Generate the generation narrative Markdown file.

    Reads:
        ``{output_dir}/brand-profile.json``
        ``{output_dir}/reports/generation-summary.json``

    Writes:
        ``{output_dir}/docs/decisions/generation-narrative.md``

    Args:
        output_dir: Root pipeline output directory.
    """
    od = Path(output_dir)

    brand_profile = _load_json(od / "brand-profile.json")
    brand_analysis = analyze_brand_profile(brand_profile)

    summary_path = od / "reports" / "generation-summary.json"
    decisions = read_decisions(str(summary_path))

    prompt = build_narrative_prompt(brand_analysis, decisions)
    narrative = _call_llm(prompt) or "No narrative generated."

    content = "\n\n".join([
        "# Generation Narrative",
        narrative,
    ])

    _write_file(od / "docs" / "decisions" / "generation-narrative.md", content)
