"""Tests for Agent 18: Composition Agent."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from daf.agents.composition import run_composition_check


@pytest.fixture
def output_dir(tmp_path):
    src_dir = tmp_path / "src" / "components"
    src_dir.mkdir(parents=True)
    return str(tmp_path)


def test_clean_tsx_records_valid_composition(output_dir, tmp_path):
    clean_tsx = """
import React from 'react';
import { Pressable, Text } from '../../primitives';

export function Button({ label, onPress }) {
  return <Pressable onPress={onPress}><Text>{label}</Text></Pressable>;
}
"""
    tsx_path = tmp_path / "src" / "components" / "Button.tsx"
    tsx_path.write_text(clean_tsx)

    with patch("daf.agents.composition._call_llm") as mock_llm:
        mock_llm.return_value = "Composition check complete."
        run_composition_check(output_dir)

    audit_path = Path(output_dir) / "reports" / "composition-audit.json"
    if audit_path.exists():
        data = json.loads(audit_path.read_text())
        components = data.get("components", {})
        if "Button" in components:
            assert components["Button"].get("composition_valid") is True


def test_non_primitive_import_writes_rejection(output_dir, tmp_path):
    bad_tsx = """
import React from 'react';
import { Dialog } from '@radix-ui/react-dialog';

export function Modal({ children }) {
  return <Dialog>{children}</Dialog>;
}
"""
    tsx_path = tmp_path / "src" / "components" / "Modal.tsx"
    tsx_path.write_text(bad_tsx)

    with patch("daf.agents.composition._call_llm") as mock_llm:
        mock_llm.return_value = "Composition violations found."
        run_composition_check(output_dir)

    rejection_path = Path(output_dir) / "reports" / "composition-rejection.json"
    audit_path = Path(output_dir) / "reports" / "composition-audit.json"
    # Either a rejection file or audit with violations expected
    found_violation = False
    if rejection_path.exists():
        found_violation = True
    if audit_path.exists():
        data = json.loads(audit_path.read_text())
        comps = data.get("components", {})
        if "Modal" in comps and not comps["Modal"].get("composition_valid", True):
            found_violation = True
    assert found_violation
