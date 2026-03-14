"""Token Ingestion Agent (Agent 7, Token Engine Crew).

Normalises incoming raw token files to W3C DTCG, detects duplicates and
naming conflicts, and stages tokens for validation.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from daf.tools.dtcg_formatter import WC3DTCGFormatter

_TIER_FILES = ("base.tokens.json", "semantic.tokens.json", "component.tokens.json")
_DTCG_REF_RE = re.compile(r"\{([a-z0-9._-]+)\}", re.IGNORECASE)


def _detect_duplicate_keys(raw_text: str) -> list[str]:
    """Parse raw JSON text and return any duplicate keys found at the same object level."""
    duplicates: list[str] = []

    def _object_pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        seen: set[str] = set()
        for key, _ in pairs:
            if not key.startswith("$") and key in seen:
                duplicates.append(key)
            seen.add(key)
        return dict(pairs)

    try:
        json.loads(raw_text, object_pairs_hook=_object_pairs_hook)
    except json.JSONDecodeError:
        pass
    return duplicates


def _ingest_tokens(output_dir: str) -> None:
    """Ingest and stage three DTCG token tier files.

    Raises:
        FileNotFoundError: if any of the three tier files is missing.
        ValueError: if any tier file contains duplicate keys.
    """
    od = Path(output_dir)
    tokens_dir = od / "tokens"
    staged_dir = tokens_dir / "staged"
    staged_dir.mkdir(parents=True, exist_ok=True)

    for tier_file in _TIER_FILES:
        src = tokens_dir / tier_file
        if not src.exists():
            raise FileNotFoundError(
                f"Required token tier file not found: {src}. "
                f"Ensure Agent 2 (Token Foundation) has completed successfully before running "
                f"the Token Engine Crew."
            )

        raw_text = src.read_text(encoding="utf-8")
        duplicates = _detect_duplicate_keys(raw_text)
        if duplicates:
            raise ValueError(
                f"duplicate key(s) detected in '{tier_file}': "
                f"{', '.join(duplicates)}. Each token key must be unique within a tier file."
            )

        # Stage (copy) the validated file
        dst = staged_dir / tier_file
        shutil.copy2(str(src), str(dst))


def create_token_ingestion_agent() -> Agent:
    """Instantiate the Token Ingestion Agent (Agent 7 — Tier 3, Haiku)."""
    import os

    model = os.environ.get("DAF_TIER3_MODEL", "anthropic/claude-sonnet-4-20250514")
    return Agent(
        role="Token Ingestion Specialist",
        goal=(
            "Normalise the three W3C DTCG token tier files (base, semantic, component) "
            "produced by Agent 2. Detect and report duplicate keys and naming conflicts. "
            "Stage the validated token files to tokens/staged/ for the Token Validation Agent."
        ),
        backstory=(
            "You are a data normalisation expert specialising in design token pipelines. "
            "Your critical first step in the Token Engine Crew ensures that only well-formed, "
            "conflict-free token files advance to validation and compilation."
        ),
        tools=[WC3DTCGFormatter()],
        llm=model,
        verbose=False,
    )


def create_token_ingestion_task(
    output_dir: str,
    context_tasks: list[Task] | None = None,
) -> Task:
    """Create Task T1: Ingest and stage token tier files."""
    return Task(
        description=(
            f"Ingest the three W3C DTCG token tier files from '{output_dir}/tokens/'. "
            "Check for missing files (raise FileNotFoundError) and duplicate keys (raise ValueError). "
            "Copy validated files to '{output_dir}/tokens/staged/'."
        ),
        expected_output=(
            "Three staged token files written to tokens/staged/: "
            "base.tokens.json, semantic.tokens.json, component.tokens.json."
        ),
        agent=create_token_ingestion_agent(),
        context=context_tasks or [],
    )
