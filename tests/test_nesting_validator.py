"""Tests for nesting_validator.py."""
from __future__ import annotations

import pytest
from daf.tools.nesting_validator import validate_nesting

PRESSABLE_IN_PRESSABLE = """
export function BadButton() {
  return (
    <Pressable>
      <Pressable>inner</Pressable>
    </Pressable>
  );
}
"""

DEEP_NESTING = """
export function Deep() {
  return (
    <Box>
      <Box>
        <Box>
          <Box>
            <Box>
              <Box>deep</Box>
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
"""

VALID_NESTING = """
export function Valid() {
  return (
    <Box>
      <Stack>
        <Text>Hello</Text>
      </Stack>
    </Box>
  );
}
"""


def test_pressable_in_pressable_detected():
    result = validate_nesting(PRESSABLE_IN_PRESSABLE)
    assert result["valid"] is False
    assert any(
        v.get("outer") == "Pressable" and v.get("inner") == "Pressable"
        for v in result["forbidden_nesting"]
    )


def test_depth_exceeding_5_flagged_as_warning():
    result = validate_nesting(DEEP_NESTING)
    assert result["depth"] >= 6
    assert result["depth_warning"] is True


def test_valid_nesting_passes():
    result = validate_nesting(VALID_NESTING)
    assert result["valid"] is True
    assert result["forbidden_nesting"] == []
    assert result["depth"] == 3
    assert result["depth_warning"] is False
