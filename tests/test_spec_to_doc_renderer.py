"""Tests for spec_to_doc_renderer.render_spec_to_sections."""
from daf.tools.spec_to_doc_renderer import render_spec_to_sections

BUTTON_SPEC = {
    "component": "Button",
    "variants": ["primary", "secondary"],
    "states": {"default": {}, "disabled": {"terminal": True}},
    "props": {
        "label": {"type": "string", "required": True},
        "disabled": {"type": "boolean", "required": False, "default": False},
    },
    "tokens": {"background": "color.interactive.default"},
    "a11y": {"role": "button"},
}


def test_render_returns_component_name():
    sections = render_spec_to_sections(BUTTON_SPEC)
    assert sections["name"] == "Button"


def test_render_extracts_props_list():
    sections = render_spec_to_sections(BUTTON_SPEC)
    props = sections["props"]
    assert len(props) == 2
    assert any(p["name"] == "label" and p["required"] is True for p in props)


def test_render_extracts_variants():
    sections = render_spec_to_sections(BUTTON_SPEC)
    assert sections["variants"] == ["primary", "secondary"]


def test_render_extracts_token_bindings():
    sections = render_spec_to_sections(BUTTON_SPEC)
    assert sections["token_bindings"]["background"] == "color.interactive.default"


def test_render_handles_missing_props_key():
    spec = {"component": "Icon"}
    sections = render_spec_to_sections(spec)
    assert sections["props"] == []
