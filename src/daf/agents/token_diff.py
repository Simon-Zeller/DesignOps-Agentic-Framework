"""Token Diff Agent (Agent 11, Token Engine Crew).

Compares the current compiled token set against the prior run's diff.json
to produce a structured change log. Writes tokens/diff.json on every run.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from daf.tools.json_diff_engine import JsonDiffEngine

_TIER_FILES = ("base.tokens.json", "semantic.tokens.json", "component.tokens.json")


def _load_staged(output_dir: str) -> dict[str, Any]:
    """Merge all staged tier files into a single flat DTCG dict for diffing."""
    staged = Path(output_dir) / "tokens" / "staged"
    merged: dict[str, Any] = {}
    for name in _TIER_FILES:
        path = staged / name
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                merged.update(data)
            except json.JSONDecodeError:
                pass
    return merged


def _load_prior_diff(output_dir: str) -> dict[str, Any] | None:
    """Load a prior diff.json to enable incremental comparison."""
    diff_path = Path(output_dir) / "tokens" / "diff.json"
    if diff_path.exists():
        try:
            result: dict[str, Any] = json.loads(diff_path.read_text(encoding="utf-8"))
            return result
        except json.JSONDecodeError:
            pass
    return None


def _run_diff(output_dir: str) -> None:
    """Generate a diff between the current token set and the prior run.

    Always writes tokens/diff.json.
    """
    current = _load_staged(output_dir)
    prior = _load_prior_diff(output_dir)

    engine = JsonDiffEngine()
    diff_result = engine._run(current=current, prior=prior)

    tokens_dir = Path(output_dir) / "tokens"
    tokens_dir.mkdir(parents=True, exist_ok=True)
    (tokens_dir / "diff.json").write_text(
        json.dumps(diff_result, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def create_token_diff_agent() -> Agent:
    """Instantiate the Token Diff Agent (Agent 11 — Tier 3, Haiku)."""
    import os

    model = os.environ.get("DAF_TIER3_MODEL", "claude-haiku-4-20250514")
    return Agent(
        role="Token Diff Specialist",
        goal=(
            "Generate a structured change log comparing the current design-token set to the "
            "previous run. Detect added, modified, removed, and deprecated tokens so that "
            "consumers can react to token changes in a controlled manner."
        ),
        backstory=(
            "You are a version-control expert for design systems. You track changes between "
            "token releases so that breaking changes are surfaced early and documented "
            "transparently for consuming teams."
        ),
        verbose=False,
        allow_delegation=False,
        llm=model,
    )


def create_token_diff_task(
    output_dir: str,
    context_tasks: list[Task] | None = None,
) -> Task:
    """Build the diff task for the Token Engine Crew."""
    agent = create_token_diff_agent()
    task = Task(
        description=(
            f"Compare the current staged tokens in '{output_dir}/tokens/staged/' against "
            f"the previous diff stored in '{output_dir}/tokens/diff.json' (if any). "
            "Write an updated diff.json documenting all added, modified, removed, and "
            "deprecated tokens."
        ),
        expected_output=(
            "Diff complete. tokens/diff.json written with keys: "
            "is_initial_generation, added, modified, removed, deprecated."
        ),
        agent=agent,
        context=context_tasks or [],
    )
    task._run_diff = _run_diff  # type: ignore[attr-defined]
    task._output_dir = output_dir  # type: ignore[attr-defined]
    return task
