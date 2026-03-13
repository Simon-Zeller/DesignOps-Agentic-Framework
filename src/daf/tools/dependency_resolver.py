"""Agent 39 – DependencyResolver tool (Release Crew, Phase 6).

Wraps subprocess.run for npm install, tsc --noEmit, and npm test.
Returns {"status": "npm_unavailable"} when npm is not on $PATH.
Returns {"status": "success", "stdout": ...} on exit code 0.
Returns {"status": "failed", "exit_code": N, "stderr": ...} on non-zero exit.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


class DependencyResolver(BaseTool):
    """Wrap npm CLI commands with graceful Node.js unavailability handling."""

    name: str = Field(default="dependency_resolver")
    description: str = Field(
        default=(
            "Runs an npm command (e.g. 'npm install', 'tsc --noEmit', 'npm test') "
            "in the output_dir. Returns {status: 'npm_unavailable'} when npm is not "
            "on PATH, {status: 'success', stdout: ...} on exit 0, or "
            "{status: 'failed', exit_code: N, stderr: ...} on non-zero exit."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, command: str = "npm install", **kwargs: Any) -> dict[str, Any]:
        cwd = str(Path(self.output_dir)) if self.output_dir else None
        args = command.split()
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                cwd=cwd,
            )
        except (FileNotFoundError, OSError):
            return {"status": "npm_unavailable", "reason": "npm not found on PATH"}

        if result.returncode == 0:
            return {"status": "success", "stdout": result.stdout}
        return {
            "status": "failed",
            "exit_code": result.returncode,
            "stderr": result.stderr,
        }
