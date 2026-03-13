"""CheckpointManager — phase-boundary snapshot tool for the pipeline orchestrator.

Creates, validates, restores, and cleans up output-directory snapshots so that
the pipeline can resume from any phase boundary after a process crash.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field

CHECKPOINTS_DIR = ".daf-checkpoints"
MANIFEST_FILE = "checkpoints.json"


class CheckpointCorruptError(Exception):
    """Raised when a checkpoint snapshot fails integrity validation."""


def _iso_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _build_file_manifest(snapshot_dir: Path) -> dict[str, int]:
    """Return {relative_path: size_bytes} for every file in snapshot_dir."""
    manifest: dict[str, int] = {}
    for file_path in sorted(snapshot_dir.rglob("*")):
        if file_path.is_file():
            rel = str(file_path.relative_to(snapshot_dir))
            manifest[rel] = file_path.stat().st_size
    return manifest


def _is_valid_snapshot(snapshot_dir: Path, file_manifest: dict[str, int]) -> bool:
    """Return True if every file in file_manifest exists in snapshot_dir."""
    for rel_path in file_manifest:
        if not (snapshot_dir / rel_path).exists():
            return False
    return True


class CheckpointManager(BaseTool):
    """Deterministic tool for creating, restoring, and cleaning up phase snapshots."""

    name: str = Field(default="checkpoint_manager")
    description: str = Field(
        default=(
            "Creates and restores phase-boundary snapshots of the output directory. "
            "Use create() at each phase boundary, restore() to roll back, "
            "get_last_valid_checkpoint() to find where to resume, and "
            "cleanup() after a successful run."
        )
    )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, output_dir: str, phase: int) -> dict[str, Any]:
        """Snapshot the output directory at a phase boundary.

        Copies all contents of *output_dir* (excluding ``.daf-checkpoints/``)
        into ``<output_dir>/.daf-checkpoints/phase-<N>-<ts>/`` and appends an
        entry to ``checkpoints.json``.

        Returns the new manifest entry dict.
        """
        od = Path(output_dir)
        ts = _iso_timestamp()
        snapshot_name = f"phase-{phase}-{ts}"
        checkpoints_root = od / CHECKPOINTS_DIR
        snapshot_dir = checkpoints_root / snapshot_name
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Copy every item except .daf-checkpoints itself
        for item in od.iterdir():
            if item.name == CHECKPOINTS_DIR:
                continue
            dest = snapshot_dir / item.name
            if item.is_dir():
                shutil.copytree(str(item), str(dest), dirs_exist_ok=True)
            else:
                shutil.copy2(str(item), str(dest))

        file_manifest = _build_file_manifest(snapshot_dir)
        entry: dict[str, Any] = {
            "phase": phase,
            "timestamp": ts,
            "path": str(snapshot_dir),
            "file_manifest": file_manifest,
        }

        manifest_path = checkpoints_root / MANIFEST_FILE
        existing: list[dict] = []
        if manifest_path.exists():
            try:
                existing = json.loads(manifest_path.read_text())
            except (json.JSONDecodeError, OSError):
                existing = []
        existing.append(entry)
        manifest_path.write_text(json.dumps(existing, indent=2))

        return entry

    def restore(self, output_dir: str, phase: int) -> None:
        """Restore the output directory to the state captured at *phase*.

        Validates the snapshot's manifest before copying.  Raises
        ``CheckpointCorruptError`` if any recorded file is missing.
        """
        od = Path(output_dir)
        entry = self._find_entry(od, phase)
        if entry is None:
            raise CheckpointCorruptError(f"No checkpoint found for phase {phase}")

        snapshot_dir = Path(entry["path"])
        file_manifest: dict[str, int] = entry.get("file_manifest", {})

        # Validate all manifest files exist in the snapshot
        for rel_path in file_manifest:
            if not (snapshot_dir / rel_path).exists():
                raise CheckpointCorruptError(
                    f"Checkpoint phase-{phase} is corrupt: missing file {rel_path!r}"
                )

        # Overwrite output_dir with snapshot contents (skip .daf-checkpoints)
        checkpoints_root = od / CHECKPOINTS_DIR
        for item in od.iterdir():
            if item.name == CHECKPOINTS_DIR:
                continue
            if item.is_dir():
                shutil.rmtree(str(item))
            else:
                item.unlink()

        for item in snapshot_dir.iterdir():
            dest = od / item.name
            if item.is_dir():
                shutil.copytree(str(item), str(dest), dirs_exist_ok=True)
            else:
                shutil.copy2(str(item), str(dest))

    def get_last_valid_checkpoint(self, output_dir: str) -> dict[str, Any] | None:
        """Return the checkpoint entry for the highest valid phase, or None."""
        od = Path(output_dir)
        manifest_path = od / CHECKPOINTS_DIR / MANIFEST_FILE
        if not manifest_path.exists():
            return None

        try:
            entries: list[dict] = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError):
            return None

        # Sort by phase descending so we return the highest valid one
        sorted_entries = sorted(entries, key=lambda e: e.get("phase", 0), reverse=True)
        for entry in sorted_entries:
            snapshot_dir = Path(entry.get("path", ""))
            file_manifest: dict[str, int] = entry.get("file_manifest", {})
            if _is_valid_snapshot(snapshot_dir, file_manifest):
                return entry

        return None

    def cleanup(self, output_dir: str) -> None:
        """Remove the entire ``.daf-checkpoints/`` directory."""
        checkpoints_root = Path(output_dir) / CHECKPOINTS_DIR
        if checkpoints_root.exists():
            shutil.rmtree(str(checkpoints_root))

    # ------------------------------------------------------------------
    # BaseTool._run (required by CrewAI)
    # ------------------------------------------------------------------

    def _run(self, action: str, output_dir: str, phase: int = 0) -> str:
        """Dispatch to create / restore / cleanup / get_last_valid_checkpoint."""
        if action == "create":
            result = self.create(output_dir=output_dir, phase=phase)
            return json.dumps(result)
        if action == "restore":
            self.restore(output_dir=output_dir, phase=phase)
            return f"Restored phase-{phase} checkpoint."
        if action == "cleanup":
            self.cleanup(output_dir=output_dir)
            return "Checkpoints cleaned up."
        if action == "get_last_valid":
            result = self.get_last_valid_checkpoint(output_dir=output_dir)
            return json.dumps(result)
        raise ValueError(f"Unknown CheckpointManager action: {action!r}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_entry(self, od: Path, phase: int) -> dict[str, Any] | None:
        manifest_path = od / CHECKPOINTS_DIR / MANIFEST_FILE
        if not manifest_path.exists():
            return None
        try:
            entries: list[dict] = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError):
            return None
        for entry in entries:
            if entry.get("phase") == phase:
                return entry
        return None
