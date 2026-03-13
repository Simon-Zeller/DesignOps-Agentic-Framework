"""Tests for focus_trap_validator.py."""
from __future__ import annotations

import pytest
from daf.tools.focus_trap_validator import validate_focus_trap


MODAL_NO_TRAP = """
export function Modal({ isOpen, onClose, children }) {
  if (!isOpen) return null;
  return (
    <div>
      {children}
      <button onClick={onClose}>Close</button>
    </div>
  );
}
"""

MODAL_WITH_TRAP = """
import { useEffect, useRef } from 'react';

export function Modal({ isOpen, onClose, children }) {
  const firstFocusableRef = useRef(null);

  useEffect(() => {
    if (isOpen && firstFocusableRef.current) {
      firstFocusableRef.current.focus();
    }
  }, [isOpen]);

  const handleKeyDown = (e) => {
    if (e.key === 'Tab') {
      // trap focus
    }
    if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!isOpen) return null;
  return (
    <div role="dialog" aria-modal="true" onKeyDown={handleKeyDown}>
      {children}
      <button ref={firstFocusableRef} onClick={onClose}>Close</button>
    </div>
  );
}
"""

BUTTON_TSX = """
export function Button({ label, onPress }) {
  return <button onClick={onPress}>{label}</button>;
}
"""


def test_missing_focus_trap_detected_in_modal():
    result = validate_focus_trap(MODAL_NO_TRAP, component_type="dialog")
    assert result["focus_trap_present"] is False
    assert len(result["issues"]) > 0


def test_correct_focus_trap_passes():
    result = validate_focus_trap(MODAL_WITH_TRAP, component_type="dialog")
    assert result["focus_trap_present"] is True
    assert result["issues"] == []


def test_non_dialog_skips_focus_trap_check():
    result = validate_focus_trap(BUTTON_TSX, component_type="button")
    assert result.get("not_applicable") is True
    assert result["focus_trap_present"] is None
    assert result["issues"] == []
