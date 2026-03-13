"""Tests for doc_generation.run_doc_generation."""
import json

import yaml
from pathlib import Path
from unittest.mock import patch

import pytest

from daf.agents.doc_generation import run_doc_generation

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

COMPILED_TOKENS = {"color.interactive.default": "#005FCC"}


@pytest.fixture
def output_dir(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "button.spec.yaml").write_text(yaml.dump(BUTTON_SPEC))
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    (tokens / "semantic.tokens.json").write_text(json.dumps(COMPILED_TOKENS))
    return str(tmp_path)


def test_creates_component_doc_file(output_dir, tmp_path):
    with patch("daf.agents.doc_generation._call_llm") as mock_llm:
        mock_llm.return_value = "// Example usage\n<Button label='Hello' />"
        run_doc_generation(output_dir)
    assert (tmp_path / "docs" / "components" / "Button.md").exists()


def test_component_doc_contains_prop_table(output_dir, tmp_path):
    with patch("daf.agents.doc_generation._call_llm") as mock_llm:
        mock_llm.return_value = "<Button />"
        run_doc_generation(output_dir)
    content = (tmp_path / "docs" / "components" / "Button.md").read_text()
    assert "label" in content and "disabled" in content


def test_creates_readme(output_dir, tmp_path):
    with patch("daf.agents.doc_generation._call_llm") as mock_llm:
        mock_llm.return_value = "<Button />"
        run_doc_generation(output_dir)
    assert (tmp_path / "docs" / "README.md").exists()


def test_readme_lists_button_component(output_dir, tmp_path):
    with patch("daf.agents.doc_generation._call_llm") as mock_llm:
        mock_llm.return_value = "<Button />"
        run_doc_generation(output_dir)
    content = (tmp_path / "docs" / "README.md").read_text()
    assert "Button" in content
