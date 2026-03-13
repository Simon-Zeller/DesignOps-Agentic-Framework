"""Tests for aria_generator.py."""
from __future__ import annotations

import pytest
from daf.tools.aria_generator import generate_aria_patches


BUTTON_SPEC = {
    "component": "Button",
    "a11y": {"role": "button"},
    "states": {"default": {}, "disabled": {}},
}

DIALOG_SPEC = {
    "component": "Modal",
    "a11y": {"role": "dialog"},
    "states": {"default": {}, "open": {}},
}

STATUS_SPEC = {
    "component": "Toast",
    "a11y": {"role": "status"},
    "states": {"default": {}, "visible": {}},
}


def test_button_role_maps_to_aria_disabled():
    patches = generate_aria_patches(BUTTON_SPEC, component_type="button")
    attrs = [p.get("attribute") for p in patches]
    assert "aria-disabled" in attrs
    disabled_patch = next(p for p in patches if p.get("attribute") == "aria-disabled")
    assert disabled_patch.get("binding") == "disabled"


def test_dialog_maps_to_role_and_aria_modal():
    patches = generate_aria_patches(DIALOG_SPEC, component_type="dialog")
    attrs = [p.get("attribute") for p in patches]
    assert "role" in attrs
    assert "aria-modal" in attrs
    role_patch = next(p for p in patches if p.get("attribute") == "role")
    assert role_patch.get("value") == "dialog"


def test_status_maps_to_aria_live_and_atomic():
    patches = generate_aria_patches(STATUS_SPEC, component_type="status")
    attrs = [p.get("attribute") for p in patches]
    assert "aria-live" in attrs
    assert "aria-atomic" in attrs
    live_patch = next(p for p in patches if p.get("attribute") == "aria-live")
    assert live_patch.get("value") == "polite"
