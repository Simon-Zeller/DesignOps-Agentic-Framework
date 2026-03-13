# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `git checkout -b feat/p07-core-component-specs`
- [x] 0.2 Verify clean working tree: `git status` shows no untracked or modified files
- [x] 0.3 `git add -A && git commit -m "chore: start p07 — core component specs branch"`

## 1. Test Scaffolding — Generator (TDD Red Phase)

Write failing tests for `generate_component_specs`, all spec dicts, and `CoreComponentSpecGenerator` tool. No production code yet.

- [x] 1.1 Create `tests/test_core_component_spec_generator.py` — import `generate_component_specs` and `CoreComponentSpecGenerator`; all test functions exist but call `pytest.fail("not implemented")` (red baseline)
- [x] 1.2 Write `test_starter_scope_produces_10_files` — calls `generate_component_specs(scope="starter", ...)`, asserts 10 YAML files exist under `tmp_path/specs/`
- [x] 1.3 Write `test_standard_scope_produces_19_files` — same as 1.2 for `standard` scope
- [x] 1.4 Write `test_comprehensive_scope_produces_26_files` — same as 1.2 for `comprehensive` scope
- [x] 1.5 Write `test_function_returns_dict_with_absolute_paths` — asserts return value is a dict and all values are absolute path strings pointing to existing files
- [x] 1.6 Write `test_generate_is_idempotent` — calls twice, asserts no error and file content unchanged
- [x] 1.7 Write `test_specs_dir_created_automatically` — asserts `specs/` subdir is created if absent
- [x] 1.8 Write `test_invalid_scope_raises_value_error` — asserts `ValueError` is raised for an invalid scope string and message mentions valid values
- [x] 1.9 Write `test_each_starter_spec_has_required_fields` — parametrize over all 10 Starter component names; assert each YAML has `component`, `description`, `props`, `variants`, `states`, `tokenBindings`, `compositionRules`, `a11yRequirements`
- [x] 1.10 Write `test_component_field_matches_filename_stem` — parametrize over all 26 Comprehensive component names; assert `spec["component"] == <filename_stem>`
- [x] 1.11 Write `test_each_prop_has_type_required_default` — parametrize over Starter components; assert every entry in `props` has `type`, `required`, `default`
- [x] 1.12 Write `test_no_hardcoded_hex_in_token_bindings` — parametrize over all Comprehensive components; assert no `$value` matches `#[0-9a-fA-F]{3,8}`
- [x] 1.13 Write `test_no_hardcoded_length_in_token_bindings` — parametrize over all Comprehensive components; assert no `$value` contains a px/rem/em literal
- [x] 1.14 Write `test_input_spec_has_semantic_color_token` — asserts at least one `tokenBindings` entry in `Input.spec.yaml` references a `color.border` or `color.interactive` alias
- [x] 1.15 Write `test_all_starter_components_have_nonempty_composes_from` — parametrize over Starter names; assert `compositionRules.composesFrom` is a non-empty list of primitive names only
- [x] 1.16 Write `test_no_component_references_component_in_composes_from` — parametrize over all Comprehensive names; assert no entry in `composesFrom` is a component name
- [x] 1.17 Write `test_button_composes_from_pressable` — asserts `"Pressable"` in `Button.spec.yaml` `compositionRules.composesFrom`
- [x] 1.18 Write `test_card_composes_from_box` — asserts `"Box"` in `Card.spec.yaml` `compositionRules.composesFrom`
- [x] 1.19 Write `test_modal_has_slot_definitions` — asserts `compositionRules.slots` is non-empty in `Modal.spec.yaml`
- [x] 1.20 Write `test_all_specs_have_forbidden_nesting_field` — parametrize over Starter names; assert `compositionRules.forbiddenNesting` key exists
- [x] 1.21 Write `test_interactive_starter_components_have_hover_focus_disabled_states` — parametrize over `["Button", "Input", "Checkbox", "Radio", "Select"]`; assert `states` contains `default`, `hover`, `focus`, `disabled`
- [x] 1.22 Write `test_form_components_have_error_and_success_states` — parametrize over `["Input", "Checkbox", "Radio", "Select"]`; assert `states` has `error` and `success`
- [x] 1.23 Write `test_badge_has_default_state` — asserts `states["default"]` exists in `Badge.spec.yaml`
- [x] 1.24 Write `test_all_starter_components_have_a11y_required_fields` — parametrize over Starter names; assert `a11yRequirements` has `role`, `focusable`, `keyboardInteractions`, `ariaAttributes`
- [x] 1.25 Write `test_button_keyboard_interactions_include_enter_and_space` — asserts `a11yRequirements.keyboardInteractions` in `Button.spec.yaml` references `"Enter"` and `"Space"`
- [x] 1.26 Write `test_modal_a11y` — asserts `role == "dialog"`, `focusable == True`, `keyboardInteractions` references `"Escape"`, `ariaAttributes` contains `"aria-modal"` or `"aria-labelledby"`
- [x] 1.27 Write `test_override_patches_target_component` — calls with `component_overrides={"Button": {"defaultVariant": "secondary"}}`; asserts `Button.spec.yaml` has `defaultVariant: secondary`; asserts `Input.spec.yaml` unaffected
- [x] 1.28 Write `test_override_for_out_of_scope_component_ignored` — calls starter scope with DataGrid override; asserts no error and 10 files created
- [x] 1.29 Write `test_none_overrides_same_as_empty_dict` — asserts YAML output identical for `None` vs `{}`
- [x] 1.30 Write `test_comprehensive_scope_does_not_include_primitive_names` — asserts no file named `Box.spec.yaml`, `Stack.spec.yaml`, etc. in the output
- [x] 1.31 Confirm all new tests are **red**: `uv run pytest tests/test_core_component_spec_generator.py -x` — expect failures
- [x] 1.32 `git add -A && git commit -m "test(p07): red phase — core component spec generator tests"`

## 2. Test Scaffolding — CrewAI Tool & Agent (TDD Red Phase)

- [x] 2.1 Create `tests/test_core_component_agent.py` — import `CoreComponentSpecGenerator` and `create_core_component_agent`, `create_core_component_task`; all test functions call `pytest.fail("not implemented")`
- [x] 2.2 Write `test_core_component_spec_generator_is_base_tool_subclass` — asserts `CoreComponentSpecGenerator` is a subclass of `crewai.tools.BaseTool`
- [x] 2.3 Write `test_core_component_spec_generator_name` — asserts `CoreComponentSpecGenerator.name == "CoreComponentSpecGenerator"`
- [x] 2.4 Write `test_tool_run_produces_starter_files` — calls `tool._run(scope="starter", output_dir=str(tmp_path), component_overrides_json="{}")`, asserts 10 files, return value contains `"10"` and path
- [x] 2.5 Write `test_tool_run_returns_error_string_for_invalid_scope` — calls with `scope="invalid"`, asserts return value is a non-empty string (no unhandled exception)
- [x] 2.6 Write `test_create_core_component_agent_returns_agent` — asserts result is `crewai.Agent`
- [x] 2.7 Write `test_core_component_agent_role` — asserts `agent.role == "Core Component Agent"`
- [x] 2.8 Write `test_core_component_agent_has_tool` — asserts `CoreComponentSpecGenerator` instance is in `agent.tools`
- [x] 2.9 Write `test_create_core_component_task_returns_task` — asserts result is `crewai.Task`
- [x] 2.10 Write `test_agent_and_task_exported_from_daf_agents` — imports both from `daf.agents` without `ImportError`
- [x] 2.11 Confirm all new tests are **red**: `uv run pytest tests/test_core_component_agent.py -x`
- [x] 2.12 `git add -A && git commit -m "test(p07): red phase — core component agent tests"`

## 3. Implementation — Spec Definitions (TDD Green Phase)

Implement the `generate_component_specs` function and all spec dict constants.

- [x] 3.1 Create `src/daf/tools/core_component_spec_generator.py` — module docstring + imports (`yaml`, `os`, `pathlib`, `crewai.tools.BaseTool`)
- [x] 3.2 Define `_STARTER_COMPONENTS` list (10 component names in order)
- [x] 3.3 Define `_STANDARD_DELTA` list (9 additional component names)
- [x] 3.4 Define `_COMPREHENSIVE_DELTA` list (7 additional component names)
- [x] 3.5 Write private spec dict constants for all 10 Starter components:
  - [x] 3.5a `_BUTTON_SPEC` — role=button, variants=[primary,secondary,ghost,danger,...], states=[default,hover,focus,disabled], composesFrom=[Pressable, Text], a11y with Enter+Space
  - [x] 3.5b `_INPUT_SPEC` — text input, states=[default,hover,focus,disabled,error,success], composesFrom=[Box, Text], semantic border + background tokens
  - [x] 3.5c `_CHECKBOX_SPEC` — role=checkbox, states=[default,hover,focus,disabled,checked,error], composesFrom=[Pressable, Box, Icon]
  - [x] 3.5d `_RADIO_SPEC` — role=radio, states=[default,hover,focus,disabled,checked,error], composesFrom=[Pressable, Box, Icon]
  - [x] 3.5e `_SELECT_SPEC` — role=combobox/listbox, states=[default,hover,focus,disabled,open,error], composesFrom=[Box, Text, Icon, Pressable], Arrow key interactions
  - [x] 3.5f `_CARD_SPEC` — container, allowedChildren=`*`, composesFrom=[Box, Stack], slots=[header,body,footer]
  - [x] 3.5g `_BADGE_SPEC` — display-only, variants=[default,info,success,warning,error], composesFrom=[Box, Text]
  - [x] 3.5h `_AVATAR_SPEC` — image/initials, variants=[circle,square], composesFrom=[Box, Text, Icon]
  - [x] 3.5i `_ALERT_SPEC` — role=alert, variants=[info,success,warning,error], composesFrom=[Box, Stack, Text, Icon]
  - [x] 3.5j `_MODAL_SPEC` — role=dialog, states=[open,closed], slots=[header,body,footer], Escape key, focus trap, composesFrom=[Box, Stack, Text, Pressable]
- [x] 3.6 Write private spec dict constants for all 9 Standard-delta components:
  - [x] 3.6a `_TABLE_SPEC` — role=table, composesFrom=[Box, Stack, Text], column/row states
  - [x] 3.6b `_TABS_SPEC` — role=tablist/tab, Arrow key navigation, composesFrom=[Box, Stack, Pressable, Text]
  - [x] 3.6c `_ACCORDION_SPEC` — role=region/button, composesFrom=[Box, Stack, Pressable, Text], slots=[trigger,content]
  - [x] 3.6d `_TOOLTIP_SPEC` — role=tooltip, states=[hidden,visible], composesFrom=[Box, Text]
  - [x] 3.6e `_TOAST_SPEC` — role=status/alert, variants=[info,success,warning,error], composesFrom=[Box, Stack, Text, Icon]
  - [x] 3.6f `_DROPDOWN_SPEC` — role=menu/menuitem, composesFrom=[Box, Stack, Pressable, Text, Icon], Arrow key nav
  - [x] 3.6g `_PAGINATION_SPEC` — role=navigation, composesFrom=[Box, Stack, Pressable, Text]
  - [x] 3.6h `_BREADCRUMB_SPEC` — role=navigation, composesFrom=[Box, Stack, Pressable, Text]
  - [x] 3.6i `_NAVIGATION_SPEC` — role=navigation, composesFrom=[Box, Stack, Pressable, Text], supports nested items
- [x] 3.7 Write private spec dict constants for all 7 Comprehensive-delta components:
  - [x] 3.7a `_DATEPICKER_SPEC` — role=dialog+grid, composesFrom=[Box, Stack, Pressable, Text, Icon], Arrow key nav
  - [x] 3.7b `_DATAGRID_SPEC` — role=grid, composesFrom=[Box, Stack, Text], pagination integration
  - [x] 3.7c `_TREEVIEW_SPEC` — role=tree/treeitem, composesFrom=[Box, Stack, Pressable, Text, Icon], Arrow key expand/collapse
  - [x] 3.7d `_DRAWER_SPEC` — role=dialog, composesFrom=[Box, Stack, Text, Pressable], Escape key, focus trap, slots=[header,body,footer]
  - [x] 3.7e `_STEPPER_SPEC` — role=list, composesFrom=[Box, Stack, Text, Icon], states=[completed,active,pending]
  - [x] 3.7f `_FILEUPLOAD_SPEC` — role=button+region, composesFrom=[Box, Stack, Text, Icon, Pressable], states=[idle,dragging,uploading,error,success]
  - [x] 3.7g `_RICHTEXT_SPEC` — role=textbox+toolbar, composesFrom=[Box, Stack, Text, Pressable, Icon]
- [x] 3.8 Build `COMPONENT_SPEC_MAP: dict[str, dict]` mapping PascalCase component names to their spec dicts
- [x] 3.9 Build `SCOPE_TIERS: dict[str, list[str]]` — `{"starter": [...], "standard": [...], "comprehensive": [...]}` using accumulation pattern
- [x] 3.10 Implement `generate_component_specs(scope: str, output_dir: str = ".", component_overrides: dict | None = None) -> dict[str, str]`:
  - Validate `scope` against known tiers, raise `ValueError` if invalid
  - Select component names for the scope
  - For each component, deep-copy the spec dict, apply shallow override if present, serialize with `yaml.dump`, write to `output_dir/specs/<ComponentName>.spec.yaml`
  - Return `{component_name: str(absolute_path)}` dict
- [x] 3.11 Run generator tests green: `uv run pytest tests/test_core_component_spec_generator.py -v` — all must pass
- [x] 3.12 `git add -A && git commit -m "feat(p07): implement generate_component_specs with all 26 component spec dicts"`

## 4. Implementation — CoreComponentSpecGenerator Tool (TDD Green Phase)

- [x] 4.1 In `src/daf/tools/core_component_spec_generator.py`, add `CoreComponentSpecGenerator(BaseTool)` class:
  - `name = "CoreComponentSpecGenerator"`
  - `description` explaining scope tier input and YAML output
  - `_run(self, scope: str, output_dir: str, component_overrides_json: str = "{}") -> str` — parses `component_overrides_json` with `json.loads`, calls `generate_component_specs()`, returns summary string `"Generated {n} component specs in {specs_dir}"`
  - Wraps `ValueError` from `generate_component_specs` — returns error message string instead of raising
- [x] 4.2 Run tool tests green: `uv run pytest tests/test_core_component_agent.py::test_core_component_spec_generator_is_base_tool_subclass tests/test_core_component_agent.py::test_core_component_spec_generator_name tests/test_core_component_agent.py::test_tool_run_produces_starter_files tests/test_core_component_agent.py::test_tool_run_returns_error_string_for_invalid_scope -v`
- [x] 4.3 Update `src/daf/tools/__init__.py` to export `CoreComponentSpecGenerator` and `generate_component_specs`
- [x] 4.4 `git add -A && git commit -m "feat(p07): CoreComponentSpecGenerator BaseTool class and tools __init__ export"`

## 5. Implementation — Agent 4 Module (TDD Green Phase)

- [x] 5.1 Create `src/daf/agents/core_component.py` — module docstring, imports
- [x] 5.2 Implement `create_core_component_agent() -> crewai.Agent`:
  - `role = "Core Component Agent"`
  - `goal` aligned with PRD §4.1 (generate canonical component spec YAMLs for scope tier)
  - `tools = [CoreComponentSpecGenerator()]`
  - Model: `os.environ.get("DAF_TIER2_MODEL", "claude-sonnet-4-20250514")` (Tier 2 per design.md)
- [x] 5.3 Implement `create_core_component_task(agent=None) -> crewai.Task`:
  - Task description referencing Brand Profile scope → component spec YAML generation
  - Wires to the agent from `create_core_component_agent()` if no agent provided
- [x] 5.4 Update `src/daf/agents/__init__.py` to export `create_core_component_agent` and `create_core_component_task`
- [x] 5.5 Run agent module tests green: `uv run pytest tests/test_core_component_agent.py -v` — all must pass
- [x] 5.6 Run full test suite to check for regressions: `uv run pytest --tb=short`
- [x] 5.7 `git add -A && git commit -m "feat(p07): Agent 4 core component module and __init__ exports"`

## 6. Capability Spec

- [x] 6.1 Create `openspec/specs/core-component-specs/spec.md` (already created in change artifacts — copy to permanent location)
  - Verify `openspec/specs/core-component-specs/spec.md` reflects the final implementation contract
  - Update any acceptance criteria checkboxes that need adjustment after implementation
- [x] 6.2 `git add -A && git commit -m "docs(p07): add core-component-specs capability spec to openspec/specs"`

## 7. Refactor

- [x] 7.1 Review spec dicts for consistency — ensure all 26 components follow identical field ordering (`component`, `description`, `props`, `variants`, `states`, `tokenBindings`, `compositionRules`, `a11yRequirements`)
- [x] 7.2 Extract a helper `_make_spec_entry(name, value, alias)` if token binding dicts are repetitive across components
- [x] 7.3 Verify test parametrization covers Standard and Comprehensive tiers adequately (not just Starter)
- [x] 7.4 Ensure all tests still pass after refactor: `uv run pytest --tb=short`
- [x] 7.5 `git add -A && git commit -m "refactor(p07): normalize spec dict structure and reduce duplication"`

## 8. Integration & Quality

- [x] 8.1 Run linter: `uv run ruff check src/daf/tools/core_component_spec_generator.py src/daf/agents/core_component.py`
- [x] 8.2 Run type checker: `uv run pyright src/daf/tools/core_component_spec_generator.py src/daf/agents/core_component.py` (or project-wide if configured)
- [x] 8.3 Fix all lint and type errors — zero warnings policy
- [x] 8.4 Run full test suite: `uv run pytest --tb=short`
- [x] 8.5 Verify no regressions in existing tests (p01–p06 test suites still pass)
- [x] 8.6 Check test coverage: `uv run pytest --cov=src/daf/tools/core_component_spec_generator --cov=src/daf/agents/core_component --cov-report=term-missing` — confirm ≥80% line coverage
- [x] 8.7 `git add -A && git commit -m "chore(p07): fix lint and type errors, confirm coverage"` (skip if no changes)

## 9. Final Verification & Push

- [x] 9.1 `git status` — confirm zero untracked files, zero unstaged changes
- [x] 9.2 `git log --oneline main..HEAD` — review all commits on this branch
- [x] 9.3 Rebase on latest main if needed: `git fetch origin && git rebase origin/main`
- [x] 9.4 Push feature branch: `git push origin feat/p07-core-component-specs`

## 10. Delivery

- [x] 10.1 All tasks above are checked
- [x] 10.2 Merge feature branch into main: `git checkout main && git merge feat/p07-core-component-specs`
- [x] 10.3 Push main: `git push origin main`
- [x] 10.4 Delete local feature branch: `git branch -d feat/p07-core-component-specs`
- [x] 10.5 Delete remote feature branch: `git push origin --delete feat/p07-core-component-specs`
- [x] 10.6 Verify clean state: `git branch -a` — feature branch gone, `git status` — clean
