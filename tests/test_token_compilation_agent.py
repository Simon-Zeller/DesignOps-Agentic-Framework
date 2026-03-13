"""Unit tests for Token Compilation Agent (Agent 9) — TDD red phase."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def staged_tokens(tmp_path):
    """Write staged tokens suitable for compilation."""
    staged = tmp_path / "tokens" / "staged"
    staged.mkdir(parents=True, exist_ok=True)
    base = {"color": {"brand": {"primary": {"$type": "color", "$value": "#005FCC"}}}}
    semantic = {
        "color": {
            "interactive": {
                "default": {
                    "$type": "color",
                    "$value": "{color.brand.primary}",
                    "$extensions": {
                        "com.daf.themes": {"light": "{color.brand.primary}", "dark": "{color.brand.primary}"}
                    },
                }
            }
        }
    }
    (staged / "base.tokens.json").write_text(json.dumps(base))
    (staged / "semantic.tokens.json").write_text(json.dumps(semantic))
    (staged / "component.tokens.json").write_text(json.dumps({}))
    return tmp_path


@pytest.fixture
def brand_profile_dict():
    return {
        "name": "TestBrand",
        "archetype": "enterprise-b2b",
        "themes": {"modes": ["light", "dark"], "defaultTheme": "light"},
        "accessibility": "AA",
    }


def test_valid_staged_tokens_produce_all_output_files(staged_tokens, brand_profile_dict):
    """Compilation produces variables.css, .scss, tokens.ts, tokens.json."""
    from daf.agents.token_compilation import _compile_tokens

    _compile_tokens(str(staged_tokens), brand_profile=brand_profile_dict)

    compiled = staged_tokens / "tokens" / "compiled"
    assert (compiled / "variables.css").exists()
    assert (compiled / "variables.scss").exists()
    assert (compiled / "tokens.ts").exists()
    assert (compiled / "tokens.json").exists()


def test_per_theme_css_files_generated(staged_tokens, brand_profile_dict):
    """Per-theme CSS files are written for each declared theme."""
    from daf.agents.token_compilation import _compile_tokens

    _compile_tokens(str(staged_tokens), brand_profile=brand_profile_dict)

    compiled = staged_tokens / "tokens" / "compiled"
    assert (compiled / "variables-light.css").exists()
    assert (compiled / "variables-dark.css").exists()


def test_compiler_error_propagates_as_task_failure(staged_tokens, brand_profile_dict):
    """RuntimeError from compiler is re-raised."""
    from daf.agents.token_compilation import _compile_tokens

    with patch("daf.tools.style_dictionary_compiler.StyleDictionaryCompiler._run") as mock_run:
        mock_run.side_effect = RuntimeError("unresolvable reference: {color.brand.nonexistent}")
        with pytest.raises(RuntimeError, match="unresolvable"):
            _compile_tokens(str(staged_tokens), brand_profile=brand_profile_dict)


def test_missing_theme_extension_falls_back_to_default_value(tmp_path, brand_profile_dict):
    """Token without theme extension for declared theme falls back to $value."""
    from daf.agents.token_compilation import _compile_tokens

    staged = tmp_path / "tokens" / "staged"
    staged.mkdir(parents=True, exist_ok=True)
    base = {"color": {"brand": {"primary": {"$type": "color", "$value": "#005FCC"}}}}
    # No $extensions.com.daf.themes.dark
    semantic = {
        "color": {
            "text": {
                "default": {
                    "$type": "color",
                    "$value": "{color.brand.primary}",
                    "$extensions": {
                        "com.daf.themes": {"light": "{color.brand.primary}"}
                        # dark is missing
                    },
                }
            }
        }
    }
    (staged / "base.tokens.json").write_text(json.dumps(base))
    (staged / "semantic.tokens.json").write_text(json.dumps(semantic))
    (staged / "component.tokens.json").write_text(json.dumps({}))

    # Should not raise; should fall back to $value for missing dark theme
    _compile_tokens(str(tmp_path), brand_profile=brand_profile_dict)
    compiled = tmp_path / "tokens" / "compiled"
    assert (compiled / "variables-dark.css").exists()
