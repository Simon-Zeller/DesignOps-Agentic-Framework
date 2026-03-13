# Proposal: p12-component-factory-crew

## Intent

The Design-to-Code Crew (p11) now produces real TSX source, unit tests, Storybook stories, and a `generation-summary.json` report for every component in scope. However, the Component Factory Crew — Phase 3's quality gate immediately downstream — remains a no-op stub. Its stub writes empty JSON placeholders to `reports/quality-scorecard.json`, `reports/a11y-audit.json`, and `reports/composition-audit.json`, performing no spec validation, no composition checking, no accessibility enforcement, and no quality scoring.

Without the Component Factory Crew, the pipeline accepts all generated TSX unconditionally. Components with broken ARIA attributes, invalid composition hierarchies, unresolved token references, or failing quality gates flow unchanged into Phase 4 (Documentation and Governance), producing reports and ownership maps over fundamentally invalid code.

This change delivers the real Component Factory Crew: 4 agents (17–20) that validate canonical specs, verify structural composition against primitive rules, enforce and patch accessibility requirements, and gate each component against a 70/100 composite quality threshold — ensuring only structurally sound, accessible, token-compliant code reaches downstream crews.

## Scope

### In scope

- **Agent 17: Spec Validation Agent** (`src/daf/agents/spec_validation.py`) — validates every `specs/*.spec.yaml` against JSON Schema: required fields present, all token references resolve against compiled token files, state machine transitions are valid (no impossible state paths), nesting rules respected, prop types complete.
- **Agent 18: Composition Agent** (`src/daf/agents/composition.py`) — verifies every generated component composes exclusively from the 9 base primitives (Box, Stack, Grid, Text, Icon, Pressable, Divider, Spacer, ThemeProvider). Checks: allowed-children constraints, forbidden nesting patterns (e.g., no Pressable inside Pressable), required slots filled, composition depth within limits.
- **Agent 19: Accessibility Agent** (`src/daf/agents/accessibility.py`) — reviews and patches every component for: correct ARIA roles and attributes per state, keyboard navigation handlers (Tab, Enter, Escape, Arrow keys), focus management (trap, restore, programmatic focus), screen-reader announcements for dynamic state changes. Appends component-level a11y test blocks to existing `.test.tsx` files (inside a `describe('Accessibility', ...)` suite — not as new files). Reads `brand-profile.json` for target accessibility level (AA or AAA) to calibrate enforcement strictness.
- **Agent 20: Quality Scoring Agent** (`src/daf/agents/quality_scoring.py`) — computes the composite quality score (0–100) per component from five weighted sub-scores: test coverage 25%, a11y pass rate 25%, token compliance 20%, composition depth 15%, spec completeness 15%. Flags components scoring below 70/100 in the quality report. Writes `reports/quality-scorecard.json`, `reports/a11y-audit.json`, and `reports/composition-audit.json`.
- **Component Factory Crew factory** (`src/daf/crews/component_factory.py`) — replaces the stub with a real CrewAI `Crew` sequencing tasks T1→T5 (validate specs → verify composition → scaffold/enforce a11y → re-validate patched components → score and gate). Preserves factory function signature (`create_component_factory_crew(output_dir)`) so the pipeline orchestrator requires no changes.
- **New tools** (under `src/daf/tools/`):
  - `json_schema_validator.py` — validates a spec YAML dict against a JSON Schema definition; returns structured validation errors.
  - `token_ref_checker.py` — resolves all `$value` token references in a spec against the compiled token files; reports unresolved refs.
  - `state_machine_validator.py` — parses spec-declared states and transitions; detects impossible states, unreachable states, and missing terminal transitions.
  - `composition_rule_engine.py` — applies allowed-children and forbidden-nesting rules from spec to the component's TSX AST; returns rule violations.
  - `primitive_registry.py` — maintains the canonical list of the 9 base primitives and 11 exports; used by the Composition Agent to classify JSX elements as primitive or non-primitive.
  - `nesting_validator.py` — walks the TSX AST to detect forbidden nesting patterns (e.g., interactive-inside-interactive) and reports depth violations.
  - `aria_generator.py` — maps spec-declared ARIA requirements and component states to concrete ARIA role + attribute assignments; outputs patch instructions.
  - `keyboard_nav_scaffolder.py` — generates keyboard event handler stubs (onKeyDown) for Tab, Enter, Escape, and Arrow key patterns based on component type and states.
  - `focus_trap_validator.py` — inspects TSX source for focus trap implementation correctness in modal/overlay components; verifies restore-on-close behaviour.
  - `coverage_reporter.py` — reads Vitest coverage output (lcov/json) for a specific component file and returns the line coverage percentage.
  - `score_calculator.py` — computes the weighted 0–100 composite quality score from the five sub-score inputs; returns per-component score breakdown.
  - `threshold_gate.py` — applies the 70/100 composite gate; returns pass/fail verdict and the components list requiring retry.
- **Tests** — unit tests for every new tool and agent; integration test for the full Component Factory Crew flow (TSX-in → patched TSX + reports-out, gate applied).

### Out of scope

- Implementing the Documentation Crew (Agents 21–25) and Governance Crew (Agents 26–30) — downstream crews; addressed in subsequent changes.
- The Governance Crew's separate 80% minimum test coverage gate (Quality Gate Agent 30) — that gate is implemented as part of the Governance Crew change, not here. The 70/100 composite gate here is independent.
- Visual regression diffing against prior baselines — the Render Validation Agent (15) captures baselines; regression comparison is a future incremental change.
- Performance profiling or bundle-size analysis — this crew enforces correctness, not output size.
- Cross-phase retry initiation — the Component Factory Crew surfaces structured rejection payloads but does not initiate retries directly; retry routing remains with Agent 6 (First Publish Agent, §3.4).

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| Component Factory | Agent 17: Spec Validation Agent | **New implementation** — replaces stub task |
| Component Factory | Agent 18: Composition Agent | **New implementation** — replaces stub task |
| Component Factory | Agent 19: Accessibility Agent | **New implementation** — replaces stub task |
| Component Factory | Agent 20: Quality Scoring Agent | **New implementation** — replaces stub task |
| DS Bootstrap | Agent 6: First Publish Agent | Retry routing — receives structured rejection payloads from Agent 17/18 for spec-level failures (§3.4) |
| Design-to-Code | Agent 14: Code Generation Agent | Upstream producer — generated TSX, tests, and stories are the primary input |
| Design-to-Code | Agent 15: Render Validation Agent | Upstream producer — render pass/fail and screenshot baselines feed Agent 20's a11y pass rate sub-score |
| Design-to-Code | Agent 16: Result Assembly Agent | Upstream producer — `reports/generation-summary.json` is read for confidence scores and variant coverage |
| Documentation | Agents 21–25 | Downstream consumers — they now receive validated, a11y-patched TSX and quality scores instead of stubs |
| Governance | Agents 26–30 | Downstream consumers — `reports/quality-scorecard.json` feeds the Quality Gate Agent (30) for the separate 80% test coverage check |
| Analytics | Agents 36–40 | Downstream consumers — token compliance data and quality scores feed the analytics layer |

## PRD References

- §3.4 — Cross-phase retry routing: Component Factory surfaces rejections that Agent 6 uses to re-invoke Agent 14 with accumulated context
- §3.6 — Crew I/O contracts: Component Factory inputs (`specs/*.spec.yaml`, `src/primitives/*.tsx`, `src/components/**/*.tsx`, `tokens/semantic.tokens.json`, `brand-profile.json`) and outputs (`reports/quality-scorecard.json`, `reports/a11y-audit.json`, `reports/composition-audit.json`, patched `src/` in place)
- §4.4 — Component Factory Crew: all 4 agents (17–20), tasks T1–T5, NFR (<60s per component)
- §4.4 (post-patch re-validation) — after a11y patching, re-run `tsc --noEmit` + Render Validation Agent on patched source; failures fed back to Agent 19
- §4.4 (Quality Scoring Agent) — composite score formula, 70/100 gate, five sub-scores with weights
- §8 — Exit criteria: Fatal F5 (WCAG contrast checks triggered by a11y audit), Fatal F2 (DTCG schema re-check after token ref resolution), Warning W1 (test failures in appended a11y test blocks)

## Pipeline Impact

- [ ] Pipeline phase ordering — Component Factory is already sequenced in Phase 3 by Agent 6; order is unchanged
- [x] Crew I/O contracts (§3.6) — Component Factory now writes real `quality-scorecard.json`, `a11y-audit.json`, and `composition-audit.json`; patches `src/` in place with a11y fixes; downstream crews consume real artifacts
- [x] Retry protocol (§3.4) — Agent 17 and 18 produce structured rejection payloads (invalid spec fields, unresolved token refs, composition violations) that enable Agent 6 to trigger targeted per-component retry of Agent 14
- [ ] Human gate policy (§5) — not affected
- [x] Exit criteria (§8) — Fatal F5 (WCAG contrast, enforced by Agent 19 via axe-core rules) and Warning W1 (a11y test blocks appended by Agent 19) are activated by this crew's output
- [ ] Brand Profile schema (§6) — Brand Profile is read by Agent 19 (AA vs AAA level) but its schema is not modified

## Approach

1. **New tools first (TDD)** — implement all 12 new tools with full unit test coverage before wiring agents. Tools are pure, deterministic functions testable in isolation.
2. **Four agents** — implement Agents 17–20 as CrewAI `Agent` objects with tool bindings. Tier assignment follows PRD complexity guidelines:
   - Agent 17 (Spec Validation): Tier-3 Haiku — structured JSON Schema validation, deterministic.
   - Agent 18 (Composition Agent): Tier-3 Haiku — rule-based AST traversal, deterministic.
   - Agent 19 (Accessibility Agent): Tier-2 Sonnet — interpretive reasoning over ARIA semantics, keyboard navigation patterns, and focus management; requires nuanced judgement.
   - Agent 20 (Quality Scoring): Tier-3 Haiku — arithmetic aggregation and threshold gating, fully deterministic.
3. **Post-patch re-validation** — after Agent 19 patches TSX source, trigger a re-validation pass: `tsc --noEmit` via subprocess + re-invoke Render Validation Agent (15) tools. If this fails, feed structured errors back to Agent 19 for correction (bounded to 3 correction attempts per component, per §3.4).
4. **Component Factory Crew factory** — replace the stub in `src/daf/crews/component_factory.py` with a real CrewAI `Crew` sequencing T1→T5. Preserve the factory function signature so the pipeline orchestrator requires no changes.
5. **Integration test** — one end-to-end test that feeds minimal TSX fixture + compiled tokens + spec YAML and asserts that `quality-scorecard.json`, `a11y-audit.json`, `composition-audit.json` are written correctly and a11y patches are applied to the TSX source.

## Risks

- **TSX AST parsing brittleness** — the Composition Agent and Accessibility Agent must parse generated TSX to inspect imports and JSX nesting. Mitigation: use Python's `ast`-compatible regex patterns or invoke `ts-node` via subprocess to extract AST data; treat AST parse failures as Warning (not Fatal) and fall back to source-text heuristics.
- **axe-core headless dependency** — Agent 19 references axe-core rule definitions for ARIA validation. Mitigation: ship a minimal subset of axe-core rule metadata as a JSON fixture in the package; no browser required for rule-name lookups, only for full runtime a11y audits (which remain in Governance scope).
- **Post-patch re-validation cost** — re-running `tsc --noEmit` and render validation per patched component could exceed the 60s per-component NFR at large scope. Mitigation: scope re-validation to only the patched files; use incremental TypeScript compilation (`--incremental`) where possible.
- **Coverage data availability** — `coverage_reporter.py` reads Vitest lcov output, which only exists if tests were run with coverage instrumentation. Mitigation: if coverage data is absent, the test coverage sub-score defaults to 0 (worst case) and a Warning is emitted — the composite score still runs.
- **AA vs AAA enforcement variance** — Agent 19 calibrates strictness from `brand-profile.json`. If the Brand Profile specifies AAA, some components may require structural changes (e.g., mandatory focus-visible on all interactive elements) that Agent 19 cannot patch in isolation. Mitigation: such components are flagged with `needs-manual-review: true` in `a11y-audit.json` and demoted to Warning threshold rather than causing Fatal failures.
