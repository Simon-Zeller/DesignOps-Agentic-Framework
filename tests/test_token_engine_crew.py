"""Integration tests for Token Engine Crew — TDD red phase."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


REQUIRED_OUTPUTS = [
    "tokens/staged/base.tokens.json",
    "tokens/staged/semantic.tokens.json",
    "tokens/staged/component.tokens.json",
    "tokens/compiled/variables.css",
    "tokens/compiled/variables-light.css",
    "tokens/compiled/variables-dark.css",
    "tokens/compiled/variables.scss",
    "tokens/compiled/tokens.ts",
    "tokens/compiled/tokens.json",
    "tokens/diff.json",
    "tokens/integrity-report.json",
]


@pytest.fixture
def valid_token_input(tmp_path):
    """Pre-built fixture with three valid DTCG tier files."""
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir(parents=True, exist_ok=True)
    base = {
        "color": {
            "neutral": {
                "50": {"$type": "color", "$value": "#F5F5F5"},
                "900": {"$type": "color", "$value": "#1A1A1A"},
                "950": {"$type": "color", "$value": "#0A0A0A"},
            },
            "brand": {
                "primary": {"$type": "color", "$value": "#005FCC"},
            },
        }
    }
    semantic = {
        "color": {
            "interactive": {
                "default": {
                    "$type": "color",
                    "$value": "{color.brand.primary}",
                    "$extensions": {
                        "com.daf.themes": {
                            "light": "{color.brand.primary}",
                            "dark": "{color.brand.primary}",
                        }
                    },
                },
            },
            "background": {
                "surface": {
                    "$type": "color",
                    "$value": "{color.neutral.50}",
                    "$extensions": {
                        "com.daf.themes": {
                            "light": "{color.neutral.50}",
                            "dark": "{color.neutral.900}",
                        }
                    },
                },
            },
        }
    }
    component = {
        "button": {
            "background": {"$type": "color", "$value": "{color.interactive.default}"},
        }
    }
    (tokens_dir / "base.tokens.json").write_text(json.dumps(base))
    (tokens_dir / "semantic.tokens.json").write_text(json.dumps(semantic))
    (tokens_dir / "component.tokens.json").write_text(json.dumps(component))
    return tmp_path


@pytest.fixture
def brand_profile():
    return {
        "name": "TestBrand",
        "archetype": "enterprise-b2b",
        "themes": {"modes": ["light", "dark"], "defaultTheme": "light"},
        "accessibility": "AA",
    }


def test_full_crew_run_valid_tokens_produces_all_outputs(valid_token_input, brand_profile):
    """Full Token Engine Crew produces all required I/O contract outputs."""
    from daf.crews.token_engine import create_token_engine_crew

    crew = create_token_engine_crew(
        output_dir=str(valid_token_input),
        brand_profile=brand_profile,
    )
    crew.kickoff()

    for relative_path in REQUIRED_OUTPUTS:
        full_path = valid_token_input / relative_path
        assert full_path.exists(), f"Expected output missing: {relative_path}"
        assert full_path.stat().st_size > 0, f"Expected non-empty output: {relative_path}"

    rejection = valid_token_input / "tokens" / "validation-rejection.json"
    assert not rejection.exists(), "No rejection file should exist for valid tokens"


def test_full_crew_run_invalid_tokens_writes_rejection_and_no_compiled(tmp_path, brand_profile):
    """Invalid tokens (missing $type) produce rejection file; compiled/ absent."""
    from daf.crews.token_engine import create_token_engine_crew

    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir(parents=True, exist_ok=True)
    # Deliberately invalid: token missing $type
    bad_base = {
        "color": {
            "brand": {
                "primary": {"$value": "#005FCC"},  # missing $type
            }
        }
    }
    (tokens_dir / "base.tokens.json").write_text(json.dumps(bad_base))
    (tokens_dir / "semantic.tokens.json").write_text(json.dumps({}))
    (tokens_dir / "component.tokens.json").write_text(json.dumps({}))

    crew = create_token_engine_crew(
        output_dir=str(tmp_path),
        brand_profile=brand_profile,
    )
    with pytest.raises(Exception):
        crew.kickoff()

    rejection = tmp_path / "tokens" / "validation-rejection.json"
    assert rejection.exists(), "Rejection file must be written for invalid tokens"
    data = json.loads(rejection.read_text())
    assert data["fatal_count"] >= 1

    # Compiled output should not exist
    compiled = tmp_path / "tokens" / "compiled"
    if compiled.exists():
        css_files = list(compiled.glob("variables*.css"))
        assert len(css_files) == 0, "No compiled CSS should be produced for invalid tokens"
