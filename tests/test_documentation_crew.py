"""Integration tests for create_documentation_crew(output_dir).kickoff()."""
import json

import yaml
from pathlib import Path
from unittest.mock import patch

import pytest

from daf.crews.documentation import create_documentation_crew

BUTTON_SPEC = {
    "component": "Button",
    "variants": ["primary", "secondary"],
    "states": {"default": {}, "disabled": {"terminal": True}},
    "props": {
        "label": {"type": "string", "required": True},
        "disabled": {"type": "boolean", "required": False, "default": False},
    },
    "tokens": {"background": "color.interactive.default"},
    "a11y": {"role": "button"},
}

BRAND_PROFILE = {"archetype": "minimalist", "a11y_level": "AA", "modular_scale": 1.25}

COMPILED_TOKENS = {
    "color.interactive.default": "#005FCC",
    "space.4": "16px",
}

GENERATION_SUMMARY = {
    "archetype": "minimalist",
    "decisions": [
        {
            "title": "Archetype Selection",
            "context": "Brand required minimal style.",
            "decision": "minimalist",
            "consequences": "Fewer tokens.",
        },
    ],
}


@pytest.fixture
def output_dir(tmp_path):
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "button.spec.yaml").write_text(yaml.dump(BUTTON_SPEC))
    (tmp_path / "tokens").mkdir()
    (tmp_path / "tokens" / "semantic.tokens.json").write_text(json.dumps(COMPILED_TOKENS))
    (tmp_path / "brand-profile.json").write_text(json.dumps(BRAND_PROFILE))
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "generation-summary.json").write_text(
        json.dumps(GENERATION_SUMMARY)
    )
    return str(tmp_path)


def test_crew_produces_all_docs(output_dir, tmp_path):
    with (
        patch("daf.agents.doc_generation._call_llm") as mock_doc,
        patch("daf.agents.token_catalog._call_llm") as mock_tok,
        patch("daf.agents.generation_narrative._call_llm") as mock_narr,
        patch("daf.agents.decision_record._call_llm") as mock_adr,
    ):
        mock_doc.return_value = "<Button />"
        mock_tok.return_value = "Usage description."
        mock_narr.return_value = "The design system was built minimally."
        mock_adr.return_value = "Fewer tokens result."
        crew = create_documentation_crew(output_dir)
        crew.kickoff()

    docs = tmp_path / "docs"
    assert (docs / "README.md").exists(), "docs/README.md not written"
    assert (docs / "components" / "Button.md").exists(), "component doc not written"
    assert (docs / "tokens" / "catalog.md").exists(), "token catalog not written"
    assert (docs / "decisions" / "generation-narrative.md").exists(), "narrative not written"
    assert (docs / "decisions" / "adr-archetype-selection.md").exists(), "ADR not written"
    assert (docs / "search-index.json").exists(), "search index not written"


def test_search_index_is_valid_json(output_dir, tmp_path):
    with (
        patch("daf.agents.doc_generation._call_llm") as mock_doc,
        patch("daf.agents.token_catalog._call_llm") as mock_tok,
        patch("daf.agents.generation_narrative._call_llm") as mock_narr,
        patch("daf.agents.decision_record._call_llm") as mock_adr,
    ):
        mock_doc.return_value = "<Button />"
        mock_tok.return_value = "Usage."
        mock_narr.return_value = "Narrative."
        mock_adr.return_value = "Consequence."
        create_documentation_crew(output_dir).kickoff()
    data = json.loads((tmp_path / "docs" / "search-index.json").read_text())
    assert isinstance(data, list)


def test_crew_kickoff_returns_without_error(output_dir):
    with (
        patch("daf.agents.doc_generation._call_llm", return_value="<Button />"),
        patch("daf.agents.token_catalog._call_llm", return_value="Usage."),
        patch("daf.agents.generation_narrative._call_llm", return_value="Narrative."),
        patch("daf.agents.decision_record._call_llm", return_value="Consequence."),
    ):
        crew = create_documentation_crew(output_dir)
        crew.kickoff()  # Must not raise
