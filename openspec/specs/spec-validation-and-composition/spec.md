# Specification: Spec Validation and Composition

## Purpose

Defines the behavioral requirements for Agent 17 (Spec Validation Agent) and Agent 18 (Composition Agent) in the Component Factory Crew. Covers JSON Schema validation of canonical spec YAMLs, token reference resolution, state machine correctness, primitive composition enforcement, forbidden nesting detection, and the structured rejection contract used by Agent 6's cross-phase retry protocol.

---

## Requirements

### Requirement: Spec YAML structural validation

Agent 17 (Spec Validation Agent) in the Component Factory Crew MUST validate every `specs/*.spec.yaml` file against the canonical JSON Schema definition for component specs. All required fields MUST be present, all referenced token keys MUST resolve against the compiled token files, all declared state transitions MUST be reachable and non-contradictory, and all prop types MUST be complete.

Required validation checks:
- JSON Schema structural validation: required fields (`name`, `type`, `variants`, `tokens`, `states`, `props`, `a11y`) are present
- Token reference resolution: every token key in `tokens: {}` resolves to a key in `tokens/compiled/**` or `tokens/semantic.tokens.json`
- State machine validity: no impossible state combinations, every non-terminal state has at least one outgoing transition, no transitions reference undefined states
- Prop completeness: every prop declared in `props: {}` has a `type`, a `required` flag, and (for optional props) a `default` value

#### Acceptance Criteria

- [ ] Every spec YAML present in `specs/primitives/` and `specs/components/**` is validated.
- [ ] A spec with a missing required field is rejected with a structured error naming the field.
- [ ] A spec with an unresolved token reference (e.g., `color.brand.primary` not in compiled tokens) is rejected with the unresolved key listed.
- [ ] A spec with an impossible state transition (e.g., `disabled → focused` with no `enabled` guard) is rejected with the invalid transition listed.
- [ ] A spec with an optional prop lacking a `default` value is rejected with the prop name listed.
- [ ] All validation errors are written to `reports/validation-errors.json` (merged into `quality-scorecard.json`).
- [ ] Valid specs pass all checks with zero errors.

#### Scenario: Valid Button spec passes validation

- GIVEN a `specs/components/button.spec.yaml` with all required fields, resolved token refs, valid states (`default → hover → focused → disabled`), and typed props
- WHEN Agent 17 runs JSON Schema validation and token ref resolution
- THEN the spec is marked `valid: true` in the validation report
- AND no rejection payload is written for this component

#### Scenario: Spec with unresolved token reference

- GIVEN a `specs/components/badge.spec.yaml` referencing `color.status.info` which does not exist in `tokens/compiled/semantic.json`
- WHEN Agent 17 runs token ref resolution via `token_ref_checker.py`
- THEN the validation report records `unresolved_refs: ["color.status.info"]` for `Badge`
- AND a structured rejection payload is written for Agent 6 retry routing
- AND validation continues for remaining specs (failure is per-component, not crew-level fatal)

#### Scenario: Impossible state transition detected

- GIVEN a spec declaring state `disabled → active` with no guard condition and no path back from `disabled`
- WHEN Agent 17 runs `state_machine_validator.py`
- THEN the validation report records `invalid_transitions: [{"from": "disabled", "to": "active", "reason": "terminal state cannot have outgoing transitions"}]`
- AND a structured rejection payload is written

---

### Requirement: Optional prop default completeness

Agent 17 MUST verify that every optional prop in a spec has a declared `default` value. This ensures generated components have predictable rendering in the absence of explicit prop values.

#### Acceptance Criteria

- [ ] Every prop with `required: false` has a non-null `default` field.
- [ ] Specs with missing defaults are rejected with the prop name and component name in the error payload.

#### Scenario: Missing default for optional size prop

- GIVEN a `button.spec.yaml` declaring `size` as optional with no `default` field
- WHEN Agent 17 validates prop completeness
- THEN the validation report records `missing_defaults: ["size"]` for `Button`
- AND a rejection payload is written for Agent 6

---

### Requirement: Primitive-only composition enforcement

Agent 18 (Composition Agent) in the Component Factory Crew MUST verify that every generated component in `src/components/**/*.tsx` and `src/primitives/*.tsx` imports and composes exclusively from the 9 canonical base primitives: Box, Stack (HStack, VStack), Grid, Text, Icon, Pressable, Divider, Spacer, ThemeProvider.

Primitive composition rules:
- No direct HTML element usage in component source (e.g., `<div>`, `<span>`, `<button>` are forbidden outside of primitive implementations)
- All imports MUST resolve to `src/primitives/` or the published primitives package — no third-party UI library imports
- Composition depth MUST NOT exceed 5 levels of primitive nesting

#### Acceptance Criteria

- [ ] Every `.tsx` file in `src/components/` is scanned for imports.
- [ ] Any import from a non-primitive source (non `src/primitives/`, non `@daf/primitives`) causes the component to be flagged in `composition-audit.json`.
- [ ] Any use of bare HTML elements (`<div>`, `<span>`, `<button>`, `<input>`, etc.) outside of `src/primitives/` is flagged as a composition violation.
- [ ] Components with composition depth greater than 5 are flagged as a Warning (not Fatal).
- [ ] All composition violations are written to `reports/composition-audit.json`.

#### Scenario: Modal using non-primitive import

- GIVEN `src/components/Modal/Modal.tsx` imports `import { Dialog } from '@radix-ui/react-dialog'`
- WHEN Agent 18 runs `composition_rule_engine.py` on `Modal.tsx`
- THEN `composition-audit.json` records `Modal` with `violations: [{"type": "non-primitive-import", "import": "@radix-ui/react-dialog"}]`
- AND a structured rejection payload is written for Agent 6 to re-invoke Code Generation Agent (14)

#### Scenario: Direct HTML element usage in component

- GIVEN `src/components/Card/Card.tsx` contains `<div className="card-wrapper">`
- WHEN Agent 18 scans for bare HTML elements
- THEN `composition-audit.json` records `Card` with `violations: [{"type": "bare-html-element", "element": "div"}]`
- AND a rejection payload is written

#### Scenario: Clean composition passes verification

- GIVEN `src/components/Button/Button.tsx` imports only `{ Pressable, Text }` from `src/primitives/`
- WHEN Agent 18 runs composition rule checks
- THEN `Button` is recorded as `composition_valid: true` in `composition-audit.json`
- AND no rejection payload is written

---

### Requirement: Forbidden nesting pattern detection

Agent 18 MUST detect forbidden nesting patterns in generated TSX — specifically, interactive primitives nested inside other interactive primitives (e.g., `Pressable` inside `Pressable`, `Input` inside `Pressable`).

#### Acceptance Criteria

- [ ] `Pressable` nested inside `Pressable` is detected and flagged as a Fatal composition violation.
- [ ] Any interactive element nested inside another interactive element is flagged.
- [ ] Violations are included in `composition-audit.json` with the component name, outer element, and inner element.

#### Scenario: Pressable inside Pressable

- GIVEN `src/components/ListItem/ListItem.tsx` contains a `<Pressable>` wrapping another `<Pressable>` for a nested action button
- WHEN Agent 18 runs `nesting_validator.py`
- THEN `composition-audit.json` records `ListItem` with `forbidden_nesting: [{"outer": "Pressable", "inner": "Pressable", "location": "ListItem.tsx:24"}]`
- AND a rejection payload is written directing Agent 14 to redesign the nested interaction using a flat composition pattern

---

### Requirement: Structured rejection payload format

Both Agent 17 and Agent 18 MUST write structured rejection payloads using the `_rejection_file.py` pattern when validation failures are discovered. Rejection payloads MUST include: component name, failure category (`spec_invalid` | `composition_violation` | `token_unresolved` | `state_invalid`), error list with field/location context, and the source artifact path that triggered the failure.

#### Acceptance Criteria

- [ ] Every validation or composition failure produces a structured rejection payload readable by Agent 6.
- [ ] The rejection payload specifies the component name and error category.
- [ ] The rejection payload includes at least one error entry with field name or location.
- [ ] Valid components produce no rejection payload.
