"""Tests for CheckpointManager tool (p09-pipeline-orchestrator, TDD red phase)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from daf.tools.checkpoint_manager import CheckpointManager, CheckpointCorruptError


@pytest.fixture()
def cm() -> CheckpointManager:
    return CheckpointManager()


# ---------------------------------------------------------------------------
# test_checkpoint_create_writes_snapshot_and_manifest
# ---------------------------------------------------------------------------

def test_checkpoint_create_writes_snapshot_and_manifest(tmp_path: Path, cm: CheckpointManager) -> None:
    """Snapshot created after Phase 1 — files written and manifest recorded."""
    (tmp_path / "brand-profile.json").write_text('{"name": "Test"}')
    (tmp_path / "tokens").mkdir()
    (tmp_path / "tokens" / "base.tokens.json").write_text("{}")

    result = cm.create(output_dir=str(tmp_path), phase=1)

    checkpoints_dir = tmp_path / ".daf-checkpoints"
    assert checkpoints_dir.exists()

    # At least one phase-1-* directory exists
    snapshots = list(checkpoints_dir.glob("phase-1-*"))
    assert snapshots, "Expected a phase-1 snapshot directory"
    snapshot = snapshots[0]
    assert (snapshot / "brand-profile.json").exists()
    assert (snapshot / "tokens" / "base.tokens.json").exists()

    manifest_path = checkpoints_dir / "checkpoints.json"
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    entry = data[0]
    assert entry["phase"] == 1
    assert "timestamp" in entry
    assert "path" in entry
    assert "file_manifest" in entry
    assert len(entry["file_manifest"]) > 0

    # result dict from .create() contains at least phase and path
    assert result["phase"] == 1


# ---------------------------------------------------------------------------
# test_checkpoint_does_not_include_checkpoints_dir
# ---------------------------------------------------------------------------

def test_checkpoint_does_not_include_checkpoints_dir(tmp_path: Path, cm: CheckpointManager) -> None:
    """Snapshot must NOT contain a nested .daf-checkpoints/ dir."""
    # Simulate an output dir that already has a prior checkpoint
    existing_cp = tmp_path / ".daf-checkpoints" / "phase-1-prior"
    existing_cp.mkdir(parents=True)
    (existing_cp / "some-file.json").write_text("{}")

    (tmp_path / "brand-profile.json").write_text("{}")

    cm.create(output_dir=str(tmp_path), phase=2)

    checkpoints_dir = tmp_path / ".daf-checkpoints"
    snapshots = list(checkpoints_dir.glob("phase-2-*"))
    assert snapshots, "Expected a phase-2 snapshot directory"
    snapshot = snapshots[0]

    assert not (snapshot / ".daf-checkpoints").exists(), (
        "Snapshot must not include the .daf-checkpoints/ directory itself"
    )


# ---------------------------------------------------------------------------
# test_checkpoint_restore_overwrites_output_dir
# ---------------------------------------------------------------------------

def test_checkpoint_restore_overwrites_output_dir(tmp_path: Path, cm: CheckpointManager) -> None:
    """Restore must overwrite modifications made after the snapshot."""
    (tmp_path / "brand-profile.json").write_text('{"name": "Original"}')
    cm.create(output_dir=str(tmp_path), phase=1)

    # Simulate a modification
    (tmp_path / "brand-profile.json").write_text('{"name": "Modified"}')

    cm.restore(output_dir=str(tmp_path), phase=1)

    content = json.loads((tmp_path / "brand-profile.json").read_text())
    assert content["name"] == "Original"


# ---------------------------------------------------------------------------
# test_checkpoint_restore_raises_on_corrupt
# ---------------------------------------------------------------------------

def test_checkpoint_restore_raises_on_corrupt(tmp_path: Path, cm: CheckpointManager) -> None:
    """CheckpointCorruptError raised when a manifest file is missing from snapshot."""
    (tmp_path / "tokens").mkdir()
    token_file = tmp_path / "tokens" / "compiled" / "variables.css"
    token_file.parent.mkdir(parents=True)
    token_file.write_text(":root { --color-primary: #000; }")
    (tmp_path / "brand-profile.json").write_text("{}")

    cm.create(output_dir=str(tmp_path), phase=2)

    # Delete a file from the snapshot to corrupt it
    checkpoints_dir = tmp_path / ".daf-checkpoints"
    snapshots = list(checkpoints_dir.glob("phase-2-*"))
    snapshot = snapshots[0]
    corrupted = snapshot / "tokens" / "compiled" / "variables.css"
    corrupted.unlink()

    with pytest.raises(CheckpointCorruptError, match="variables.css"):
        cm.restore(output_dir=str(tmp_path), phase=2)


# ---------------------------------------------------------------------------
# test_get_last_valid_checkpoint_returns_highest_valid_phase
# ---------------------------------------------------------------------------

def test_get_last_valid_checkpoint_returns_highest_valid_phase(
    tmp_path: Path, cm: CheckpointManager
) -> None:
    """Returns the last intact checkpoint even when an intermediate one is corrupt."""
    (tmp_path / "brand-profile.json").write_text("{}")

    cm.create(output_dir=str(tmp_path), phase=1)
    cm.create(output_dir=str(tmp_path), phase=2)
    cm.create(output_dir=str(tmp_path), phase=3)

    # Corrupt phase 2 snapshot by deleting its files
    checkpoints_dir = tmp_path / ".daf-checkpoints"
    phase2_snaps = list(checkpoints_dir.glob("phase-2-*"))
    for snap in phase2_snaps:
        for f in snap.rglob("*"):
            if f.is_file():
                f.unlink()

    result = cm.get_last_valid_checkpoint(output_dir=str(tmp_path))
    assert result is not None
    assert result["phase"] == 3


# ---------------------------------------------------------------------------
# test_get_last_valid_checkpoint_returns_none_when_all_corrupt
# ---------------------------------------------------------------------------

def test_get_last_valid_checkpoint_returns_none_when_all_corrupt(
    tmp_path: Path, cm: CheckpointManager
) -> None:
    """Returns None when all checkpoints in the manifest are corrupt."""
    (tmp_path / "brand-profile.json").write_text("{}")
    cm.create(output_dir=str(tmp_path), phase=1)

    # Delete all files in the phase-1 snapshot
    checkpoints_dir = tmp_path / ".daf-checkpoints"
    for snap in checkpoints_dir.glob("phase-1-*"):
        for f in snap.rglob("*"):
            if f.is_file():
                f.unlink()

    result = cm.get_last_valid_checkpoint(output_dir=str(tmp_path))
    assert result is None


# ---------------------------------------------------------------------------
# test_checkpoint_cleanup_removes_all_snapshots
# ---------------------------------------------------------------------------

def test_checkpoint_cleanup_removes_all_snapshots(tmp_path: Path, cm: CheckpointManager) -> None:
    """cleanup() removes the entire .daf-checkpoints/ directory."""
    (tmp_path / "brand-profile.json").write_text("{}")

    cm.create(output_dir=str(tmp_path), phase=1)
    cm.create(output_dir=str(tmp_path), phase=2)
    cm.create(output_dir=str(tmp_path), phase=3)

    assert (tmp_path / ".daf-checkpoints").exists()
    cm.cleanup(output_dir=str(tmp_path))
    assert not (tmp_path / ".daf-checkpoints").exists()


# ---------------------------------------------------------------------------
# test_checkpoint_manager_handles_empty_output_dir
# ---------------------------------------------------------------------------

def test_checkpoint_manager_handles_empty_output_dir(tmp_path: Path, cm: CheckpointManager) -> None:
    """create() on an empty directory succeeds — empty snapshot and zero-file manifest."""
    result = cm.create(output_dir=str(tmp_path), phase=1)

    checkpoints_dir = tmp_path / ".daf-checkpoints"
    assert checkpoints_dir.exists()
    snapshots = list(checkpoints_dir.glob("phase-1-*"))
    assert snapshots

    manifest = json.loads((checkpoints_dir / "checkpoints.json").read_text())
    assert manifest[0]["file_manifest"] == {}
    assert result["phase"] == 1
