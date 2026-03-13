"""Tests for composition_rule_engine.py."""
from __future__ import annotations

import pytest
from daf.tools.composition_rule_engine import check_composition, compute_token_compliance

CLEAN_TSX = """
import React from 'react';
import { Pressable, Text } from '../primitives';

export function Button({ label, disabled, onPress }) {
  return (
    <Pressable onPress={onPress} disabled={disabled}
      style={{ backgroundColor: 'var(--color-interactive-default)', borderRadius: 'var(--radius-md)' }}
    >
      <Text style={{ color: 'var(--color-interactive-foreground)' }}>{label}</Text>
    </Pressable>
  );
}
"""

NON_PRIMITIVE_TSX = """
import React from 'react';
import { Dialog } from '@radix-ui/react-dialog';
import { Pressable } from '../primitives';

export function Modal({ children }) {
  return <Dialog><Pressable>{children}</Pressable></Dialog>;
}
"""


def test_clean_tsx_passes_composition():
    result = check_composition(CLEAN_TSX, None)
    assert result["valid"] is True
    assert result["violations"] == []
    assert result["non_primitive_imports"] == []


def test_non_primitive_import_flagged():
    result = check_composition(NON_PRIMITIVE_TSX, None)
    assert result["valid"] is False
    violations = result["violations"]
    assert any(v.get("type") == "non-primitive-import" for v in violations)
    assert any("@radix-ui/react-dialog" in v.get("import", "") for v in violations)


def test_token_compliance_ratio():
    tsx = """
    const style = {
      backgroundColor: 'var(--color-brand)',
      color: 'var(--color-text)',
      borderRadius: 'var(--radius-md)',
      border: '#FF0000',
      padding: '#aabbcc',
      margin: '16px',
      fontSize: 'var(--typography-body-size)',
      fontWeight: 'var(--typography-body-weight)',
      opacity: '#ffffff',
      lineHeight: 'var(--typography-line-height)',
    };
    """
    result = compute_token_compliance(tsx)
    assert "token_compliance" in result
    assert "hardcoded_values" in result
    assert "total_style_values" in result
    # 3 hardcoded (#FF0000, #aabbcc, #ffffff), 10 total
    assert result["hardcoded_values"] == 3
    assert result["token_compliance"] == pytest.approx(0.7)
