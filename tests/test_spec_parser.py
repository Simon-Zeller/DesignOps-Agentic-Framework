"""Unit tests for spec_parser — valid YAML parse and malformed YAML warning."""
from __future__ import annotations

import logging
from pathlib import Path


def test_parses_valid_spec_yaml(tmp_path):
    """A valid spec YAML is parsed into a structured dict with expected keys."""
    from daf.tools.spec_parser import parse_spec

    spec_content = """\
component: Button
variants:
  - primary
  - secondary
states:
  - default
  - hover
  - disabled
composedOf:
  - Pressable
  - Text
tokens:
  background: color.interactive.default
  foreground: color.interactive.foreground
"""
    spec_file = tmp_path / "button.spec.yaml"
    spec_file.write_text(spec_content)

    result = parse_spec(str(spec_file))
    assert result is not None
    assert result["component"] == "Button"
    assert "variants" in result
    assert "states" in result
    assert "composedOf" in result
    assert "tokens" in result


def test_malformed_yaml_returns_none_with_warning(tmp_path, caplog):
    """Malformed YAML returns None and logs a warning without raising."""
    from daf.tools.spec_parser import parse_spec

    bad_file = tmp_path / "bad.spec.yaml"
    bad_file.write_text("key: [unclosed")

    with caplog.at_level(logging.WARNING):
        result = parse_spec(str(bad_file))

    assert result is None
    assert any("warning" in r.levelname.lower() or "warn" in r.message.lower() for r in caplog.records) or len(caplog.records) > 0
