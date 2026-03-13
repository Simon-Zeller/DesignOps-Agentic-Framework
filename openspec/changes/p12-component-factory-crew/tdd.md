# TDD Plan: p12-component-factory-crew

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

All 12 new tools are pure Python functions with no LLM calls — they are unit-tested in isolation using `pytest`. All four agents are tested using CrewAI agent mocking with fixture-based tool outputs. The Component Factory Crew integration test wires all four agents together against a minimal fixture set (TSX source, spec YAML, compiled tokens, brand profile), verifying patched output files and report JSON without making real LLM calls (`pytest-mock` replaces LLM calls with deterministic responses).

**Frameworks:** `pytest`, `pytest-mock`, `unittest.mock`
**Fixtures:**
- `tests/fixtures/specs/button.spec.yaml` — valid spec with required fields, resolved token refs, valid states (reused from p11 fixtures)
- `tests/fixtures/specs/badge-unresolved-token.spec.yaml` — spec with an unresolved token reference
- `tests/fixtures/specs/invalid-state-machine.spec.yaml` — spec with an impossible state transition
- `tests/fixtures/tsx/Button.tsx` — clean generated TSX using only primitives (reused from p11 fixtures)
- `tests/fixtures/tsx/Modal.tsx` — generated TSX for a dialog, missing focus trap
- `tests/fixtures/tsx/NonPrimitive.tsx` — generated TSX importing a non-primitive (@radix-ui)
- `tests/fixtures/tsx/Button.test.tsx` — test file with `// @accessibility-placeholder`
- `tests/fixtures/tokens/semantic.json` — compiled semantic token fixture
- `tests/fixtures/brand-profile.json` — brand profile with `a11y_level: "AA"`
- `tests/fixtures/brand-profile-aaa.json` — brand profile with `a11y_level: "AAA"`
- `tests/fixtures/coverage/lcov.json` — Vitest coverage fixture for Button (95% line coverage)

**Coverage gate:** ≥80% line coverage per file (hard gate); ≥70% branch coverage (soft target).

---

## Test Cases

### JSON Schema Validator (`json_schema_validator.py`)

#### Test: Valid spec passes schema validation

- **Maps to:** Requirement "Spec YAML structural validation" → Scenario "Valid Button spec passes validation"
- **Type:** unit
- **Given:** A spec dict with all required fields (`name`, `type`, `variants`, `tokens`, `states`, `props`, `a11y`)
- **When:** `validate_spec_schema(spec_dict, schema)` is called
- **Then:** Returns `{"valid": True, "errors": []}`
- **File:** `tests/test_json_schema_validator.py`

#### Test: Missing required field returns structured error

- **Maps to:** Requirement "Spec YAML structural validation" → Scenario "Spec with unresolved token reference"
- **Type:** unit
- **Given:** A spec dict missing the `variants` field
- **When:** `validate_spec_schema(spec_dict, schema)` is called
- **Then:** Returns `{"valid": False, "errors": [{"field": "variants", "message": "required field missing"}]}`
- **File:** `tests/test_json_schema_validator.py`

---

### Token Reference Checker (`token_ref_checker.py`)

#### Test: All token refs resolve successfully

- **Maps to:** Requirement "Spec YAML structural validation" → Scenario "Valid Button spec passes validation"
- **Type:** unit
- **Given:** A spec with `tokens: {"background": "color.brand.primary"}` and compiled tokens containing `color.brand.primary`
- **When:** `check_token_refs(spec_tokens, compiled_tokens)` is called
- **Then:** Returns `{"unresolved": [], "all_resolved": True}`
- **File:** `tests/test_token_ref_checker.py`

#### Test: Unresolved reference is reported

- **Maps to:** Requirement "Spec YAML structural validation" → Scenario "Spec with unresolved token reference"
- **Type:** unit
- **Given:** A spec with `tokens: {"color": "color.status.info"}` and compiled tokens that do not contain `color.status.info`
- **When:** `check_token_refs(spec_tokens, compiled_tokens)` is called
- **Then:** Returns `{"unresolved": ["color.status.info"], "all_resolved": False}`
- **File:** `tests/test_token_ref_checker.py`

---

### State Machine Validator (`state_machine_validator.py`)

#### Test: Valid state graph passes

- **Maps to:** Requirement "Spec YAML structural validation" → Scenario "Valid Button spec passes validation"
- **Type:** unit
- **Given:** A states dict `{"default": {"transitions": ["hover", "focused"]}, "hover": {"transitions": ["default", "focused"]}, "focused": {"transitions": ["default", "disabled"]}, "disabled": {"transitions": []}}`
- **When:** `validate_state_machine(states)` is called
- **Then:** Returns `{"valid": True, "invalid_transitions": [], "unreachable_states": []}`
- **File:** `tests/test_state_machine_validator.py`

#### Test: Impossible terminal-to-non-terminal transition is detected

- **Maps to:** Requirement "Spec YAML structural validation" → Scenario "Impossible state transition detected"
- **Type:** unit
- **Given:** A states dict where `disabled` (marked as terminal) has a transition to `active`
- **When:** `validate_state_machine(states)` is called
- **Then:** Returns `{"valid": False, "invalid_transitions": [{"from": "disabled", "to": "active", "reason": "terminal state cannot have outgoing transitions"}]}`
- **File:** `tests/test_state_machine_validator.py`

#### Test: Unreachable state is flagged

- **Maps to:** Requirement "Spec YAML structural validation" (unreachable state branch)
- **Type:** unit
- **Given:** A states dict where `ghost` state has no incoming transitions from any other state
- **When:** `validate_state_machine(states)` is called
- **Then:** Returns `{"unreachable_states": ["ghost"]}`
- **File:** `tests/test_state_machine_validator.py`

---

### Primitive Registry (`primitive_registry.py`)

#### Test: Known primitive is recognized

- **Maps to:** Requirement "Primitive-only composition enforcement"
- **Type:** unit
- **Given:** The string `"Box"`
- **When:** `is_primitive("Box")` is called
- **Then:** Returns `True`
- **File:** `tests/test_primitive_registry.py`

#### Test: Unknown element is not a primitive

- **Maps to:** Requirement "Primitive-only composition enforcement"
- **Type:** unit
- **Given:** The string `"Dialog"` (from @radix-ui)
- **When:** `is_primitive("Dialog")` is called
- **Then:** Returns `False`
- **File:** `tests/test_primitive_registry.py`

#### Test: All 9 base primitives and 11 exports are registered

- **Maps to:** Requirement "Primitive-only composition enforcement"
- **Type:** unit
- **Given:** The primitive registry module
- **When:** `get_all_primitives()` is called
- **Then:** Returns a set containing `Box`, `Stack`, `HStack`, `VStack`, `Grid`, `Text`, `Icon`, `Pressable`, `Divider`, `Spacer`, `ThemeProvider`
- **File:** `tests/test_primitive_registry.py`

---

### Composition Rule Engine (`composition_rule_engine.py`)

#### Test: Clean TSX with primitive-only imports passes

- **Maps to:** Requirement "Primitive-only composition enforcement" → Scenario "Clean composition passes verification"
- **Type:** unit
- **Given:** TSX source that imports only `{ Pressable, Text }` from `src/primitives/`
- **When:** `check_composition(tsx_source, primitive_registry)` is called
- **Then:** Returns `{"valid": True, "violations": [], "non_primitive_imports": []}`
- **File:** `tests/test_composition_rule_engine.py`

#### Test: Non-primitive import is flagged

- **Maps to:** Requirement "Primitive-only composition enforcement" → Scenario "Modal using non-primitive import"
- **Type:** unit
- **Given:** TSX source importing `import { Dialog } from '@radix-ui/react-dialog'`
- **When:** `check_composition(tsx_source, primitive_registry)` is called
- **Then:** Returns `{"valid": False, "violations": [{"type": "non-primitive-import", "import": "@radix-ui/react-dialog"}]}`
- **File:** `tests/test_composition_rule_engine.py`

#### Test: Token compliance ratio is computed

- **Maps to:** Requirement "Composite quality score computation" (token_compliance sub-score)
- **Type:** unit
- **Given:** TSX source with 10 style value assignments, 3 using hardcoded hex colors
- **When:** `compute_token_compliance(tsx_source)` is called
- **Then:** Returns `{"token_compliance": 0.7, "hardcoded_values": 3, "total_style_values": 10}`
- **File:** `tests/test_composition_rule_engine.py`

---

### Nesting Validator (`nesting_validator.py`)

#### Test: Pressable inside Pressable is detected

- **Maps to:** Requirement "Forbidden nesting pattern detection" → Scenario "Pressable inside Pressable"
- **Type:** unit
- **Given:** TSX source containing `<Pressable><Pressable>inner</Pressable></Pressable>`
- **When:** `validate_nesting(tsx_source)` is called
- **Then:** Returns `{"valid": False, "forbidden_nesting": [{"outer": "Pressable", "inner": "Pressable"}]}`
- **File:** `tests/test_nesting_validator.py`

#### Test: Depth exceeding 5 levels is flagged as Warning

- **Maps to:** Requirement "Primitive-only composition enforcement" (composition depth)
- **Type:** unit
- **Given:** TSX source with 6 levels of nested primitives
- **When:** `validate_nesting(tsx_source)` is called
- **Then:** Returns `{"depth": 6, "depth_warning": True}` (Warning, not Fatal)
- **File:** `tests/test_nesting_validator.py`

#### Test: Valid nesting passes

- **Maps to:** Requirement "Primitive-only composition enforcement" → Scenario "Clean composition passes verification"
- **Type:** unit
- **Given:** TSX source with 3-level clean primitive nesting, no forbidden patterns
- **When:** `validate_nesting(tsx_source)` is called
- **Then:** Returns `{"valid": True, "forbidden_nesting": [], "depth": 3, "depth_warning": False}`
- **File:** `tests/test_nesting_validator.py`

---

### ARIA Generator (`aria_generator.py`)

#### Test: Button role maps to button ARIA attributes

- **Maps to:** Requirement "ARIA role and attribute enforcement" → Scenario "Button missing aria-disabled binding"
- **Type:** unit
- **Given:** A component spec with `a11y: {role: "button"}` and a `disabled` state
- **When:** `generate_aria_patches(spec, component_type="button")` is called
- **Then:** Returns a list of patch instructions including `{"attribute": "aria-disabled", "binding": "disabled", "element": "root"}`
- **File:** `tests/test_aria_generator.py`

#### Test: Dialog component maps to dialog/alertdialog ARIA

- **Maps to:** Requirement "ARIA role and attribute enforcement" → Scenario "Modal missing role='dialog'"
- **Type:** unit
- **Given:** A spec for a modal/dialog component
- **When:** `generate_aria_patches(spec, component_type="dialog")` is called
- **Then:** Returns patch instructions for `role="dialog"` and `aria-modal="true"`
- **File:** `tests/test_aria_generator.py`

#### Test: Toast maps to aria-live and aria-atomic

- **Maps to:** Requirement "ARIA role and attribute enforcement" → Scenario "Toast missing aria-live"
- **Type:** unit
- **Given:** A spec for a toast/notification component
- **When:** `generate_aria_patches(spec, component_type="status")` is called
- **Then:** Returns patch instructions for `aria-live="polite"` and `aria-atomic="true"`
- **File:** `tests/test_aria_generator.py`

---

### Keyboard Nav Scaffolder (`keyboard_nav_scaffolder.py`)

#### Test: Dialog pattern generates Escape handler

- **Maps to:** Requirement "Keyboard navigation handler enforcement" → Scenario "Modal missing Escape key handler"
- **Type:** unit
- **Given:** Component type `"dialog"` and close callback name `"onClose"`
- **When:** `scaffold_keyboard_handlers("dialog", callbacks={"close": "onClose"})` is called
- **Then:** Returns a handler stub containing `case "Escape": onClose()` with focus restoration comment
- **File:** `tests/test_keyboard_nav_scaffolder.py`

#### Test: Listbox pattern generates arrow-key navigation

- **Maps to:** Requirement "Keyboard navigation handler enforcement" → Scenario "Select missing arrow-key navigation"
- **Type:** unit
- **Given:** Component type `"listbox"` with state handler names
- **When:** `scaffold_keyboard_handlers("listbox", ...)` is called
- **Then:** Returns a handler stub containing cases for `ArrowDown`, `ArrowUp`, `Enter`, and `Escape`
- **File:** `tests/test_keyboard_nav_scaffolder.py`

---

### Focus Trap Validator (`focus_trap_validator.py`)

#### Test: Missing focus trap detected in Modal

- **Maps to:** Requirement "Focus management in modal and overlay components" → Scenario "Modal without focus trap"
- **Type:** unit
- **Given:** TSX source for a Modal component with no `useEffect` focus management or Tab cycling logic
- **When:** `validate_focus_trap(tsx_source, component_type="dialog")` is called
- **Then:** Returns `{"focus_trap_present": False, "issues": ["no programmatic focus on open", "no focus cycling"]}`
- **File:** `tests/test_focus_trap_validator.py`

#### Test: Correct focus trap implementation passes

- **Maps to:** Requirement "Focus management in modal and overlay components"
- **Type:** unit
- **Given:** TSX source with a `useEffect` that calls `firstFocusableRef.current.focus()` on mount and a `onKeyDown` that traps Tab
- **When:** `validate_focus_trap(tsx_source, component_type="dialog")` is called
- **Then:** Returns `{"focus_trap_present": True, "issues": []}`
- **File:** `tests/test_focus_trap_validator.py`

#### Test: Non-dialog component skips focus trap check

- **Maps to:** Requirement "Focus management in modal and overlay components" (non-dialog scope)
- **Type:** unit
- **Given:** TSX source for a `Button` component (non-dialog)
- **When:** `validate_focus_trap(tsx_source, component_type="button")` is called
- **Then:** Returns `{"focus_trap_present": None, "issues": [], "not_applicable": True}`
- **File:** `tests/test_focus_trap_validator.py`

---

### Coverage Reporter (`coverage_reporter.py`)

#### Test: Returns line coverage percentage from LCOV fixture

- **Maps to:** Requirement "Composite quality score computation" (test_coverage sub-score)
- **Type:** unit
- **Given:** A `lcov.json` fixture containing line coverage for `Button.tsx` at 95%
- **When:** `get_coverage("Button.tsx", coverage_file)` is called
- **Then:** Returns `0.95`
- **File:** `tests/test_coverage_reporter.py`

#### Test: Returns None when coverage file is absent

- **Maps to:** Requirement "Composite quality score computation" → Scenario "Component with missing coverage data"
- **Type:** unit
- **Given:** A non-existent coverage file path
- **When:** `get_coverage("Button.tsx", non_existent_path)` is called
- **Then:** Returns `None` (no exception raised)
- **File:** `tests/test_coverage_reporter.py`

#### Test: Returns None for component not in coverage file

- **Maps to:** Requirement "Composite quality score computation" (coverage_unavailable branch)
- **Type:** unit
- **Given:** A valid `lcov.json` that does not contain an entry for `NewComponent.tsx`
- **When:** `get_coverage("NewComponent.tsx", coverage_file)` is called
- **Then:** Returns `None`
- **File:** `tests/test_coverage_reporter.py`

---

### Score Calculator (`score_calculator.py`)

#### Test: Full sub-scores produce correct composite

- **Maps to:** Requirement "Composite quality score computation" → Scenario "Button with full coverage and clean a11y"
- **Type:** unit
- **Given:** `test_coverage=0.95, a11y_pass_rate=1.0, token_compliance=1.0, composition_depth_score=1.0, spec_completeness=1.0`
- **When:** `calculate_score(sub_scores)` is called
- **Then:** Returns `{"composite": 98.75, "sub_scores": {...}}`
- **File:** `tests/test_score_calculator.py`

#### Test: Missing coverage defaults to 0.0 with flag

- **Maps to:** Requirement "Composite quality score computation" → Scenario "Component with missing coverage data"
- **Type:** unit
- **Given:** `test_coverage=None`
- **When:** `calculate_score(sub_scores)` is called
- **Then:** Returns composite using `0.0` for `test_coverage` and sets `coverage_unavailable: True` in output
- **File:** `tests/test_score_calculator.py`

#### Test: Formula produces deterministic result for same inputs

- **Maps to:** Requirement "Composite quality score computation" (determinism)
- **Type:** unit
- **Given:** Fixed sub-score inputs called twice
- **When:** `calculate_score(sub_scores)` is called twice with identical inputs
- **Then:** Both calls return identical composite scores
- **File:** `tests/test_score_calculator.py`

---

### Threshold Gate (`threshold_gate.py`)

#### Test: Score ≥ 70 returns gate passed

- **Maps to:** Requirement "70/100 composite quality gate" → Scenario "Component scores exactly 70/100 — gate pass"
- **Type:** unit
- **Given:** A component score of `70.0`
- **When:** `apply_gate(score=70.0, threshold=70.0)` is called
- **Then:** Returns `{"gate": "passed", "verdict": True}`
- **File:** `tests/test_threshold_gate.py`

#### Test: Score < 70 returns gate failed

- **Maps to:** Requirement "70/100 composite quality gate" → Scenario "Component scores 68/100 — gate failure"
- **Type:** unit
- **Given:** A component score of `68.0`
- **When:** `apply_gate(score=68.0, threshold=70.0)` is called
- **Then:** Returns `{"gate": "failed", "verdict": False}`
- **File:** `tests/test_threshold_gate.py`

#### Test: Gate applied to component list returns pass/fail split

- **Maps to:** Requirement "70/100 composite quality gate" (bulk gating)
- **Type:** unit
- **Given:** A list of component scores `[{"name": "Button", "composite": 85.0}, {"name": "DatePicker", "composite": 60.0}]`
- **When:** `gate_components(scores, threshold=70.0)` is called
- **Then:** Returns `{"passed": ["Button"], "failed": ["DatePicker"]}`
- **File:** `tests/test_threshold_gate.py`

---

### Spec Validation Agent (Agent 17)

#### Test: Agent produces validation report from valid spec fixtures

- **Maps to:** Requirement "Spec YAML structural validation" → Scenario "Valid Button spec passes validation"
- **Type:** unit (agent mock)
- **Given:** Mocked tool calls returning `valid: True` for Button spec
- **When:** Agent 17 is invoked against the Button spec fixture
- **Then:** The validation report records `Button: {valid: true, errors: []}` and no rejection file is written
- **File:** `tests/test_spec_validation_agent.py`

#### Test: Agent writes rejection payload for unresolved token

- **Maps to:** Requirement "Structured rejection payload format"
- **Type:** unit (agent mock)
- **Given:** Mocked `token_ref_checker.py` returning `unresolved: ["color.status.info"]`
- **When:** Agent 17 is invoked
- **Then:** A rejection file is written with `component: "Badge", failure_category: "token_unresolved"`
- **File:** `tests/test_spec_validation_agent.py`

---

### Composition Agent (Agent 18)

#### Test: Agent records clean composition for primitive-only component

- **Maps to:** Requirement "Primitive-only composition enforcement" → Scenario "Clean composition passes verification"
- **Type:** unit (agent mock)
- **Given:** Mocked `composition_rule_engine.py` and `nesting_validator.py` returning no violations for Button
- **When:** Agent 18 is invoked
- **Then:** `composition-audit.json` records `Button: {composition_valid: true, violations: []}`
- **File:** `tests/test_composition_agent.py`

#### Test: Agent writes rejection for non-primitive import

- **Maps to:** Requirement "Primitive-only composition enforcement" → Scenario "Modal using non-primitive import"
- **Type:** unit (agent mock)
- **Given:** Mocked tool returning `non_primitive_imports: ["@radix-ui/react-dialog"]`
- **When:** Agent 18 is invoked
- **Then:** A rejection file is written for `Modal` with `failure_category: "composition_violation"`
- **File:** `tests/test_composition_agent.py`

---

### Accessibility Agent (Agent 19)

#### Test: Agent patches component with missing aria-disabled

- **Maps to:** Requirement "ARIA role and attribute enforcement" → Scenario "Button missing aria-disabled binding"
- **Type:** unit (agent mock)
- **Given:** Button TSX fixture missing `aria-disabled` binding; mocked `aria_generator.py` returns patch instruction; mocked `tsc` passes after patch
- **When:** Agent 19 is invoked
- **Then:** The patched TSX contains `aria-disabled={disabled}` and `a11y-audit.json` records `aria_patched: true`
- **File:** `tests/test_accessibility_agent.py`

#### Test: Agent appends a11y describe block to test file

- **Maps to:** Requirement "Accessibility test block generation" → Scenario "A11y test block for Button"
- **Type:** unit (agent mock)
- **Given:** `Button.test.tsx` fixture with `// @accessibility-placeholder`
- **When:** Agent 19 generates and appends the a11y test block
- **Then:** The `.test.tsx` file contains a `describe('Accessibility', ...)` block after the placeholder
- **File:** `tests/test_accessibility_agent.py`

#### Test: Agent restores original source after 3 failed re-validations

- **Maps to:** Requirement "Post-patch re-validation" → Scenario "Persistent patch failure after 3 attempts"
- **Type:** unit (agent mock)
- **Given:** Mocked `tsc` subprocess returns failure for 3 consecutive calls
- **When:** Agent 19 attempts patching with 3 correction cycles
- **Then:** The original (unpatched) source is restored and `patch_failed: true` is written to `a11y-audit.json`
- **File:** `tests/test_accessibility_agent.py`

---

### Quality Scoring Agent (Agent 20)

#### Test: Agent computes correct composite for clean component

- **Maps to:** Requirement "Composite quality score computation" → Scenario "Button with full coverage and clean a11y"
- **Type:** unit (agent mock)
- **Given:** All tool fixtures returning maximum sub-scores for Button
- **When:** Agent 20 is invoked
- **Then:** `quality-scorecard.json` records `Button: {composite: 98.75, gate: "passed"}`
- **File:** `tests/test_quality_scoring_agent.py`

#### Test: Agent writes gate-failed entry and rejection for below-threshold component

- **Maps to:** Requirement "70/100 composite quality gate" → Scenario "Component scores 68/100 — gate failure"
- **Type:** unit (agent mock)
- **Given:** Mocked score of 68.0 for DatePicker
- **When:** Agent 20 applies gate
- **Then:** `quality-scorecard.json` records `DatePicker: {gate: "failed"}` and a rejection file is written
- **File:** `tests/test_quality_scoring_agent.py`

---

## Edge Case Tests

#### Test: Token ref checker handles empty tokens dict in spec

- **Maps to:** Requirement "Spec YAML structural validation" (zero-token spec)
- **Type:** unit
- **Given:** A spec with `tokens: {}` (no token bindings declared)
- **When:** `check_token_refs({}, compiled_tokens)` is called
- **Then:** Returns `{"unresolved": [], "all_resolved": True}` (empty input is valid)
- **File:** `tests/test_token_ref_checker.py`

#### Test: Score calculator handles all-zero sub-scores

- **Maps to:** Requirement "Composite quality score computation" (boundary: minimum score)
- **Type:** unit
- **Given:** All sub-scores are `0.0`
- **When:** `calculate_score(sub_scores)` is called
- **Then:** Returns `{"composite": 0.0}` (no negative scores, no exceptions)
- **File:** `tests/test_score_calculator.py`

#### Test: Accessibility placeholder absent — block appended to EOF

- **Maps to:** Requirement "Accessibility test block generation" (missing placeholder branch)
- **Type:** unit (agent mock)
- **Given:** A `.test.tsx` file with no `// @accessibility-placeholder` comment
- **When:** Agent 19 appends the a11y block
- **Then:** The block is appended to the end of the file and a Warning is logged
- **File:** `tests/test_accessibility_agent.py`

#### Test: Component Factory Crew integration — TSX in, reports out

- **Maps to:** All requirements (end-to-end verification)
- **Type:** integration
- **Given:** Button fixture TSX (primitives-only, clean), Button spec fixture (valid), compiled token fixture, AA brand profile fixture; all LLM calls mocked to return identity patches (no changes)
- **When:** `create_component_factory_crew(output_dir).run()` is called
- **Then:**
  - `reports/quality-scorecard.json` is written and valid JSON
  - `reports/a11y-audit.json` is written and valid JSON
  - `reports/composition-audit.json` is written and valid JSON
  - `Button` record shows `gate: "passed"` in scorecard
  - `checkpoints/component-factory.json` is written
- **File:** `tests/test_component_factory_crew.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage (tools) | ≥80% | PRD quality gate; tools are pure functions — high coverage is achievable |
| Line coverage (agents) | ≥75% | Agents use LLM mocking; some paths depend on LLM response content |
| Branch coverage (tools) | ≥70% | Covers error branches and optional-field handling |
| Integration test | 1 full crew run | Verifies all five tasks and file output without LLM costs |

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_json_schema_validator.py` | new | Unit tests for `json_schema_validator.py` |
| `tests/test_token_ref_checker.py` | new | Unit tests for `token_ref_checker.py` |
| `tests/test_state_machine_validator.py` | new | Unit tests for `state_machine_validator.py` |
| `tests/test_composition_rule_engine.py` | new | Unit tests for `composition_rule_engine.py` |
| `tests/test_primitive_registry.py` | new | Unit tests for `primitive_registry.py` |
| `tests/test_nesting_validator.py` | new | Unit tests for `nesting_validator.py` |
| `tests/test_aria_generator.py` | new | Unit tests for `aria_generator.py` |
| `tests/test_keyboard_nav_scaffolder.py` | new | Unit tests for `keyboard_nav_scaffolder.py` |
| `tests/test_focus_trap_validator.py` | new | Unit tests for `focus_trap_validator.py` |
| `tests/test_coverage_reporter.py` | new | Unit tests for `coverage_reporter.py` |
| `tests/test_score_calculator.py` | new | Unit tests for `score_calculator.py` |
| `tests/test_threshold_gate.py` | new | Unit tests for `threshold_gate.py` |
| `tests/test_spec_validation_agent.py` | new | Unit tests for Agent 17 with mocked tools |
| `tests/test_composition_agent.py` | new | Unit tests for Agent 18 with mocked tools |
| `tests/test_accessibility_agent.py` | new | Unit tests for Agent 19 with mocked tools and tsc subprocess |
| `tests/test_quality_scoring_agent.py` | new | Unit tests for Agent 20 with mocked tools |
| `tests/test_component_factory_crew.py` | new | Integration test: full crew run with fixture inputs |
| `tests/fixtures/specs/button.spec.yaml` | new | Valid Button spec fixture (or reuse from p11) |
| `tests/fixtures/specs/badge-unresolved-token.spec.yaml` | new | Spec with unresolved token ref |
| `tests/fixtures/specs/invalid-state-machine.spec.yaml` | new | Spec with impossible state transition |
| `tests/fixtures/tsx/Button.tsx` | new | Clean TSX fixture (primitive-only composition) |
| `tests/fixtures/tsx/Modal.tsx` | new | Modal TSX missing focus trap and ARIA |
| `tests/fixtures/tsx/NonPrimitive.tsx` | new | TSX with non-primitive import |
| `tests/fixtures/tsx/Button.test.tsx` | new | Test file with `// @accessibility-placeholder` |
| `tests/fixtures/coverage/lcov.json` | new | Vitest coverage fixture for Button at 95% |
| `tests/fixtures/brand-profile.json` | new | AA brand profile (or reuse from earlier fixtures) |
| `tests/fixtures/brand-profile-aaa.json` | new | AAA brand profile fixture |
