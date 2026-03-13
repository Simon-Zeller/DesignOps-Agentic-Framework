"""StatusReporter — structured stdout progress reporter for the pipeline orchestrator."""
from __future__ import annotations

import sys
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


class StatusReporter(BaseTool):
    """Deterministic tool that emits structured progress to stdout."""

    name: str = Field(default="status_reporter")
    description: str = Field(
        default="Emits structured pipeline progress messages to stdout."
    )

    def phase_start(self, crew: str, phase: int) -> None:
        self._emit("phase_start", crew=crew, phase=phase)

    def phase_complete(self, crew: str, phase: int, status: str) -> None:
        self._emit("phase_complete", crew=crew, phase=phase, status=status)

    def phase_retry(self, crew: str, phase: int, attempt: int) -> None:
        self._emit("phase_retry", crew=crew, phase=phase, attempt=attempt)

    def phase_failure(self, crew: str, phase: int, reason: str) -> None:
        self._emit("phase_failure", crew=crew, phase=phase, reason=reason)

    def _emit(self, event: str, **kwargs: Any) -> None:
        parts = " ".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"[daf:{event}] {parts}", file=sys.stdout, flush=True)

    def _run(self, event: str, **kwargs: Any) -> str:
        self._emit(event, **kwargs)
        return f"Emitted {event}"
