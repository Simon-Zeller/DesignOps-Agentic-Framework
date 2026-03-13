"""Tests for CodemodTemplateGenerator tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

import json
from pathlib import Path


def test_generates_before_and_after_snippets(tmp_path: Path) -> None:
    """Output contains both 'before' and 'after' code blocks."""
    from daf.tools.codemod_template_generator import CodemodTemplateGenerator

    gen = CodemodTemplateGenerator(output_dir=str(tmp_path))
    payload = json.dumps({"element": "button", "ds_component": "Button"})
    result = gen._run(payload)
    result_lower = result.lower()
    assert "before" in result_lower
    assert "after" in result_lower


def test_output_is_markdown_string(tmp_path: Path) -> None:
    """Output is a non-empty Markdown string with code fences."""
    from daf.tools.codemod_template_generator import CodemodTemplateGenerator

    gen = CodemodTemplateGenerator(output_dir=str(tmp_path))
    payload = json.dumps({"element": "input", "ds_component": "Input"})
    result = gen._run(payload)
    assert isinstance(result, str)
    assert "```" in result
