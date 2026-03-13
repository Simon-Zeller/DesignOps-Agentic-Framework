"""Shared StubCrew base class for downstream crew stubs (p09).

Provides a minimal .kickoff() interface without requiring a real LLM.
Each stub crew returns a StubCrew instance that writes the minimum
expected output files when kickoff() is called.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any


class StubCrew:
    """Lightweight stub that mimics CrewAI Crew's kickoff() interface."""

    def __init__(self, name: str, run_fn: Callable[[], None]) -> None:
        self._name = name
        self._run_fn = run_fn

    def kickoff(self, *args: Any, **kwargs: Any) -> str:
        """Execute the stub task and return a completion message."""
        self._run_fn()
        return f"{self._name} stub completed."
