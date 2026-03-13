"""Tests for RestoreExecutor tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path

import pytest


def test_restore_copies_checkpoint_back_to_output_dir(tmp_path: Path) -> None:
    """Restores checkpoint contents back into output_dir."""
    checkpoint_dir = tmp_path / "checkpoints" / "token-engine"
    (checkpoint_dir / "reports").mkdir(parents=True)
    (checkpoint_dir / "reports" / "generation-summary.json").write_text('{"restored": true}')

    from daf.tools.restore_executor import RestoreExecutor

    executor = RestoreExecutor(output_dir=str(tmp_path))
    executor._run("token-engine")
    restored = tmp_path / "reports" / "generation-summary.json"
    assert restored.exists()
    assert '"restored": true' in restored.read_text()


def test_raises_file_not_found_when_snapshot_missing(tmp_path: Path) -> None:
    """Raises FileNotFoundError when snapshot directory does not exist."""
    from daf.tools.restore_executor import RestoreExecutor

    executor = RestoreExecutor(output_dir=str(tmp_path))
    with pytest.raises(FileNotFoundError):
        executor._run("ds-bootstrap")
