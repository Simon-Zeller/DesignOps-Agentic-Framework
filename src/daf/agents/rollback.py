"""Rollback Agent (Agent 40) — evaluates checkpoint integrity and determines rollback scope.

Lightweight Agent 40 is instantiated by Agent 6 at pipeline start. Agent 6 holds
a reference to the CheckpointManager tool and calls it directly for checkpoint I/O.
"""
from __future__ import annotations

import os

from crewai import Agent

from daf.tools.checkpoint_manager import CheckpointManager


def create_rollback_agent() -> Agent:
    """Instantiate Agent 40: Rollback Agent (Tier 3 — Claude Haiku, classification)."""
    model = os.environ.get("DAF_TIER3_MODEL", "claude-haiku-4-20250414")
    return Agent(
        role="Rollback Specialist",
        goal=(
            "Evaluate checkpoint integrity and determine the correct rollback scope "
            "when the pipeline needs to retry from a prior phase boundary."
        ),
        backstory=(
            "You are a pipeline operations specialist. Your sole responsibility is to "
            "assess checkpoint validity (detect partial writes, missing manifest files, "
            "size mismatches) and determine which phase to roll back to when a cascade "
            "failure occurs. You work quickly and produce structured JSON decisions."
        ),
        tools=[CheckpointManager()],
        llm=model,
        verbose=False,
    )
