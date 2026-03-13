"""Tests for decision_record.run_decision_records."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from daf.agents.decision_record import run_decision_records

GENERATION_SUMMARY = {
    "decisions": [
        {
            "title": "Archetype Selection",
            "context": "Brand context.",
            "decision": "minimalist",
            "consequences": "Fewer tokens.",
        },
        {
            "title": "Token Scale Algorithm",
            "context": "Scale context.",
            "decision": "1.25 ratio.",
            "consequences": "Harmonious scale.",
        },
    ]
}


@pytest.fixture
def output_dir(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "generation-summary.json").write_text(json.dumps(GENERATION_SUMMARY))
    return str(tmp_path)


def test_creates_adr_for_each_decision(output_dir, tmp_path):
    with patch("daf.agents.decision_record._call_llm") as mock_llm:
        mock_llm.return_value = "Expanded consequences."
        run_decision_records(output_dir)
    decisions_dir = tmp_path / "docs" / "decisions"
    adr_files = list(decisions_dir.glob("adr-*.md"))
    assert len(adr_files) == 2


def test_adr_filename_is_slugified(output_dir, tmp_path):
    with patch("daf.agents.decision_record._call_llm") as mock_llm:
        mock_llm.return_value = "Consequence."
        run_decision_records(output_dir)
    assert (tmp_path / "docs" / "decisions" / "adr-archetype-selection.md").exists()


def test_fallback_adr_created_when_no_decisions(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "generation-summary.json").write_text(json.dumps({}))
    with patch("daf.agents.decision_record._call_llm") as mock_llm:
        mock_llm.return_value = "No decisions."
        run_decision_records(str(tmp_path))
    assert (tmp_path / "docs" / "decisions" / "adr-no-decisions.md").exists()
