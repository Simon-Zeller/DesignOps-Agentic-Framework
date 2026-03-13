"""Tests for decision_log_reader.read_decisions."""
import json
from daf.tools.decision_log_reader import read_decisions


def test_reads_decisions_from_summary(tmp_path):
    summary = {
        "archetype": "minimalist",
        "a11y_level": "AA",
        "decisions": [
            {
                "title": "Archetype Selection",
                "context": "Brand is minimal.",
                "decision": "Use minimalist archetype.",
                "consequences": "Fewer colors.",
            }
        ],
    }
    path = tmp_path / "generation-summary.json"
    path.write_text(json.dumps(summary))
    decisions = read_decisions(str(path))
    assert len(decisions) == 1
    assert decisions[0]["title"] == "Archetype Selection"


def test_returns_empty_list_when_no_decisions_key(tmp_path):
    path = tmp_path / "generation-summary.json"
    path.write_text(json.dumps({"archetype": "minimal"}))
    decisions = read_decisions(str(path))
    assert decisions == []


def test_returns_empty_list_when_file_missing(tmp_path):
    decisions = read_decisions(str(tmp_path / "nonexistent.json"))
    assert decisions == []
