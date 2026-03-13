"""Integration test for Component Factory Crew."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from daf.crews.component_factory import create_component_factory_crew


BUTTON_TSX = """
import React from 'react';
import { Pressable, Text } from '../../primitives';

export function Button({ label, disabled, onPress }) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      aria-disabled={disabled}
      style={{
        backgroundColor: 'var(--color-interactive-default)',
        borderRadius: 'var(--radius-md)',
        paddingLeft: 'var(--space-4)',
        paddingRight: 'var(--space-4)',
      }}
    >
      <Text style={{ color: 'var(--color-interactive-foreground)' }}>{label}</Text>
    </Pressable>
  );
}

export default Button;
"""

BUTTON_TEST_TSX = """
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders', () => {});
});

// @accessibility-placeholder
"""

BUTTON_SPEC = {
    "component": "Button",
    "variants": ["primary", "secondary"],
    "states": {
        "default": {"transitions": ["hover", "focused", "disabled"]},
        "hover": {"transitions": ["default", "focused"]},
        "focused": {"transitions": ["default", "hover"]},
        "disabled": {"terminal": True, "transitions": []},
    },
    "tokens": {
        "background": "color.interactive.default",
        "foreground": "color.interactive.foreground",
        "borderRadius": "radius.md",
    },
    "a11y": {"role": "button", "label": True},
}

COMPILED_TOKENS = {
    "color.interactive.default": "#005FCC",
    "color.interactive.foreground": "#FFFFFF",
    "color.interactive.disabled": "#99BBDD",
    "radius.md": "8px",
    "space.4": "16px",
}

BRAND_PROFILE = {"brand": "Acme", "a11y_level": "AA"}


@pytest.fixture
def output_dir(tmp_path):
    # Set up specs
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text(yaml.dump(BUTTON_SPEC))

    # Set up src
    src_dir = tmp_path / "src" / "components"
    src_dir.mkdir(parents=True)
    (src_dir / "Button.tsx").write_text(BUTTON_TSX)
    (src_dir / "Button.test.tsx").write_text(BUTTON_TEST_TSX)

    # Set up tokens
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    (tokens_dir / "semantic.tokens.json").write_text(json.dumps(COMPILED_TOKENS))

    # Set up coverage
    coverage_dir = tmp_path / "coverage"
    coverage_dir.mkdir()
    lcov = {
        "Button.tsx": {
            "lines": {"total": 40, "covered": 38, "pct": 95.0},
            "functions": {"total": 2, "covered": 2, "pct": 100.0},
            "branches": {"total": 4, "covered": 3, "pct": 75.0},
            "statements": {"total": 40, "covered": 38, "pct": 95.0},
        }
    }
    (coverage_dir / "lcov.json").write_text(json.dumps(lcov))

    # Set up brand profile
    (tmp_path / "brand-profile.json").write_text(json.dumps(BRAND_PROFILE))

    return str(tmp_path)


def test_component_factory_crew_produces_all_reports(output_dir, tmp_path):
    with (
        patch("daf.agents.spec_validation._call_llm") as mock_spec_llm,
        patch("daf.agents.composition._call_llm") as mock_comp_llm,
        patch("daf.agents.accessibility._call_llm") as mock_a11y_llm,
        patch("daf.agents.accessibility._run_tsc") as mock_tsc,
        patch("daf.agents.quality_scoring._call_llm") as mock_score_llm,
    ):
        mock_spec_llm.return_value = "Spec validation complete."
        mock_comp_llm.return_value = "Composition check complete."
        mock_a11y_llm.return_value = BUTTON_TSX
        mock_tsc.return_value = (0, "")
        mock_score_llm.return_value = "Scoring complete."

        crew = create_component_factory_crew(output_dir)
        crew.kickoff()

    reports_dir = tmp_path / "reports"

    # All three reports must exist
    assert (reports_dir / "quality-scorecard.json").exists(), "quality-scorecard.json not written"
    assert (reports_dir / "a11y-audit.json").exists(), "a11y-audit.json not written"
    assert (reports_dir / "composition-audit.json").exists(), "composition-audit.json not written"

    # Scorecard must be valid JSON
    scorecard = json.loads((reports_dir / "quality-scorecard.json").read_text())
    assert isinstance(scorecard, dict)

    # Button should have gate: "passed"
    components = scorecard.get("components", {})
    if "Button" in components:
        assert components["Button"].get("gate") == "passed"

    # Checkpoint must exist
    checkpoint_path = tmp_path / "checkpoints" / "component-factory.json"
    assert checkpoint_path.exists(), "checkpoint file not written"
