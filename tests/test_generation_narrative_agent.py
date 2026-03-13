"""Tests for generation_narrative.run_generation_narrative."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from daf.agents.generation_narrative import run_generation_narrative

BRAND_PROFILE = {"archetype": "minimalist", "a11y_level": "AA", "modular_scale": 1.25}
GENERATION_SUMMARY = {
    "archetype": "minimalist",
    "decisions": [
        {
            "title": "Archetype Selection",
            "context": "Brand required minimal style.",
            "decision": "minimalist",
            "consequences": "Fewer colors.",
        }
    ],
}


@pytest.fixture
def output_dir(tmp_path):
    (tmp_path / "brand-profile.json").write_text(json.dumps(BRAND_PROFILE))
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "generation-summary.json").write_text(json.dumps(GENERATION_SUMMARY))
    return str(tmp_path)


def test_creates_narrative_file(output_dir, tmp_path):
    with patch("daf.agents.generation_narrative._call_llm") as mock_llm:
        mock_llm.return_value = "The design system was built with a minimalist philosophy."
        run_generation_narrative(output_dir)
    assert (tmp_path / "docs" / "decisions" / "generation-narrative.md").exists()


def test_narrative_contains_llm_output(output_dir, tmp_path):
    with patch("daf.agents.generation_narrative._call_llm") as mock_llm:
        mock_llm.return_value = "Unique narrative prose for testing."
        run_generation_narrative(output_dir)
    content = (tmp_path / "docs" / "decisions" / "generation-narrative.md").read_text()
    assert "Unique narrative prose for testing." in content


def test_narrative_created_when_no_summary(tmp_path):
    (tmp_path / "brand-profile.json").write_text(json.dumps(BRAND_PROFILE))
    with patch("daf.agents.generation_narrative._call_llm") as mock_llm:
        mock_llm.return_value = "Fallback narrative."
        run_generation_narrative(str(tmp_path))
    assert (tmp_path / "docs" / "decisions" / "generation-narrative.md").exists()
