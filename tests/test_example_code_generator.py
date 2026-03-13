"""Tests for example_code_generator.generate_example_stub."""
from daf.tools.example_code_generator import generate_example_stub


def test_stub_contains_component_name():
    stub = generate_example_stub("Button", "primary")
    assert "Button" in stub


def test_stub_is_wrapped_in_tsx_fence():
    stub = generate_example_stub("Button", "primary")
    assert stub.startswith("```tsx") or "```tsx" in stub


def test_stub_for_different_variant():
    stub = generate_example_stub("Button", "destructive")
    assert "destructive" in stub.lower() or "Button" in stub
