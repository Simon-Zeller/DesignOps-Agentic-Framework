# TDD: p13-documentation-crew

## Overview

This document specifies the complete test suite for the Documentation Crew. All tests are written **before** implementation (Red phase) and follow the red → green → refactor cycle established by the Component Factory Crew (p12).

The test suite covers:
- 14 deterministic tool tests
- 5 agent tests (LLM mocked via `unittest.mock.patch`)
- 1 integration test (full crew `kickoff()`)

All agent LLM calls are patched at `daf.agents.<module>._call_llm`. Agent 25 has no `_call_llm`.

---

## Tool Tests

### `tests/test_spec_to_doc_renderer.py`

**Purpose:** Verify that `spec_to_doc_renderer.render_spec_to_sections(spec_dict)` correctly extracts structured doc sections from a component spec.

```python
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
```

---

### `tests/test_prop_table_generator.py`

**Purpose:** Verify that `prop_table_generator.generate_prop_table(props)` renders a Markdown table.

```python
from daf.tools.prop_table_generator import generate_prop_table

PROPS = [
    {"name": "label", "type": "string", "required": True, "default": None},
    {"name": "disabled", "type": "boolean", "required": False, "default": False},
]

def test_generates_markdown_table_header():
    table = generate_prop_table(PROPS)
    assert "| Prop |" in table and "| Type |" in table

def test_required_prop_has_no_default_dash():
    table = generate_prop_table(PROPS)
    assert "—" in table  # label has no default

def test_optional_prop_shows_default():
    table = generate_prop_table(PROPS)
    assert "False" in table or "false" in table

def test_empty_props_returns_no_props_note():
    result = generate_prop_table([])
    assert "No props declared" in result
```

---

### `tests/test_example_code_generator.py`

**Purpose:** Verify that `example_code_generator.generate_example_stub(component_name, variant)` produces a TSX code block stub.

```python
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
```

---

### `tests/test_readme_template.py`

**Purpose:** Verify that `readme_template.render_readme(component_names, token_categories)` generates valid README content.

```python
from daf.tools.readme_template import render_readme

def test_readme_contains_install_instructions():
    result = render_readme(["Button", "Badge"], ["color", "spacing"])
    assert "npm install" in result

def test_readme_lists_all_components():
    result = render_readme(["Button", "Badge", "Input"], ["color"])
    assert "Button" in result and "Badge" in result and "Input" in result

def test_readme_links_to_component_docs():
    result = render_readme(["Button"], ["color"])
    assert "docs/components/Button" in result or "components/Button" in result

def test_readme_with_empty_components_includes_note():
    result = render_readme([], [])
    assert "no components" in result.lower() or result  # graceful empty
```

---

### `tests/test_token_value_resolver.py`

**Purpose:** Verify `token_value_resolver.resolve_token(token_path, compiled_tokens)` and `classify_tier(token_path)`.

```python
from daf.tools.token_value_resolver import resolve_token, classify_tier

COMPILED = {
    "color.interactive.default": "#005FCC",
    "space.4": "16px",
}

def test_resolves_known_token():
    result = resolve_token("color.interactive.default", COMPILED)
    assert result == "#005FCC"

def test_returns_none_for_unknown_token():
    result = resolve_token("color.unknown.token", COMPILED)
    assert result is None

def test_classifies_semantic_token():
    tier = classify_tier("color.interactive.default")
    assert tier == "semantic"

def test_classifies_global_token():
    tier = classify_tier("color.global.blue-60")
    assert tier == "global"

def test_classifies_component_token():
    tier = classify_tier("button.background.default")
    assert tier == "component"
```

---

### `tests/test_scale_visualizer.py`

**Purpose:** Verify `scale_visualizer.visualize_token(token_path, value)` returns appropriate visual representations.

```python
from daf.tools.scale_visualizer import visualize_token

def test_color_token_shows_swatch():
    result = visualize_token("color.interactive.default", "#005FCC")
    assert "■" in result or "#005FCC" in result

def test_spacing_token_shows_dash():
    result = visualize_token("space.4", "16px")
    assert "16px" in result

def test_non_color_non_spacing_returns_value():
    result = visualize_token("font.size.md", "16px")
    assert "16px" in result
```

---

### `tests/test_usage_context_extractor.py`

**Purpose:** Verify `usage_context_extractor.extract_usage_context(token_path, spec_tokens_map)` returns context strings.

```python
from daf.tools.usage_context_extractor import extract_usage_context

SPEC_TOKENS = {
    "background": "color.interactive.default",
    "foreground": "color.interactive.foreground",
}

def test_returns_context_for_known_usage():
    context = extract_usage_context("color.interactive.default", SPEC_TOKENS)
    assert isinstance(context, str)
    assert len(context) > 0

def test_returns_empty_string_for_unknown_token():
    context = extract_usage_context("color.mystery.unknown", SPEC_TOKENS)
    assert isinstance(context, str)  # never raises
```

---

### `tests/test_decision_log_reader.py`

**Purpose:** Verify `decision_log_reader.read_decisions(generation_summary_path)` parses the generation summary JSON.

```python
import json
from daf.tools.decision_log_reader import read_decisions

def test_reads_decisions_from_summary(tmp_path):
    summary = {
        "archetype": "minimalist",
        "a11y_level": "AA",
        "decisions": [
            {"title": "Archetype Selection", "context": "Brand is minimal.", "decision": "Use minimalist archetype.", "consequences": "Fewer colors."}
        ]
    }
    path = tmp_path / "generation-summary.json"
    path.write_text(json.dumps(summary))
    decisions = read_decisions(str(path))
    assert len(decisions) == 1
    assert decisions[0]["title"] == "Archetype Selection"

def test_returns_empty_list_when_no_decisions_key(tmp_path):
    path = tmp_path / "generation-summary.json"
    path.write_text(json.dumps({"archetype": "minimal"}))
    decisions = read_decisions(str(path))
    assert decisions == []

def test_returns_empty_list_when_file_missing(tmp_path):
    decisions = read_decisions(str(tmp_path / "nonexistent.json"))
    assert decisions == []
```

---

### `tests/test_brand_profile_analyzer.py`

**Purpose:** Verify `brand_profile_analyzer.analyze_brand_profile(profile_dict)` extracts key fields.

```python
from daf.tools.brand_profile_analyzer import analyze_brand_profile

def test_extracts_archetype():
    result = analyze_brand_profile({"archetype": "vibrant", "a11y_level": "AA"})
    assert result["archetype"] == "vibrant"

def test_extracts_a11y_level():
    result = analyze_brand_profile({"archetype": "minimal", "a11y_level": "AAA"})
    assert result["a11y_level"] == "AAA"

def test_handles_missing_archetype():
    result = analyze_brand_profile({"a11y_level": "AA"})
    assert result["archetype"] == "unspecified"

def test_handles_empty_profile():
    result = analyze_brand_profile({})
    assert result["archetype"] == "unspecified"
    assert result["a11y_level"] == "AA"  # default
```

---

### `tests/test_prose_generator.py`

**Purpose:** Verify `prose_generator.build_narrative_prompt(brand_analysis, decisions)` builds a well-formed LLM prompt.

```python
from daf.tools.prose_generator import build_narrative_prompt

BRAND = {"archetype": "minimalist", "a11y_level": "AA", "modular_scale": 1.25}
DECISIONS = [{"title": "Archetype Selection", "decision": "Use minimalist archetype."}]

def test_prompt_contains_archetype():
    prompt = build_narrative_prompt(BRAND, DECISIONS)
    assert "minimalist" in prompt

def test_prompt_contains_a11y_level():
    prompt = build_narrative_prompt(BRAND, DECISIONS)
    assert "AA" in prompt

def test_prompt_is_non_empty_string():
    prompt = build_narrative_prompt(BRAND, DECISIONS)
    assert isinstance(prompt, str) and len(prompt) > 20

def test_prompt_with_empty_decisions():
    prompt = build_narrative_prompt(BRAND, [])
    assert isinstance(prompt, str)  # never raises
```

---

### `tests/test_decision_extractor.py`

**Purpose:** Verify `decision_extractor.extract_decisions(generation_summary)` normalizes decision records.

```python
from daf.tools.decision_extractor import extract_decisions

def test_extracts_all_decisions():
    summary = {
        "decisions": [
            {"title": "Token Scale", "context": "Ctx", "decision": "Dec", "consequences": "Con"},
            {"title": "Archetype", "context": "Ctx2", "decision": "Dec2", "consequences": "Con2"},
        ]
    }
    decisions = extract_decisions(summary)
    assert len(decisions) == 2

def test_returns_empty_list_for_no_decisions():
    decisions = extract_decisions({})
    assert decisions == []

def test_each_decision_has_required_keys():
    summary = {"decisions": [{"title": "T", "decision": "D"}]}
    decisions = extract_decisions(summary)
    assert "title" in decisions[0]
    assert "decision" in decisions[0]
    assert "context" in decisions[0]  # defaults to empty string
    assert "consequences" in decisions[0]  # defaults to empty string
```

---

### `tests/test_adr_template_generator.py`

**Purpose:** Verify `adr_template_generator.generate_adr(decision)` produces valid ADR Markdown and `slugify_title(title)` produces a valid filename slug.

```python
from daf.tools.adr_template_generator import generate_adr, slugify_title

DECISION = {
    "title": "Archetype Selection",
    "context": "The brand required a visual style.",
    "decision": "We selected the minimalist archetype.",
    "consequences": "Fewer color tokens, simpler type scale.",
}

def test_adr_contains_context_section():
    adr = generate_adr(DECISION)
    assert "## Context" in adr or "Context" in adr

def test_adr_contains_decision_section():
    adr = generate_adr(DECISION)
    assert "## Decision" in adr or "Decision" in adr

def test_adr_contains_consequences_section():
    adr = generate_adr(DECISION)
    assert "## Consequences" in adr or "Consequences" in adr

def test_slugify_basic_title():
    assert slugify_title("Archetype Selection") == "archetype-selection"

def test_slugify_strips_special_chars():
    assert slugify_title("Token Scale Algorithm (v2)") == "token-scale-algorithm-v2"
```

---

### `tests/test_search_index_builder.py`

**Purpose:** Verify `search_index_builder.build_index_entries(markdown_content, file_path)` produces valid index entries.

```python
from daf.tools.search_index_builder import build_index_entries

BUTTON_MD = """# Button

A pressable component.

## Props

The Button accepts label, disabled, and onPress.

## Usage

Import and use it.
"""

def test_returns_list_of_entries():
    entries = build_index_entries(BUTTON_MD, "docs/components/Button.md")
    assert isinstance(entries, list)
    assert len(entries) > 0

def test_each_entry_has_required_keys():
    entries = build_index_entries(BUTTON_MD, "docs/components/Button.md")
    for entry in entries:
        assert "id" in entry
        assert "title" in entry
        assert "content" in entry
        assert "path" in entry

def test_content_strips_markdown_formatting():
    entries = build_index_entries("# Button\n\nA **pressable** component.", "docs/components/Button.md")
    for entry in entries:
        assert "**" not in entry["content"]
        assert "#" not in entry["content"]

def test_empty_markdown_returns_empty_list():
    entries = build_index_entries("", "docs/components/Empty.md")
    assert entries == []
```

---

### `tests/test_metadata_tagger.py`

**Purpose:** Verify `metadata_tagger.tag_entry(entry, file_path)` assigns the correct `category` based on file path.

```python
from daf.tools.metadata_tagger import tag_entry

def test_component_file_gets_component_category():
    entry = {"id": "1", "title": "Button", "content": "...", "path": "docs/components/Button.md"}
    tagged = tag_entry(entry, "docs/components/Button.md")
    assert tagged["category"] == "component"

def test_token_catalog_gets_token_category():
    entry = {"id": "2", "title": "color.interactive", "content": "...", "path": "docs/tokens/catalog.md"}
    tagged = tag_entry(entry, "docs/tokens/catalog.md")
    assert tagged["category"] == "token"

def test_decision_file_gets_decision_category():
    entry = {"id": "3", "title": "ADR-001", "content": "...", "path": "docs/decisions/adr-archetype.md"}
    tagged = tag_entry(entry, "docs/decisions/adr-archetype.md")
    assert tagged["category"] == "decision"

def test_readme_gets_readme_category():
    entry = {"id": "4", "title": "README", "content": "...", "path": "docs/README.md"}
    tagged = tag_entry(entry, "docs/README.md")
    assert tagged["category"] == "readme"
```

---

## Agent Tests

### `tests/test_doc_generation_agent.py`

**Purpose:** Integration-level tests for `run_doc_generation(output_dir)`.

```python
import json, yaml
from pathlib import Path
from unittest.mock import patch
import pytest
from daf.agents.doc_generation import run_doc_generation

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

COMPILED_TOKENS = {"color.interactive.default": "#005FCC"}

@pytest.fixture
def output_dir(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "button.spec.yaml").write_text(yaml.dump(BUTTON_SPEC))
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    (tokens / "semantic.tokens.json").write_text(json.dumps(COMPILED_TOKENS))
    return str(tmp_path)

def test_creates_component_doc_file(output_dir, tmp_path):
    with patch("daf.agents.doc_generation._call_llm") as mock_llm:
        mock_llm.return_value = "// Example usage\n<Button label='Hello' />"
        run_doc_generation(output_dir)
    assert (tmp_path / "docs" / "components" / "Button.md").exists()

def test_component_doc_contains_prop_table(output_dir, tmp_path):
    with patch("daf.agents.doc_generation._call_llm") as mock_llm:
        mock_llm.return_value = "<Button />"
        run_doc_generation(output_dir)
    content = (tmp_path / "docs" / "components" / "Button.md").read_text()
    assert "label" in content and "disabled" in content

def test_creates_readme(output_dir, tmp_path):
    with patch("daf.agents.doc_generation._call_llm") as mock_llm:
        mock_llm.return_value = "<Button />"
        run_doc_generation(output_dir)
    assert (tmp_path / "docs" / "README.md").exists()

def test_readme_lists_button_component(output_dir, tmp_path):
    with patch("daf.agents.doc_generation._call_llm") as mock_llm:
        mock_llm.return_value = "<Button />"
        run_doc_generation(output_dir)
    content = (tmp_path / "docs" / "README.md").read_text()
    assert "Button" in content
```

---

### `tests/test_token_catalog_agent.py`

**Purpose:** Integration-level tests for `run_token_catalog(output_dir)`.

```python
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from daf.agents.token_catalog import run_token_catalog

SEMANTIC_TOKENS = {
    "color.interactive.default": "#005FCC",
    "space.4": "16px",
}

@pytest.fixture
def output_dir(tmp_path):
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    (tokens / "semantic.tokens.json").write_text(json.dumps(SEMANTIC_TOKENS))
    (tmp_path / "docs" / "tokens").mkdir(parents=True)
    return str(tmp_path)

def test_creates_catalog_file(output_dir, tmp_path):
    with patch("daf.agents.token_catalog._call_llm") as mock_llm:
        mock_llm.return_value = "A color token used for interactive elements."
        run_token_catalog(output_dir)
    assert (tmp_path / "docs" / "tokens" / "catalog.md").exists()

def test_catalog_contains_token_path(output_dir, tmp_path):
    with patch("daf.agents.token_catalog._call_llm") as mock_llm:
        mock_llm.return_value = "Usage description."
        run_token_catalog(output_dir)
    content = (tmp_path / "docs" / "tokens" / "catalog.md").read_text()
    assert "color.interactive.default" in content

def test_catalog_contains_resolved_value(output_dir, tmp_path):
    with patch("daf.agents.token_catalog._call_llm") as mock_llm:
        mock_llm.return_value = "Usage description."
        run_token_catalog(output_dir)
    content = (tmp_path / "docs" / "tokens" / "catalog.md").read_text()
    assert "#005FCC" in content
```

---

### `tests/test_generation_narrative_agent.py`

**Purpose:** Integration-level tests for `run_generation_narrative(output_dir)`.

```python
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from daf.agents.generation_narrative import run_generation_narrative

BRAND_PROFILE = {"archetype": "minimalist", "a11y_level": "AA", "modular_scale": 1.25}
GENERATION_SUMMARY = {
    "archetype": "minimalist",
    "decisions": [
        {"title": "Archetype Selection", "context": "Brand required minimal style.", "decision": "minimalist", "consequences": "Fewer colors."}
    ]
}

@pytest.fixture
def output_dir(tmp_path):
    (tmp_path / "brand-profile.json").write_text(json.dumps(BRAND_PROFILE))
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "generation-summary.json").write_text(json.dumps(GENERATION_SUMMARY))
    return str(tmp_path)

def test_creates_narrative_file(output_dir, tmp_path):
    with patch("daf.agents.generation_narrative._call_llm") as mock_llm:
        mock_llm.return_value = "The design system was built with a minimalist philosophy."
        run_generation_narrative(output_dir)
    assert (tmp_path / "docs" / "decisions" / "generation-narrative.md").exists()

def test_narrative_contains_llm_output(output_dir, tmp_path):
    with patch("daf.agents.generation_narrative._call_llm") as mock_llm:
        mock_llm.return_value = "Unique narrative prose for testing."
        run_generation_narrative(output_dir)
    content = (tmp_path / "docs" / "decisions" / "generation-narrative.md").read_text()
    assert "Unique narrative prose for testing." in content

def test_narrative_created_when_no_summary(tmp_path):
    (tmp_path / "brand-profile.json").write_text(json.dumps(BRAND_PROFILE))
    with patch("daf.agents.generation_narrative._call_llm") as mock_llm:
        mock_llm.return_value = "Fallback narrative."
        run_generation_narrative(str(tmp_path))
    assert (tmp_path / "docs" / "decisions" / "generation-narrative.md").exists()
```

---

### `tests/test_decision_record_agent.py`

**Purpose:** Integration-level tests for `run_decision_records(output_dir)`.

```python
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from daf.agents.decision_record import run_decision_records

GENERATION_SUMMARY = {
    "decisions": [
        {"title": "Archetype Selection", "context": "Brand context.", "decision": "minimalist", "consequences": "Fewer tokens."},
        {"title": "Token Scale Algorithm", "context": "Scale context.", "decision": "1.25 ratio.", "consequences": "Harmonious scale."},
    ]
}

@pytest.fixture
def output_dir(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "generation-summary.json").write_text(json.dumps(GENERATION_SUMMARY))
    return str(tmp_path)

def test_creates_adr_for_each_decision(output_dir, tmp_path):
    with patch("daf.agents.decision_record._call_llm") as mock_llm:
        mock_llm.return_value = "Expanded consequences."
        run_decision_records(output_dir)
    decisions_dir = tmp_path / "docs" / "decisions"
    adr_files = list(decisions_dir.glob("adr-*.md"))
    assert len(adr_files) == 2

def test_adr_filename_is_slugified(output_dir, tmp_path):
    with patch("daf.agents.decision_record._call_llm") as mock_llm:
        mock_llm.return_value = "Consequence."
        run_decision_records(output_dir)
    assert (tmp_path / "docs" / "decisions" / "adr-archetype-selection.md").exists()

def test_fallback_adr_created_when_no_decisions(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "generation-summary.json").write_text(json.dumps({}))
    with patch("daf.agents.decision_record._call_llm") as mock_llm:
        mock_llm.return_value = "No decisions."
        run_decision_records(str(tmp_path))
    assert (tmp_path / "docs" / "decisions" / "adr-no-decisions.md").exists()
```

---

### `tests/test_search_index_agent.py`

**Purpose:** Integration-level tests for `run_search_index(output_dir)`.

```python
import json
from pathlib import Path
import pytest
from daf.agents.search_index import run_search_index

@pytest.fixture
def output_dir(tmp_path):
    docs = tmp_path / "docs"
    (docs / "components").mkdir(parents=True)
    (docs / "tokens").mkdir(parents=True)
    (docs / "decisions").mkdir(parents=True)
    (docs / "components" / "Button.md").write_text("# Button\n\nA pressable component with label prop.\n")
    (docs / "tokens" / "catalog.md").write_text("# Token Catalog\n\n## color.interactive.default\n\nValue: #005FCC\n")
    (docs / "decisions" / "adr-archetype-selection.md").write_text("# ADR: Archetype Selection\n\n## Context\nMinimalist brand.\n")
    (docs / "README.md").write_text("# Design System\n\nInstall via npm.\n")
    return str(tmp_path)

def test_creates_search_index_file(output_dir, tmp_path):
    run_search_index(output_dir)
    assert (tmp_path / "docs" / "search-index.json").exists()

def test_search_index_is_valid_json(output_dir, tmp_path):
    run_search_index(output_dir)
    content = (tmp_path / "docs" / "search-index.json").read_text()
    data = json.loads(content)
    assert isinstance(data, list)

def test_search_index_contains_component_entries(output_dir, tmp_path):
    run_search_index(output_dir)
    data = json.loads((tmp_path / "docs" / "search-index.json").read_text())
    categories = [e.get("category") for e in data]
    assert "component" in categories

def test_search_index_contains_token_entries(output_dir, tmp_path):
    run_search_index(output_dir)
    data = json.loads((tmp_path / "docs" / "search-index.json").read_text())
    categories = [e.get("category") for e in data]
    assert "token" in categories

def test_empty_docs_produces_empty_index(tmp_path):
    (tmp_path / "docs").mkdir()
    run_search_index(str(tmp_path))
    data = json.loads((tmp_path / "docs" / "search-index.json").read_text())
    assert data == []
```

---

## Integration Test

### `tests/test_documentation_crew.py`

**Purpose:** End-to-end test: `create_documentation_crew(output_dir).kickoff()` produces all required docs.

```python
import json, yaml
from pathlib import Path
from unittest.mock import patch
import pytest
from daf.crews.documentation import create_documentation_crew

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

BRAND_PROFILE = {"archetype": "minimalist", "a11y_level": "AA", "modular_scale": 1.25}

COMPILED_TOKENS = {
    "color.interactive.default": "#005FCC",
    "space.4": "16px",
}

GENERATION_SUMMARY = {
    "archetype": "minimalist",
    "decisions": [
        {"title": "Archetype Selection", "context": "Brand required minimal style.", "decision": "minimalist", "consequences": "Fewer tokens."},
    ],
}

@pytest.fixture
def output_dir(tmp_path):
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "button.spec.yaml").write_text(yaml.dump(BUTTON_SPEC))
    (tmp_path / "tokens").mkdir()
    (tmp_path / "tokens" / "semantic.tokens.json").write_text(json.dumps(COMPILED_TOKENS))
    (tmp_path / "brand-profile.json").write_text(json.dumps(BRAND_PROFILE))
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "generation-summary.json").write_text(json.dumps(GENERATION_SUMMARY))
    return str(tmp_path)

def test_crew_produces_all_docs(output_dir, tmp_path):
    with (
        patch("daf.agents.doc_generation._call_llm") as mock_doc,
        patch("daf.agents.token_catalog._call_llm") as mock_tok,
        patch("daf.agents.generation_narrative._call_llm") as mock_narr,
        patch("daf.agents.decision_record._call_llm") as mock_adr,
    ):
        mock_doc.return_value = "<Button />"
        mock_tok.return_value = "Usage description."
        mock_narr.return_value = "The design system was built minimally."
        mock_adr.return_value = "Fewer tokens result."
        crew = create_documentation_crew(output_dir)
        crew.kickoff()

    docs = tmp_path / "docs"
    assert (docs / "README.md").exists(), "docs/README.md not written"
    assert (docs / "components" / "Button.md").exists(), "component doc not written"
    assert (docs / "tokens" / "catalog.md").exists(), "token catalog not written"
    assert (docs / "decisions" / "generation-narrative.md").exists(), "narrative not written"
    assert (docs / "decisions" / "adr-archetype-selection.md").exists(), "ADR not written"
    assert (docs / "search-index.json").exists(), "search index not written"

def test_search_index_is_valid_json(output_dir, tmp_path):
    with (
        patch("daf.agents.doc_generation._call_llm") as mock_doc,
        patch("daf.agents.token_catalog._call_llm") as mock_tok,
        patch("daf.agents.generation_narrative._call_llm") as mock_narr,
        patch("daf.agents.decision_record._call_llm") as mock_adr,
    ):
        mock_doc.return_value = "<Button />"
        mock_tok.return_value = "Usage."
        mock_narr.return_value = "Narrative."
        mock_adr.return_value = "Consequence."
        create_documentation_crew(output_dir).kickoff()
    data = json.loads((tmp_path / "docs" / "search-index.json").read_text())
    assert isinstance(data, list)

def test_crew_kickoff_returns_without_error(output_dir):
    with (
        patch("daf.agents.doc_generation._call_llm", return_value="<Button />"),
        patch("daf.agents.token_catalog._call_llm", return_value="Usage."),
        patch("daf.agents.generation_narrative._call_llm", return_value="Narrative."),
        patch("daf.agents.decision_record._call_llm", return_value="Consequence."),
    ):
        crew = create_documentation_crew(output_dir)
        crew.kickoff()  # Must not raise
```
