"""Tests for CheckpointCreator tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path


def test_snapshot_creates_checkpoint_directory(tmp_path: Path) -> None:
    """Creates checkpoints/<phase_name>/ directory in output_dir."""
    from daf.tools.checkpoint_creator import CheckpointCreator

    creator = CheckpointCreator(output_dir=str(tmp_path))
    creator._run("token-engine")
    assert (tmp_path / "checkpoints" / "token-engine").is_dir()


def test_snapshot_copies_output_dir_contents(tmp_path: Path) -> None:
    """Snapshot copies output_dir contents into the checkpoint directory."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "generation-summary.json").write_text('{"stub": true}')

    from daf.tools.checkpoint_creator import CheckpointCreator

    creator = CheckpointCreator(output_dir=str(tmp_path))
    creator._run("ds-bootstrap")
    snapshot = tmp_path / "checkpoints" / "ds-bootstrap"
    assert (snapshot / "reports" / "generation-summary.json").exists()


def test_creates_checkpoints_dir_if_absent(tmp_path: Path) -> None:
    """Creates checkpoints/ parent directory when it doesn't exist."""
    from daf.tools.checkpoint_creator import CheckpointCreator

    creator = CheckpointCreator(output_dir=str(tmp_path))
    creator._run("phase-test")
    assert (tmp_path / "checkpoints").is_dir()
