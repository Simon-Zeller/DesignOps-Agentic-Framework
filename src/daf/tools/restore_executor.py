"""Agent 40 – RestoreExecutor tool (Release Crew, Phase 6).

Accepts a phase name; raises FileNotFoundError if checkpoints/<phase_name>/
is absent; copies checkpoint contents back into output_dir, overwriting
current files.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


class RestoreExecutor(BaseTool):
    """Restore output_dir contents from a named checkpoint."""

    name: str = Field(default="restore_executor")
    description: str = Field(
        default=(
            "Accepts a phase name string. Restores output_dir from "
            "checkpoints/<phase_name>/. Raises FileNotFoundError when the "
            "snapshot does not exist."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, phase_name: str = "", **kwargs: Any) -> str:
        output_path = Path(self.output_dir)
        snapshot_dir = output_path / "checkpoints" / phase_name

        if not snapshot_dir.exists():
            raise FileNotFoundError(
                f"No checkpoint found for phase '{phase_name}' at {snapshot_dir}"
            )

        for item in snapshot_dir.iterdir():
            dest = output_path / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        return str(output_path)
