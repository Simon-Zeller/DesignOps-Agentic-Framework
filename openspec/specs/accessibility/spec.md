# Specification: Accessibility Enforcement

## Purpose

Defines the behavioral requirements for Agent 19 (Accessibility Agent) in the Component Factory Crew. Covers ARIA role and attribute enforcement, keyboard navigation handler scaffolding and patching, focus management validation, screen-reader announcement requirements, post-patch re-validation, a11y test block generation, AA vs. AAA strictness calibration from Brand Profile, and rollback on persistent patch failure.

---

## Requirements

### Requirement: ARIA role and attribute enforcement per component state

Agent 19 (Accessibility Agent) MUST review every generated component for correct ARIA roles and attributes for each declared interactive state. Required attributes MUST be present on the correct elements. Attributes that must be dynamically toggled by state (e.g., `aria-expanded`, `aria-disabled`, `aria-checked`) MUST be bound to component state variables, not hardcoded.

ARIA enforcement rules:
- Every interactive component root MUST have an explicit ARIA `role` matching its semantic function (e.g., `button`, `dialog`, `listbox`, `combobox`)
- Dynamic state attributes (`aria-expanded`, `aria-selected`, `aria-checked`, `aria-disabled`, `aria-pressed`) MUST be driven by component state props
- Every form input MUST be associated with a label via `aria-label`, `aria-labelledby`, or a `<label>` element wrapping
- Live-region components (Toast, Alert) MUST have `aria-live` (`polite` or `assertive`) and `aria-atomic` attributes

#### Acceptance Criteria

- [ ] Every interactive component has an explicit `role` attribute on its root element.
- [ ] All dynamic ARIA state attributes are bound to component state variables.
- [ ] All form input components have an associated label.
- [ ] All Toast and Alert components have `aria-live` and `aria-atomic`.
- [ ] Components missing required ARIA attributes are patched in place by Agent 19.
- [ ] A11y patches produce syntactically valid TypeScript that passes `tsc --noEmit`.

#### Scenario: Button missing aria-disabled binding

- GIVEN `Button.tsx` has a `disabled` prop but does not pass `aria-disabled={disabled}` to the `<Pressable>`
- WHEN Agent 19 reviews the component via `aria_generator.py`
- THEN Agent 19 patches `Button.tsx` to add `aria-disabled={disabled}` to the root `<Pressable>`
- AND the patched file is re-validated with `tsc --noEmit`
- AND `a11y-audit.json` records `Button` with `aria_patched: true, patches: ["aria-disabled binding added"]`

#### Scenario: Modal missing role="dialog"

- GIVEN `Modal.tsx` renders a content overlay without an explicit `role="dialog"` attribute
- WHEN Agent 19 runs ARIA generation for the `Modal` component type
- THEN Agent 19 patches `Modal.tsx` to add `role="dialog"` to the modal root element
- AND adds `aria-modal="true"` per WAI-ARIA dialog pattern
- AND the patched file compiles successfully

#### Scenario: Toast missing aria-live

- GIVEN `Toast.tsx` renders transient status messages without `aria-live`
- WHEN Agent 19 reviews live-region requirements
- THEN Agent 19 patches `Toast.tsx` to add `aria-live="polite"` and `aria-atomic="true"` to the notification container
- AND records the patch in `a11y-audit.json`

---

### Requirement: Keyboard navigation handler enforcement

Agent 19 MUST scaffold or patch keyboard event handlers for all interactive components. The required keyboard interactions depend on the component's ARIA role and semantic type. Missing handlers for required keys MUST be added as patches to the TSX source.

Required keyboard interaction patterns (per WAI-ARIA Authoring Practices):
- Buttons/Pressable: `Enter` and `Space` activate (already handled by native button semantics; verify not blocked)
- Dialogs/Modals: `Escape` closes and restores focus to the element that opened the dialog
- Listboxes/Selects: `Arrow Up/Down` navigate options; `Enter` selects; `Escape` collapses
- Tab panels: `Arrow Left/Right` switch between tabs; `Home/End` jump to first/last tab
- Menu/Dropdown: `Arrow Up/Down` navigate items; `Escape` closes; `Tab` closes and moves focus out

#### Acceptance Criteria

- [ ] Every interactive component with keyboard interaction requirements has an `onKeyDown` handler present.
- [ ] Dialog/Modal components handle `Escape` to close and restore focus.
- [ ] Listbox/Select components handle `ArrowDown`, `ArrowUp`, `Enter`, and `Escape`.
- [ ] Tab panel components handle `ArrowLeft`, `ArrowRight`, `Home`, and `End`.
- [ ] Keyboard handlers are patched or scaffolded by Agent 19 using `keyboard_nav_scaffolder.py`.

#### Scenario: Modal missing Escape key handler

- GIVEN `Modal.tsx` has no `onKeyDown` handler on its container
- WHEN Agent 19 applies keyboard nav scaffolding for `dialog` role components
- THEN `keyboard_nav_scaffolder.py` generates an `onKeyDown` handler for `Escape`
- AND Agent 19 patches `Modal.tsx` to add the handler with focus restoration to the triggering element
- AND the patch is recorded in `a11y-audit.json`

#### Scenario: Select missing arrow-key navigation

- GIVEN `Select.tsx` renders a dropdown listbox without arrow-key navigation
- WHEN Agent 19 applies keyboard nav patterns for `listbox` role
- THEN `keyboard_nav_scaffolder.py` generates `ArrowDown`, `ArrowUp`, `Enter`, and `Escape` handlers
- AND Agent 19 patches `Select.tsx` with the complete handler
- AND `a11y-audit.json` records `Select` with `keyboard_patched: true`

---

### Requirement: Focus management in modal and overlay components

Agent 19 MUST verify and enforce focus management for all components with `role="dialog"`, `role="alertdialog"`, and overlay-type components (Drawer, Tooltip when acting as dialog, Modal). Focus trap correctness is validated via `focus_trap_validator.py`.

Focus management rules:
- When a dialog opens, focus MUST move to the first focusable element inside the dialog (or the dialog element itself if no focusable children)
- Focus MUST be trapped inside the dialog while it is open (Tab cycles within, Shift+Tab cycles backward)
- When a dialog closes, focus MUST be restored to the element that triggered the dialog

#### Acceptance Criteria

- [ ] All `role="dialog"` components have a focus trap implementation (programmatic focus move on open, focus cycling, focus restore on close).
- [ ] Focus trap absence is detected by `focus_trap_validator.py` and triggers an Agent 19 patch.
- [ ] Patched focus trap implementation compiles successfully.
- [ ] `a11y-audit.json` records focus trap status per dialog/overlay component.

#### Scenario: Modal without focus trap

- GIVEN `Modal.tsx` opens without moving focus into the modal and does not trap Tab focus
- WHEN `focus_trap_validator.py` scans `Modal.tsx` for focus trap primitives
- THEN the tool returns `focus_trap_present: false`
- AND Agent 19 patches `Modal.tsx` to add `useEffect` with programmatic focus on open and Tab cycling
- AND `a11y-audit.json` records `Modal` with `focus_trap_patched: true`

---

### Requirement: Accessibility test block generation

Agent 19 MUST append a `describe('Accessibility', ...)` test suite to each component's `.test.tsx` file, inserted after the `// @accessibility-placeholder` comment. This block MUST contain test cases covering ARIA attribute correctness, keyboard interaction, focus management, and axe-core audit pass.

Required test cases per component:
- One `it` asserting the correct ARIA `role` is present on the root element
- One `it` per dynamic ARIA state attribute (verifying it toggles when the state changes)
- One `it` asserting keyboard handler fires for the primary interaction key
- One `it` for dialog/overlay components asserting `Escape` closes and focus is restored
- One `it` running `axe-core` in the test environment and asserting zero violations

#### Acceptance Criteria

- [ ] A `describe('Accessibility', ...)` block is appended to every `.test.tsx` file after `// @accessibility-placeholder`.
- [ ] Each block contains at minimum: one ARIA role assertion, one dynamic ARIA state test, one keyboard event test, and one axe-core zero-violations test.
- [ ] Dialog/overlay component test blocks include a focus restoration assertion.
- [ ] Appended test blocks are syntactically valid TypeScript.
- [ ] If `// @accessibility-placeholder` is absent, the block is appended to the end of the file with a Warning logged.

#### Scenario: A11y test block for Button

- GIVEN `Button.test.tsx` exists with `// @accessibility-placeholder` at the end
- WHEN Agent 19 generates the a11y test block for `Button`
- THEN a `describe('Accessibility', ...)` block is appended containing:
  - `it('has role button')` asserting `getByRole('button')` returns the element
  - `it('aria-disabled reflects disabled prop')` toggling the `disabled` prop and asserting `aria-disabled` updates
  - `it('activates on Enter key')` firing `keyDown(Enter)` on the button
  - `it('passes axe-core audit')` running `axe` and asserting `violations.length === 0`
- AND the appended content is valid TypeScript

---

### Requirement: AA vs. AAA strictness calibration

Agent 19 MUST read `brand-profile.json` to determine the target accessibility level (`a11y_level: "AA"` or `"AAA"`). AAA mode enforces stricter requirements beyond standard AA.

AAA-specific additional requirements:
- All interactive elements MUST have `:focus-visible` CSS indicator (not just `:focus`)
- Color contrast MUST meet WCAG AAA thresholds (7:1 normal text, 4.5:1 large text)
- Sign language video alternatives MUST be noted as required for video content components (flagged, not auto-patched)
- Additional keyboard shortcut documentation is generated in the component doc metadata

#### Acceptance Criteria

- [ ] Agent 19 reads `a11y_level` from `brand-profile.json` before beginning enforcement.
- [ ] AA mode enforces WCAG 2.1 Level AA requirements only.
- [ ] AAA mode enforces all AA requirements PLUS `:focus-visible` presence, AAA contrast thresholds, and marks sign language requirements.
- [ ] Components that cannot be auto-patched to AAA (e.g., require structural redesign) are flagged with `needs_manual_review: true` in `a11y-audit.json` and demoted to Warning.

#### Scenario: AAA mode with missing focus-visible

- GIVEN `brand-profile.json` contains `"a11y_level": "AAA"`
- AND `Button.tsx` uses `:focus` in its token-driven CSS but not `:focus-visible`
- WHEN Agent 19 runs AAA enforcement
- THEN Agent 19 patches `Button.tsx` to add a `data-focus-visible` prop or CSS class pattern that the ThemeProvider resolves to a `:focus-visible` indicator
- AND `a11y-audit.json` records `Button` with `aaaa_focus_visible_patched: true`

---

### Requirement: Post-patch re-validation

After Agent 19 completes all patches for a component, a re-validation pass MUST be run: `tsc --noEmit` on the patched file AND a render validation pass via `playwright_renderer.py`. Failures trigger Agent 19 self-correction (max 3 attempts per component). After 3 failed attempts, the component is flagged with `patch_failed: true` and a structured rejection is written; the original unpatched source is restored from the pre-patch backup.

#### Acceptance Criteria

- [ ] `tsc --noEmit` is run on every patched `.tsx` file immediately after patching.
- [ ] A render validation pass is run on every patched component.
- [ ] TypeScript or render failures trigger Agent 19 self-correction.
- [ ] Self-correction is bounded to 3 attempts per component.
- [ ] After 3 failed self-corrections, the original source is restored and a rejection payload is written.
- [ ] `a11y-audit.json` records the number of correction attempts per component.

#### Scenario: Patch introduces TypeScript error

- GIVEN Agent 19 patches `Accordion.tsx` with a keyboard handler that references an undefined state variable
- WHEN `tsc --noEmit` is run on the patched file
- THEN the compilation fails with an error message
- AND Agent 19 re-patches `Accordion.tsx` on correction attempt 1 with the error message as additional context
- AND `tsc --noEmit` passes on correction attempt 1
- AND `a11y-audit.json` records `Accordion` with `correction_attempts: 1`

#### Scenario: Persistent patch failure after 3 attempts

- GIVEN Agent 19's patches to a complex component fail `tsc --noEmit` on attempts 1, 2, and 3
- WHEN the 3-attempt cap is reached
- THEN the original unpatched source is restored from the pre-patch backup
- AND `a11y-audit.json` records `patch_failed: true, correction_attempts: 3`
- AND a structured rejection payload is written for Agent 6
