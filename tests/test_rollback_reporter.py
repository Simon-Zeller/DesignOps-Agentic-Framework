"""Tests for RollbackReporter tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

import json
from pathlib import Path


def test_writes_rollback_log_json(tmp_path: Path) -> None:
    """Writes reports/rollback-log.json to output_dir."""
    from daf.tools.rollback_reporter import RollbackReporter

    reporter = RollbackReporter(output_dir=str(tmp_path))
    payload = json.dumps({
        "restored_phase": "token-engine",
        "failed_crew": "design-to-code",
        "reason": "exhausted retries",
    })
    reporter._run(payload)
    log_path = tmp_path / "reports" / "rollback-log.json"
    assert log_path.exists()


def test_rollback_log_contains_restored_phase_and_reason(tmp_path: Path) -> None:
    """rollback-log.json contains the restored_phase and reason fields."""
    from daf.tools.rollback_reporter import RollbackReporter

    reporter = RollbackReporter(output_dir=str(tmp_path))
    payload = json.dumps({
        "restored_phase": "token-engine",
        "failed_crew": "design-to-code",
        "reason": "exhausted retries",
    })
    reporter._run(payload)
    log_path = tmp_path / "reports" / "rollback-log.json"
    data = json.loads(log_path.read_text())
    # data may be a list (appended) or dict
    entry = data if isinstance(data, dict) else data[-1]
    assert entry["restored_phase"] == "token-engine"
    assert entry["reason"] == "exhausted retries"
