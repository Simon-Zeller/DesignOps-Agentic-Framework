## 1. Branch Setup

- [ ] 1.1 Create feature branch: `git checkout -b feat/p06-primitive-spec-generation`
- [ ] 1.2 Verify clean working tree: `git status` shows no untracked or modified files
- [ ] 1.3 `git add -A && git commit -m "chore: start p06 — primitive spec generation branch"`

## 2. Red — Test Scaffolding (primitive spec generator)

- [ ] 2.1 Create `tests/test_primitive_spec_generator.py` — import `generate_all_primitive_specs` and `PrimitiveSpecGenerator`; all test functions exist but call `pytest.fail("not implemented")` (red baseline)
- [ ] 2.2 Write `test_generate_all_primitive_specs_produces_11_files` — asserts 11 YAML files exist under `tmp_path/specs/` after calling `generate_all_primitive_specs`
- [ ] 2.3 Write `test_generate_all_primitive_specs_returns_dict_with_11_keys` — asserts returned dict has exactly 11 keys matching all component names
- [ ] 2.4 Write `test_generate_all_primitive_specs_is_idempotent` — runs twice, asserts no error and file content unchanged
- [ ] 2.5 Write `test_each_spec_has_required_fields` — parameterize over all 11 component names, assert each YAML has `component`, `description`, `props`, `tokenBindings`, `compositionRules`, `a11yRequirements`
- [ ] 2.6 Write `test_layout_primitives_allow_any_children` — parameterize Box/Stack/HStack/VStack/Grid/ThemeProvider; assert `compositionRules.allowedChildren == "*"`
- [ ] 2.7 Write `test_leaf_primitives_have_empty_allowed_children` — parameterize Text/Icon/Divider/Spacer; assert `compositionRules.allowedChildren == []`
- [ ] 2.8 Write `test_pressable_forbids_nested_pressable` — assert `"Pressable"` in `Pressable.spec.yaml` `compositionRules.forbiddenNesting`
- [ ] 2.9 Write `test_pressable_is_focusable` — assert `a11yRequirements.focusable == True` in Pressable spec
- [ ] 2.10 Write `test_no_hardcoded_values_in_token_bindings` — assert no `$value` in any spec's `tokenBindings` matches a hex color or px literal
- [ ] 2.11 Write `test_theme_provider_has_empty_token_bindings` — assert `ThemeProvider.spec.yaml` `tokenBindings == []`
- [ ] 2.12 Confirm all new tests are **red**: `uv run pytest tests/test_primitive_spec_generator.py -x` — expect failures
- [ ] 2.13 `git add -A && git commit -m "test(p06): red phase — primitive spec generator tests"`

## 3. Red — Test Scaffolding (CrewAI Tool and Agent 3)

- [ ] 3.1 Create `tests/test_primitive_scaffolding_agent.py` — import `PrimitiveSpecGenerator` and `create_primitive_scaffolding_agent`; all test functions exist but call `pytest.fail("not implemented")`
- [ ] 3.2 Write `test_primitive_spec_generator_tool_is_base_tool_subclass` — assert `PrimitiveSpecGenerator` is a subclass of `crewai.tools.BaseTool`
- [ ] 3.3 Write `test_primitive_spec_generator_tool_name` — assert `PrimitiveSpecGenerator.name == "PrimitiveSpecGenerator"`
- [ ] 3.4 Write `test_primitive_spec_generator_tool_run_produces_files` — call `tool.run(output_dir=str(tmp_path))`, assert 11 files created, return value is a non-empty string
- [ ] 3.5 Write `test_create_primitive_scaffolding_agent_returns_agent` — import `create_primitive_scaffolding_agent`, call it, assert result is a `crewai.Agent` instance
- [ ] 3.6 Write `test_primitive_scaffolding_agent_has_tool` — assert `PrimitiveSpecGenerator` is in the agent's tools list
- [ ] 3.7 Confirm all new tests are **red**: `uv run pytest tests/test_primitive_scaffolding_agent.py -x`
- [ ] 3.8 `git add -A && git commit -m "test(p06): red phase — primitive scaffolding agent tests"`

## 4. Green — Implement primitive spec definitions

- [ ] 4.1 In `src/daf/tools/primitive_spec_generator.py`, add private dict constants for all 8 missing primitives: `_BOX_SPEC`, `_STACK_SPEC`, `_HSTACK_SPEC`, `_VSTACK_SPEC`, `_GRID_SPEC`, `_TEXT_SPEC`, `_ICON_SPEC`, `_PRESSABLE_SPEC`, `_DIVIDER_SPEC`, `_SPACER_SPEC`
- [ ] 4.2 Each dict must include: `component`, `description`, `props`, `tokenBindings` (DTCG alias format for non-layout primitives, `[]` for layout/utility), `compositionRules` (`allowedChildren`, `forbiddenNesting`), `a11yRequirements` (`role`, `focusable`, `ariaAttributes`)
- [ ] 4.3 Implement `generate_all_primitive_specs(output_dir: str = ".") -> dict[str, str]` — iterates over all 11 specs, calls `yaml.dump` for each, returns `{component_name: absolute_path}` dict
- [ ] 4.4 Verify `generate_all_primitive_specs` calls the existing `generate_theme_provider_spec` internally (or reuses `_THEME_PROVIDER_SPEC` directly) to avoid duplicate dict maintenance
- [ ] 4.5 Run generator tests green: `uv run pytest tests/test_primitive_spec_generator.py -v` — all must pass
- [ ] 4.6 `git add -A && git commit -m "feat(p06): implement generate_all_primitive_specs with all 9 primitives"`

## 5. Green — Implement PrimitiveSpecGenerator CrewAI Tool

- [ ] 5.1 In `src/daf/tools/primitive_spec_generator.py`, add `PrimitiveSpecGenerator(BaseTool)` class with `name = "PrimitiveSpecGenerator"`, `description`, and `_run(self, output_dir: str) -> str`
- [ ] 5.2 `_run` calls `generate_all_primitive_specs(output_dir)` and returns a summary string: `"Generated {n} primitive specs in {specs_dir}"` with the target `specs/` path
- [ ] 5.3 Run tool tests green: `uv run pytest tests/test_primitive_scaffolding_agent.py::test_primitive_spec_generator_tool_is_base_tool_subclass tests/test_primitive_scaffolding_agent.py::test_primitive_spec_generator_tool_name tests/test_primitive_scaffolding_agent.py::test_primitive_spec_generator_tool_run_produces_files -v` — all must pass
- [ ] 5.4 `git add -A && git commit -m "feat(p06): PrimitiveSpecGenerator BaseTool class"`

## 6. Green — Implement Agent 3 module

- [ ] 6.1 Create `src/daf/agents/primitive_scaffolding.py` following the pattern of `token_foundation.py`: module docstring, imports, `create_primitive_scaffolding_agent()` factory function, `create_primitive_scaffolding_task()` factory function
- [ ] 6.2 `create_primitive_scaffolding_agent()` returns a `crewai.Agent` with role `"Primitive Scaffolding Agent"`, goal aligned with PRD §3.3, `tools=[PrimitiveSpecGenerator()]`, model set to Haiku Tier 3 (`DAF_TIER3_MODEL` env var, default `"claude-3-haiku-20240307"`)
- [ ] 6.3 Update `src/daf/agents/__init__.py` to export `create_primitive_scaffolding_agent` and `create_primitive_scaffolding_task`
- [ ] 6.4 Run agent tests green: `uv run pytest tests/test_primitive_scaffolding_agent.py -v` — all must pass
- [ ] 6.5 Run full test suite to check for regressions: `uv run pytest --tb=short`
- [ ] 6.6 `git add -A && git commit -m "feat(p06): Agent 3 primitive scaffolding module and __init__ exports"`

## 7. Refactor

- [ ] 7.1 Review all 10 private spec dicts for consistency: ensure `component` exactly matches filename stem (PascalCase), all `tokenBindings.$value` strings use `{semantic.*}` prefix, all `compositionRules.allowedChildren` are either `"*"` or `[]` by primitive type rule
- [ ] 7.2 Extract any repeated patterns (props like `className`, `style`, `testId`) into a shared `_COMMON_PROPS` dict snippet if 3+ primitives share the same definition — inline otherwise
- [ ] 7.3 Ensure `generate_all_primitive_specs` docstring documents: what files it writes, return type, idempotency guarantee
- [ ] 7.4 Run tests to confirm refactor is non-breaking: `uv run pytest tests/test_primitive_spec_generator.py tests/test_primitive_scaffolding_agent.py tests/test_theme_provider_spec.py -v`
- [ ] 7.5 `git add -A && git commit -m "refactor(p06): normalize primitive spec dicts and add docstrings"`

## 8. Quality Gates

- [ ] 8.1 Run full lint: `uv run ruff check src/daf/tools/primitive_spec_generator.py src/daf/agents/primitive_scaffolding.py src/daf/agents/__init__.py` — zero errors
- [ ] 8.2 Run type-check: `uv run mypy src/daf/tools/primitive_spec_generator.py src/daf/agents/primitive_scaffolding.py` — zero errors
- [ ] 8.3 Run complete test suite: `uv run pytest --tb=short` — all tests pass, no regressions
- [ ] 8.4 Verify `scripts/bootstrap.sh` — Agent 3 (Task T3) is represented; add a `primitive-specs` stage if the script tests the DS Bootstrap Crew pipeline manually; update stage list to include primitive spec generation step after token-foundation
- [ ] 8.5 `git add -A && git commit -m "chore(p06): lint, type-check, bootstrap.sh update"`

## 9. Delivery

- [ ] 9.1 Verify `git status` — zero untracked files
- [ ] 9.2 Run final full test suite: `uv run pytest` — all pass
- [ ] 9.3 Push feature branch: `git push -u origin feat/p06-primitive-spec-generation`
- [ ] 9.4 Merge to main: `git checkout main && git merge --no-ff feat/p06-primitive-spec-generation -m "feat(p06): primitive spec generation — all 9 primitives + Agent 3 wiring"`
- [ ] 9.5 Delete feature branch: `git branch -d feat/p06-primitive-spec-generation && git push origin --delete feat/p06-primitive-spec-generation`
- [ ] 9.6 Final verification on main: `uv run pytest` — all pass
