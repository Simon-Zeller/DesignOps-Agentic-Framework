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


def test_appends_to_existing_log(tmp_path: Path) -> None:
    """Subsequent calls append to rollback-log.json rather than overwriting."""
    from daf.tools.rollback_reporter import RollbackReporter

    reporter = RollbackReporter(output_dir=str(tmp_path))
    reporter._run(json.dumps({"restored_phase": "phase-1", "reason": "first"}))
    reporter._run(json.dumps({"restored_phase": "phase-2", "reason": "second"}))
    log_path = tmp_path / "reports" / "rollback-log.json"
    data = json.loads(log_path.read_text())
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["restored_phase"] == "phase-1"
    assert data[1]["restored_phase"] == "phase-2"


def test_handles_malformed_report_json(tmp_path: Path) -> None:
    """Malformed input is stored as a raw entry without raising."""
    from daf.tools.rollback_reporter import RollbackReporter

    reporter = RollbackReporter(output_dir=str(tmp_path))
    reporter._run("not valid json {{")
    log_path = tmp_path / "reports" / "rollback-log.json"
    data = json.loads(log_path.read_text())
    entry = data[-1] if isinstance(data, list) else data
    assert "raw" in entry
    assert entry["raw"] == "not valid json {{"


def test_appends_to_existing_dict_log(tmp_path: Path) -> None:
    """If rollback-log.json contains a plain dict it is wrapped before appending."""
    from daf.tools.rollback_reporter import RollbackReporter

    log_path = tmp_path / "reports" / "rollback-log.json"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(json.dumps({"restored_phase": "old", "reason": "pre-existing"}))

    reporter = RollbackReporter(output_dir=str(tmp_path))
    reporter._run(json.dumps({"restored_phase": "new", "reason": "appended"}))
    data = json.loads(log_path.read_text())
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["restored_phase"] == "old"
    assert data[1]["restored_phase"] == "new"
