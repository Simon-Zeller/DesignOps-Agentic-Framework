"""Unit tests for MultiFormatSerializer tool (p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import json

import pytest


def test_multi_format_serializer_writes_all_three_files(tmp_path):
    """MultiFormatSerializer writes .cursorrules, copilot-instructions.md, and ai-context.json."""
    from daf.tools.multi_format_serializer import MultiFormatSerializer

    cursorrules = "# Cursor rules\nUse Button for all CTAs."
    copilot_instructions = "# GitHub Copilot Instructions\nAlways use Button."
    ai_context = {"components": [{"name": "Button"}]}

    serializer = MultiFormatSerializer()
    serializer._run(
        cursorrules=cursorrules,
        copilot_instructions=copilot_instructions,
        ai_context=ai_context,
        output_dir=str(tmp_path),
    )

    assert (tmp_path / ".cursorrules").exists()
    assert (tmp_path / "copilot-instructions.md").exists()
    assert (tmp_path / "ai-context.json").exists()


def test_multi_format_serializer_writes_valid_json(tmp_path):
    """MultiFormatSerializer writes valid JSON to ai-context.json."""
    from daf.tools.multi_format_serializer import MultiFormatSerializer

    ai_context = {"components": [{"name": "Button"}], "tokens": []}

    serializer = MultiFormatSerializer()
    serializer._run(
        cursorrules="rules",
        copilot_instructions="instructions",
        ai_context=ai_context,
        output_dir=str(tmp_path),
    )

    data = json.loads((tmp_path / "ai-context.json").read_text())
    assert isinstance(data, dict)
    assert "components" in data


def test_multi_format_serializer_writes_non_empty_markdown(tmp_path):
    """MultiFormatSerializer writes non-empty content to copilot-instructions.md."""
    from daf.tools.multi_format_serializer import MultiFormatSerializer

    serializer = MultiFormatSerializer()
    serializer._run(
        cursorrules="# Rules",
        copilot_instructions="# Copilot Instructions\nContent here.",
        ai_context={},
        output_dir=str(tmp_path),
    )

    content = (tmp_path / "copilot-instructions.md").read_text()
    assert len(content) > 0


def test_multi_format_serializer_handles_missing_upstream_file(tmp_path):
    """MultiFormatSerializer does not raise when ai_context is empty dict."""
    from daf.tools.multi_format_serializer import MultiFormatSerializer

    serializer = MultiFormatSerializer()
    # Should not raise
    serializer._run(
        cursorrules="",
        copilot_instructions="",
        ai_context={},
        output_dir=str(tmp_path),
    )
