# Specification: Code Generation

## Purpose

Defines the behavioral requirements for Agent 14 (Code Generation Agent) in the Design-to-Code Crew. Covers production TypeScript/TSX source generation, unit test file generation (`.test.tsx`), Storybook story file generation (`.stories.tsx`), inline lint-retry loop, pattern memory consistency, and the structured rejection contract used by Agent 6's cross-phase retry protocol.

---

## Requirements

### Requirement: TSX source generation from intent manifest

Agent 14 (Code Generation Agent) in the Design-to-Code Crew MUST generate a production-quality `ComponentName.tsx` file from the intent manifest produced by Agent 13. The generated file MUST satisfy all structural and quality constraints defined in PRD §4.3.

Structural constraints:
- Zero hardcoded style values — all visual properties MUST reference compiled token variables.
- All declared variants MUST be rendered via a single component (no separate variant components).
- Composition MUST use approved primitives only (Box, Stack, HStack, VStack, Grid, Text, Icon, Pressable, Divider, Spacer, ThemeProvider) — no direct HTML element usage except inside primitive implementations.
- Every interactive element MUST include a `data-testid` attribute.
- TypeScript strict mode — no implicit `any`, all props typed.
- An `// @accessibility-placeholder` comment MUST appear at the end of the test file as an insertion marker for the Accessibility Agent (19).

#### Acceptance Criteria

- [ ] A `.tsx` file is written to `src/primitives/ComponentName.tsx` (for primitives) or `src/components/ComponentName/ComponentName.tsx` (for non-primitives).
- [ ] The file contains zero hardcoded color, spacing, or typography values; all values are CSS token variable references.
- [ ] All variants declared in the intent manifest are represented by conditional prop-driven rendering in a single component.
- [ ] All interactive elements have `data-testid` attributes.
- [ ] The file passes `tsc --noEmit` without errors (TypeScript compilation).
- [ ] The file passes ESLint after at most 2 inline retry cycles (lint errors trigger Agent 14 self-correction before escalation).
- [ ] Each generated component is added to the pattern memory store before the next component is generated.

#### Scenario: Successful Button TSX generation

- GIVEN an intent manifest for `Button` with variants `[primary, secondary, ghost]` and token bindings for `background-color` and `color`
- WHEN Agent 14 generates `Button.tsx`
- THEN the file references `var(--semantic-color-btn-bg-primary)` (or equivalent CSS variable) for background, not a hex value
- AND the file renders all three variants via props
- AND every `<Pressable>` child has a `data-testid`
- AND the file compiles cleanly with `tsc --noEmit`

#### Scenario: Hardcoded value detected by lint retry

- GIVEN the first generation pass includes `color: '#1a1a1a'` in a style prop
- WHEN `eslint_runner.py` reports a `no-hardcoded-tokens` violation
- THEN Agent 14 corrects the value to the appropriate token variable on retry pass 1
- AND ESLint passes on retry pass 1

#### Scenario: Persistent lint failure after 2 retries

- GIVEN ESLint reports a violation on the initial generation and both retry passes
- WHEN Agent 14 exhausts the 2-retry cap
- THEN the file is written with the best available output
- AND `reports/generation-summary.json` records `lint_warnings: [...]` for that component
- AND generation continues to the next component (not a fatal crew failure)

---

### Requirement: Unit test file generation

Agent 14 MUST generate a `.test.tsx` file for every component immediately after generating its TSX source. The test file MUST cover all declared variants and interactive state transitions.

Required test structure:
- A top-level `describe('ComponentName', ...)` block.
- One `it` block per variant rendering assertion.
- One `it` block per interactive state (hover, focus, disabled, etc.) rendering assertion.
- All interactive elements asserted via `data-testid` queries.
- An `// @accessibility-placeholder` comment block at the end of the file.

#### Acceptance Criteria

- [ ] A `.test.tsx` file is written alongside each `.tsx` file.
- [ ] The test file contains one `it` per variant declared in the intent manifest.
- [ ] The test file contains one `it` per interactive state declared in the intent manifest.
- [ ] All element queries use `getByTestId` or `getByRole` (no brittle CSS selector queries).
- [ ] The `// @accessibility-placeholder` comment appears as the last non-empty line in the file.
- [ ] The test file is valid TypeScript (no type errors).

#### Scenario: Variant coverage for Button

- GIVEN Button has variants `[primary, secondary, ghost]`
- WHEN the test file is generated
- THEN there exist three `it` blocks asserting rendering for `variant="primary"`, `variant="secondary"`, and `variant="ghost"`

#### Scenario: Accessibility placeholder presence

- GIVEN any component test file is generated
- WHEN the file is written to disk
- THEN the final non-empty line (or comment block) is exactly `// @accessibility-placeholder`

---

### Requirement: Storybook story file generation

Agent 14 MUST generate a `.stories.tsx` file for every component using CSF3 format. The story file MUST include one named story per variant and one named story per interactive state.

#### Acceptance Criteria

- [ ] A `.stories.tsx` file is written alongside each `.tsx` file.
- [ ] The story file exports a default `Meta<typeof ComponentName>` object with `title` and `component` fields.
- [ ] One named export exists per variant declared in the intent manifest.
- [ ] One named or embedded story entry exists for each interactive state (using Storybook's `play` function or `args`).
- [ ] The story file is valid TypeScript (no type errors).

#### Scenario: Button story coverage

- GIVEN Button has variants `[primary, secondary, ghost]` and states `[hover, focus, disabled]`
- WHEN the story file is generated
- THEN six named exports exist: `Primary`, `Secondary`, `Ghost`, `HoverState`, `FocusState`, `DisabledState` (or equivalent)

---

### Requirement: Structured rejection on unresolvable generation

Agent 14 MUST write `reports/generation-rejection.json` when one or more components cannot be generated due to unresolvable token references or irrecoverable spec intent failures. This file is the primary signal for Agent 6's cross-phase retry.

Rejection schema:
```json
{
  "rejected_components": [
    {
      "component": "string",
      "reason": "unresolvable_token_ref | invalid_spec_intent | compilation_failure",
      "details": "string",
      "missing_refs": ["string"]
    }
  ]
}
```

#### Acceptance Criteria

- [ ] If all components are generated successfully, `reports/generation-rejection.json` is NOT written (or is deleted if it existed from a prior run).
- [ ] If any component fails with an unresolvable token ref or invalid spec intent, `reports/generation-rejection.json` is written with the schema above.
- [ ] `reason` is one of the three defined enum values.
- [ ] `missing_refs` lists every unresolvable token path that caused the failure.
- [ ] Agent 6 can read this file to determine whether to trigger a cross-phase retry.

#### Scenario: Successful generation — no rejection file

- GIVEN all components generate successfully
- WHEN Agent 14 completes task T3
- THEN `reports/generation-rejection.json` is absent from the output directory

#### Scenario: Unresolvable token reference

- GIVEN `button.spec.yaml` references `semantic.color.btn.bg-nonexistent` which does not exist in the compiled tokens
- WHEN Agent 14 attempts to generate `Button.tsx`
- THEN `Button` is added to `rejected_components` with `reason: unresolvable_token_ref`
- AND `missing_refs: ["semantic.color.btn.bg-nonexistent"]`
- AND `reports/generation-rejection.json` is written

---

### Requirement: Pattern memory consistency across component generations

Agent 14 MUST use `pattern_memory_store.py` to record and retrieve generation patterns across the full component generation sequence within a single pipeline run. Patterns are used to maintain prop shape consistency, token binding conventions, and slot structure uniformity.

#### Acceptance Criteria

- [ ] After each component is generated, its prop shape, token bindings, and slot structure are stored in the pattern memory.
- [ ] Before generating each subsequent component, Agent 14 queries the pattern memory for similar components and uses matching patterns as a consistency reference.
- [ ] Pattern memory is scoped to the current pipeline run (not persisted across runs).
- [ ] Pattern memory retrieval never causes a failure; if no matching pattern exists, generation proceeds without context.

#### Scenario: Consistent prop shape for related components

- GIVEN `Card` was generated first with `padding` prop typed as `SpacingToken`
- WHEN `CardHeader` is generated next
- THEN the pattern memory provides the `SpacingToken` type used by `Card`
- AND Agent 14 uses the same type for `CardHeader.padding`
