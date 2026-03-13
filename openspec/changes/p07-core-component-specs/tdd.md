# TDD Plan: p07-core-component-specs

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

This change introduces one deterministic generator function, one CrewAI `BaseTool` subclass, and one Agent 4 factory module. Tests are written in **pytest**.

Three test types are used:

1. **Unit tests** — the generator function and spec dicts are tested in isolation using a `tmp_path` fixture; no LLM calls; assertions are structural and value-level
2. **Parametrized tests** — scope tier coverage and per-field assertions are parametrized over component name lists to avoid test duplication
3. **Structural tests** — CrewAI tool and agent factory are tested without live API calls; presence of tools, model configuration, and class hierarchy are verified

Integration tests (live Anthropic API) are excluded from the default test run via `@pytest.mark.integration`. Coverage target: ≥80% line coverage, ≥70% branch coverage.

Test files:
- `tests/test_core_component_spec_generator.py` — generator function, all scope tiers, spec field validation, token binding rules, composition rules, state machine structures
- `tests/test_core_component_agent.py` — `CoreComponentSpecGenerator` BaseTool subclass, `create_core_component_agent()`, `create_core_component_task()` factories

---

## Test Cases

### Generator — scope tier output

#### Test: Starter scope produces exactly 10 spec files

- **Maps to:** Requirement "Scope-tier component coverage" → Scenario "Starter scope generates 10 files"
- **Type:** unit
- **Given:** an empty `tmp_path` directory
- **When:** `generate_component_specs(scope="starter", output_dir=str(tmp_path))` is called
- **Then:** exactly 10 YAML files exist under `tmp_path/specs/`
- AND the returned dict has exactly 10 keys
- AND each key is a PascalCase component name from the Starter list
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Standard scope produces exactly 19 spec files

- **Maps to:** Requirement "Scope-tier component coverage" → Scenario "Standard scope accumulates Starter components"
- **Type:** unit
- **Given:** an empty `tmp_path` directory
- **When:** `generate_component_specs(scope="standard", output_dir=str(tmp_path))` is called
- **Then:** exactly 19 YAML files exist under `tmp_path/specs/`
- AND `Button.spec.yaml` is present (Starter-inherited)
- AND `Table.spec.yaml` is present (Standard-delta)
- AND dict has 19 keys
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Comprehensive scope produces exactly 26 spec files

- **Maps to:** Requirement "Scope-tier component coverage" → Scenario "Standard scope accumulates Starter components" (extended)
- **Type:** unit
- **Given:** an empty `tmp_path` directory
- **When:** `generate_component_specs(scope="comprehensive", output_dir=str(tmp_path))` is called
- **Then:** exactly 26 YAML files exist under `tmp_path/specs/`
- AND `Button.spec.yaml`, `Table.spec.yaml`, `DatePicker.spec.yaml` all exist
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Function returns dict mapping names to absolute paths

- **Maps to:** Requirement "Scope-tier component coverage" → Acceptance criteria (return type)
- **Type:** unit
- **Given:** a `tmp_path` directory
- **When:** `generate_component_specs(scope="starter", output_dir=str(tmp_path))` is called
- **Then:** the return value is a dict
- AND every value in the dict is a string path to an existing file
- AND every value path is absolute (starts with `/`)
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Function is idempotent — second call overwrites without error

- **Maps to:** Requirement "Scope-tier component coverage" → Acceptance criteria (idempotency)
- **Type:** unit
- **Given:** `generate_component_specs` has already run for `starter` scope
- **When:** `generate_component_specs(scope="starter", output_dir=str(tmp_path))` is called again
- **Then:** no exception is raised
- AND the 10 spec files still exist with identical content
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: specs/ subdirectory is created automatically

- **Maps to:** Requirement "Scope-tier component coverage" → Acceptance criteria (directory creation)
- **Type:** unit
- **Given:** `tmp_path` does not contain a `specs/` subdirectory
- **When:** `generate_component_specs(scope="starter", output_dir=str(tmp_path))` is called
- **Then:** `tmp_path/specs/` directory exists after the call
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Invalid scope raises ValueError

- **Maps to:** Requirement "Scope-tier component coverage" → Scenario "Invalid scope raises ValueError"
- **Type:** unit
- **Given:** an invalid scope string `"enterprise"`
- **When:** `generate_component_specs(scope="enterprise", output_dir=str(tmp_path))` is called
- **Then:** `ValueError` is raised
- AND the error message contains one of: `"starter"`, `"standard"`, `"comprehensive"`
- **File:** `tests/test_core_component_spec_generator.py`

---

### Generator — required YAML fields

#### Test: All Starter component specs have all 8 required top-level fields (parametrized)

- **Maps to:** Requirement "Required YAML fields per component spec" → Acceptance criteria
- **Type:** unit (parametrized over all 10 Starter component names)
- **Given:** `generate_component_specs(scope="starter", ...)` has been called
- **When:** each `*.spec.yaml` is loaded with `yaml.safe_load`
- **Then:** the document contains: `component`, `description`, `props`, `variants`, `states`, `tokenBindings`, `compositionRules`, `a11yRequirements`
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Button spec structural correctness

- **Maps to:** Requirement "Required YAML fields per component spec" → Scenario "Button spec structure"
- **Type:** unit
- **Given:** `Button.spec.yaml` has been generated
- **When:** the file is loaded with `yaml.safe_load`
- **Then:** `component == "Button"`
- AND `variants` is a non-empty list
- AND `states` contains at least `default`, `hover`, `focus`, `disabled`
- AND `a11yRequirements["role"] == "button"`
- AND `a11yRequirements["focusable"] == True`
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Each component's `component` field matches the filename stem (parametrized)

- **Maps to:** Requirement "Required YAML fields per component spec" → Acceptance criteria (PascalCase)
- **Type:** unit (parametrized over all 26 component names in Comprehensive scope)
- **Given:** all 26 specs are generated
- **When:** each spec is loaded
- **Then:** `spec["component"] == <filename_stem>` (e.g., `Button.spec.yaml` → `"Button"`)
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: All props entries have type, required, and default sub-fields (parametrized)

- **Maps to:** Requirement "Required YAML fields per component spec" → Acceptance criteria (props structure)
- **Type:** unit (parametrized over Starter component names)
- **Given:** each Starter spec is loaded
- **When:** each entry in `props` is inspected
- **Then:** each prop dict contains at minimum `type`, `required`, and `default` keys
- **File:** `tests/test_core_component_spec_generator.py`

---

### Generator — token binding convention

#### Test: No spec contains a hardcoded hex color in tokenBindings (parametrized)

- **Maps to:** Requirement "Token binding key convention" → Scenario "No hardcoded values across all component specs"
- **Type:** unit (parametrized over all Comprehensive-scope component names)
- **Given:** all 26 specs are generated
- **When:** every entry in each spec's `tokenBindings` list is inspected
- **Then:** no `$value` field matches a hex color pattern `#[0-9a-fA-F]{3,8}`
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: No spec contains a CSS length literal in tokenBindings (parametrized)

- **Maps to:** Requirement "Token binding key convention" → Scenario "No hardcoded values across all component specs"
- **Type:** unit (parametrized over all Comprehensive-scope component names)
- **Given:** all 26 specs are generated
- **When:** every `$value` in `tokenBindings` is inspected
- **Then:** no value matches a px/rem/em literal (e.g., `"16px"`, `"1rem"`)
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Input spec has semantic color token for border

- **Maps to:** Requirement "Token binding key convention" → Scenario "Input spec references semantic color token"
- **Type:** unit
- **Given:** `Input.spec.yaml` is generated
- **When:** `tokenBindings` is inspected
- **Then:** at least one entry has a `$value` referencing a token containing `color.border` or `color.interactive`
- AND the value starts with `{` and ends with `}`
- **File:** `tests/test_core_component_spec_generator.py`

---

### Generator — composition rules

#### Test: All components have non-empty composesFrom (parametrized over Starter)

- **Maps to:** Requirement "Composition from primitives" → Acceptance criteria
- **Type:** unit (parametrized over all 10 Starter component names)
- **Given:** all Starter specs are generated
- **When:** each spec's `compositionRules.composesFrom` is inspected
- **Then:** the list is non-empty
- AND every entry is one of: `Box`, `Stack`, `Grid`, `Text`, `Icon`, `Pressable`, `Divider`, `Spacer`, `ThemeProvider`
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: No component references another component in composesFrom (parametrized)

- **Maps to:** Requirement "Composition from primitives" → Acceptance criteria (no component-to-component)
- **Type:** unit (parametrized over all Comprehensive-scope component names)
- **Given:** all 26 specs are generated
- **When:** each spec's `compositionRules.composesFrom` is inspected
- **Then:** no entry is a component name (e.g., `"Button"`, `"Card"`) — only primitive names are allowed
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Button composes from Pressable

- **Maps to:** Requirement "Composition from primitives" → Scenario "Button composes from Pressable"
- **Type:** unit
- **Given:** `Button.spec.yaml` is generated
- **When:** `compositionRules.composesFrom` is inspected
- **Then:** `"Pressable"` is in the list
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Card composes from Box

- **Maps to:** Requirement "Composition from primitives" → Scenario "Card composes from Box"
- **Type:** unit
- **Given:** `Card.spec.yaml` is generated
- **When:** `compositionRules.composesFrom` is inspected
- **Then:** `"Box"` is in the list
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Modal has at least one slot definition

- **Maps to:** Requirement "Composition from primitives" → Scenario "Modal has a slot definition"
- **Type:** unit
- **Given:** `Modal.spec.yaml` is generated
- **When:** `compositionRules.slots` is inspected
- **Then:** `compositionRules.slots` is a non-empty list (e.g., contains `"header"`, `"body"`, or `"footer"`)
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: All specs have forbiddenNesting field (parametrized)

- **Maps to:** Requirement "Composition from primitives" → Acceptance criteria
- **Type:** unit (parametrized over Starter names)
- **Given:** Starter specs are generated
- **When:** each spec's `compositionRules` is inspected
- **Then:** `forbiddenNesting` key exists (value may be empty list)
- **File:** `tests/test_core_component_spec_generator.py`

---

### Generator — state machine

#### Test: Interactive Starter components have hover, focus, disabled states (parametrized)

- **Maps to:** Requirement "Interactive state machine" → Acceptance criteria
- **Type:** unit (parametrized over `["Button", "Input", "Checkbox", "Radio", "Select"]`)
- **Given:** Starter specs are generated
- **When:** each spec's `states` is inspected
- **Then:** `states` contains keys `default`, `hover`, `focus`, `disabled`
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Form components have error and success states (parametrized)

- **Maps to:** Requirement "Interactive state machine" → Scenario "Input has error state"
- **Type:** unit (parametrized over `["Input", "Checkbox", "Radio", "Select"]`)
- **Given:** Starter specs are generated
- **When:** each spec's `states` is inspected
- **Then:** `states` contains `error` and `success` keys
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Badge has at minimum a default state

- **Maps to:** Requirement "Interactive state machine" → Scenario "Badge has only default state"
- **Type:** unit
- **Given:** `Badge.spec.yaml` is generated
- **When:** `states` is inspected
- **Then:** `states["default"]` exists
- **File:** `tests/test_core_component_spec_generator.py`

---

### Generator — accessibility requirements

#### Test: All Starter components have role, focusable, keyboardInteractions, ariaAttributes (parametrized)

- **Maps to:** Requirement "Accessibility requirements per component" → Acceptance criteria
- **Type:** unit (parametrized over all 10 Starter component names)
- **Given:** Starter specs are generated
- **When:** each spec's `a11yRequirements` is inspected
- **Then:** keys `role`, `focusable`, `keyboardInteractions`, `ariaAttributes` all exist
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Button has Enter and Space in keyboardInteractions

- **Maps to:** Requirement "Accessibility requirements per component" → Scenario "Button keyboard interactions"
- **Type:** unit
- **Given:** `Button.spec.yaml` is generated
- **When:** `a11yRequirements.keyboardInteractions` is inspected
- **Then:** the list contains entries referencing `"Enter"` and `"Space"`
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Modal has role=dialog and documents focus trap and Escape key

- **Maps to:** Requirement "Accessibility requirements per component" → Scenario "Modal documents focus trap"
- **Type:** unit
- **Given:** `Modal.spec.yaml` is generated
- **When:** `a11yRequirements` is inspected
- **Then:** `role` is `"dialog"`
- AND `focusable` is `True`
- AND `keyboardInteractions` contains an entry referencing `"Escape"`
- AND `ariaAttributes` contains `"aria-modal"` or `"aria-labelledby"`
- **File:** `tests/test_core_component_spec_generator.py`

---

### Generator — componentOverrides patching

#### Test: Override patches top-level field in target component

- **Maps to:** Requirement "componentOverrides patching" → Scenario "Override default variant for Button"
- **Type:** unit
- **Given:** `component_overrides = {"Button": {"defaultVariant": "secondary"}}`
- **When:** `generate_component_specs(scope="starter", component_overrides=component_overrides, output_dir=...)` is called
- **Then:** `Button.spec.yaml` contains `defaultVariant: secondary`
- AND `Input.spec.yaml` does not contain `defaultVariant`
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Override for out-of-scope component is silently ignored

- **Maps to:** Requirement "componentOverrides patching" → Scenario "Override for out-of-scope component is ignored"
- **Type:** unit
- **Given:** `component_overrides = {"DataGrid": {"defaultVariant": "compact"}}`
- **When:** `generate_component_specs(scope="starter", component_overrides=component_overrides, output_dir=...)` is called
- **Then:** no exception is raised
- AND exactly 10 Starter spec files exist (no `DataGrid.spec.yaml`)
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: None overrides behaves identically to empty dict overrides

- **Maps to:** Requirement "componentOverrides patching" → Acceptance criteria
- **Type:** unit
- **Given:** two calls — one with `component_overrides=None`, one with `component_overrides={}`
- **When:** both calls are made with identical `scope` and `output_dir`
- **Then:** the YAML output files are byte-for-byte identical
- **File:** `tests/test_core_component_spec_generator.py`

---

### CrewAI Tool — CoreComponentSpecGenerator

#### Test: CoreComponentSpecGenerator is a BaseTool subclass

- **Maps to:** Requirement "CoreComponentSpecGenerator CrewAI tool" → Acceptance criteria
- **Type:** unit
- **Given:** `CoreComponentSpecGenerator` class is imported from `daf.tools`
- **When:** `issubclass(CoreComponentSpecGenerator, BaseTool)` is evaluated
- **Then:** result is `True`
- **File:** `tests/test_core_component_agent.py`

#### Test: CoreComponentSpecGenerator.name is correct

- **Maps to:** Requirement "CoreComponentSpecGenerator CrewAI tool" → Acceptance criteria
- **Type:** unit
- **Given:** `CoreComponentSpecGenerator` is imported
- **When:** `CoreComponentSpecGenerator.name` is accessed
- **Then:** value equals `"CoreComponentSpecGenerator"`
- **File:** `tests/test_core_component_agent.py`

#### Test: Tool _run produces 10 files for starter scope

- **Maps to:** Requirement "CoreComponentSpecGenerator CrewAI tool" → Scenario "Tool generates Starter specs"
- **Type:** unit
- **Given:** a `CoreComponentSpecGenerator` instance and a `tmp_path`
- **When:** `tool._run(scope="starter", output_dir=str(tmp_path), component_overrides_json="{}")` is called
- **Then:** 10 YAML files exist under `tmp_path/specs/`
- AND the return value is a non-empty string containing `"10"` and the output path
- **File:** `tests/test_core_component_agent.py`

#### Test: Tool _run returns error string (not exception) for invalid scope

- **Maps to:** Requirement "CoreComponentSpecGenerator CrewAI tool" → Acceptance criteria (error handling)
- **Type:** unit
- **Given:** a `CoreComponentSpecGenerator` instance
- **When:** `tool._run(scope="invalid", output_dir=str(tmp_path), component_overrides_json="{}")` is called
- **Then:** the return value is a non-empty string (no unhandled exception raised)
- AND the string indicates an error occurred (contains `"invalid"` or `"ValueError"` or similar)
- **File:** `tests/test_core_component_agent.py`

---

### Agent 4 module — factory functions

#### Test: create_core_component_agent returns a crewai.Agent

- **Maps to:** Requirement "Agent 4 module structure" → Scenario "Agent factory produces valid Agent"
- **Type:** unit
- **Given:** `from daf.agents import create_core_component_agent`
- **When:** `create_core_component_agent()` is called
- **Then:** the result is a `crewai.Agent` instance
- **File:** `tests/test_core_component_agent.py`

#### Test: Agent role is "Core Component Agent"

- **Maps to:** Requirement "Agent 4 module structure" → Acceptance criteria
- **Type:** unit
- **Given:** `agent = create_core_component_agent()`
- **When:** `agent.role` is accessed
- **Then:** value equals `"Core Component Agent"`
- **File:** `tests/test_core_component_agent.py`

#### Test: CoreComponentSpecGenerator is in agent tools list

- **Maps to:** Requirement "Agent 4 module structure" → Acceptance criteria
- **Type:** unit
- **Given:** `agent = create_core_component_agent()`
- **When:** agent's `tools` list is inspected
- **Then:** at least one tool is an instance of `CoreComponentSpecGenerator`
- **File:** `tests/test_core_component_agent.py`

#### Test: create_core_component_task returns a crewai.Task

- **Maps to:** Requirement "Agent 4 module structure" → Acceptance criteria
- **Type:** unit
- **Given:** `from daf.agents import create_core_component_task`
- **When:** `create_core_component_task()` is called
- **Then:** the result is a `crewai.Task` instance
- **File:** `tests/test_core_component_agent.py`

#### Test: create_core_component_agent and create_core_component_task are exported from daf.agents

- **Maps to:** Requirement "Agent 4 module structure" → Acceptance criteria
- **Type:** unit
- **Given:** `from daf.agents import create_core_component_agent, create_core_component_task`
- **When:** both are imported
- **Then:** neither import raises `ImportError`
- **File:** `tests/test_core_component_agent.py`

---

## Edge Case Tests

#### Test: generate_component_specs with empty string output_dir raises or uses cwd

- **Maps to:** Requirement "Scope-tier component coverage" → Scenario error case
- **Type:** unit
- **Given:** `output_dir=""` (empty string)
- **When:** `generate_component_specs(scope="starter", output_dir="")` is called
- **Then:** either a `ValueError` is raised, or files are written relative to `os.getcwd()` without error
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: Comprehensive scope does not include primitive spec filenames

- **Maps to:** Requirement "Scope-tier component coverage" (boundary)
- **Type:** unit
- **Given:** all 26 Comprehensive specs are generated
- **When:** the output `specs/` directory is listed
- **Then:** no file named `Box.spec.yaml`, `Stack.spec.yaml`, or any other primitive spec name is present (component specs are distinct from primitive specs)
- **File:** `tests/test_core_component_spec_generator.py`

#### Test: component_overrides with empty patch dict leaves spec unchanged

- **Maps to:** Requirement "componentOverrides patching" (boundary)
- **Type:** unit
- **Given:** `component_overrides = {"Button": {}}` (empty patch)
- **When:** generate is called and `Button.spec.yaml` is loaded
- **Then:** `Button.spec.yaml` content is identical to calling without overrides
- **File:** `tests/test_core_component_spec_generator.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|--------------|
| Line coverage | ≥80% | PRD quality gate requirement (§4.6, Agent 30) |
| Branch coverage | ≥70% | Covers scope-tier conditionals and override patching branches |
| A11y rules passing | N/A | This change generates specs, not rendered components |

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_core_component_spec_generator.py` | new | Generator function, all scope tiers, field validation, token binding rules, composition rules, state machine, a11y requirements, componentOverrides patching |
| `tests/test_core_component_agent.py` | new | `CoreComponentSpecGenerator` BaseTool class and Agent 4 module factories |
