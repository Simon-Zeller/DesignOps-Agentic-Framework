"""Rollback Agent (Agent 40) – Generation checkpoint manager (Release Crew, Phase 6).

Agent 40 is instantiated by Agent 6 (First Publish Agent) at pipeline start.
It maintains checkpoints at each pipeline phase boundary and restores to the
last known-good snapshot when a crew fails catastrophically.

Factory signature: create_rollback_agent(model=None, output_dir="") → Agent
Both positional and keyword invocation are supported for backwards compatibility.
"""
from __future__ import annotations

import os

from crewai import Agent

from daf.tools.checkpoint_creator import CheckpointCreator
from daf.tools.restore_executor import RestoreExecutor
from daf.tools.rollback_reporter import RollbackReporter


def create_rollback_agent(model: str | None = None, output_dir: str = "") -> Agent:
    """Agent 40 – Generation Checkpoint Manager (Release Crew, Phase 6)."""
    if model is None:
        model = os.environ.get("DAF_TIER3_MODEL", "claude-haiku-4-20250414")
    return Agent(
        role="Generation checkpoint manager",
        goal=(
            "Maintain phase-boundary snapshots of the output directory. "
            "Before each crew runs, create a checkpoint snapshot. "
            "When a crew exhausts its retry budget, restore from the last "
            "known-good checkpoint and report what was rolled back and why."
        ),
        backstory=(
            "You are a pipeline resilience specialist. Your job is to ensure that "
            "pipeline failures never result in a corrupted or unusable output directory. "
            "You snapshot state before every crew run and can restore the output directory "
            "to any prior phase boundary on demand."
        ),
        tools=[
            CheckpointCreator(output_dir=output_dir),
            RestoreExecutor(output_dir=output_dir),
            RollbackReporter(output_dir=output_dir),
        ],
        llm=model,
        verbose=False,
    )
