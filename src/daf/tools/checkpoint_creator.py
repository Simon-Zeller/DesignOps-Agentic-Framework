"""Agent 40 – CheckpointCreator tool (Release Crew, Phase 6).

Accepts a phase name; creates checkpoints/<phase_name>/ inside output_dir
if absent; copies current output_dir contents into it (excluding the
checkpoints/ directory itself to avoid recursion).
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


class CheckpointCreator(BaseTool):
    """Snapshot output_dir contents to checkpoints/<phase_name>/."""

    name: str = Field(default="checkpoint_creator")
    description: str = Field(
        default=(
            "Accepts a phase name string. Creates checkpoints/<phase_name>/ inside "
            "output_dir and copies all current output_dir contents into it, excluding "
            "the checkpoints/ directory itself."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, phase_name: str = "", **kwargs: Any) -> str:
        output_path = Path(self.output_dir)
        checkpoints_root = output_path / "checkpoints"
        checkpoints_root.mkdir(parents=True, exist_ok=True)

        snapshot_dir = checkpoints_root / phase_name
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        for item in output_path.iterdir():
            if item.name == "checkpoints":
                continue
            dest = snapshot_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        return str(snapshot_dir)
