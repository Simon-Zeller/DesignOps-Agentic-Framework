# Design: p12-component-factory-crew

## Technical Approach

The Component Factory Crew replaces the no-op stub in `src/daf/crews/component_factory.py` with a real CrewAI `Crew` that sequences four agents (17–20) across tasks T1–T5. The crew receives generated TSX source, unit test files, Storybook stories, and a `generation-summary.json` from the Design-to-Code Crew (p11), plus the canonical spec YAMLs, compiled token files, and the Brand Profile from the shared output directory.

The crew follows a linear pipeline with one conditional re-validation branch:

1. **T1 — Spec Validation** (Agent 17): Reads every `specs/*.spec.yaml` and validates it against JSON Schema. Checks required fields, token reference resolution against compiled token files, state machine transition validity, and prop completeness. Produces a validation report; invalid specs are flagged as structured rejections for Agent 6 retry routing.
2. **T2 — Composition Verification** (Agent 18): Reads every generated `.tsx` file and verifies it composes exclusively from the 9 base primitives. Checks allowed-children constraints, forbidden nesting patterns (e.g., Pressable inside Pressable), required slot compliance, and composition depth limits.
3. **T3 — Accessibility Enforcement** (Agent 19): Reviews every component for correct ARIA roles/attributes per state, keyboard navigation handlers, focus management, and dynamic screen-reader announcements. Patches TSX source in place for fixable issues. Reads `brand-profile.json` for AA vs. AAA strictness calibration. Appends a `describe('Accessibility', ...)` test block to each `.test.tsx` file after the `// @accessibility-placeholder` marker.
4. **T4 — Post-Patch Re-validation** (Agent 19, continued): After patching, re-runs `tsc --noEmit` and re-invokes the render validation tools on patched source. If this fails, feeds structured errors back to Agent 19 for correction (bounded to 3 correction attempts per component).
5. **T5 — Quality Scoring and Gating** (Agent 20): Computes the 0–100 composite quality score per component from five weighted sub-scores. Applies the 70/100 gate. Writes `reports/quality-scorecard.json`, `reports/a11y-audit.json`, and `reports/composition-audit.json`.

All 12 new tools are deterministic Python modules with no LLM calls. Agents call them as CrewAI tools. LLM reasoning is bounded to ARIA semantic interpretation, keyboard navigation pattern selection, and a11y triage — all other operations are verifiable and unit-testable.

The crew factory signature `create_component_factory_crew(output_dir: str) -> Crew` is preserved from the stub, so the pipeline orchestrator requires no changes.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Validate spec YAML against JSON Schema | Deterministic (`json_schema_validator.py`) | Schema validation is fully structural; no LLM judgment required |
| Resolve token references in specs | Deterministic (`token_ref_checker.py`) | Reference lookup against compiled token JSON is a deterministic key lookup |
| Validate state machine transitions | Deterministic (`state_machine_validator.py`) | Reachability analysis on a finite directed graph; deterministic algorithm |
| Verify primitive composition from TSX AST | Deterministic (`composition_rule_engine.py` + `nesting_validator.py`) | AST traversal with rule lookup against `primitive_registry.py`; no interpretation needed |
| Map spec a11y requirements to ARIA attributes | Deterministic (`aria_generator.py`) | WAI-ARIA role-to-attribute mapping is fully specified; no generative reasoning needed |
| Scaffold keyboard event handlers | Agent 19 (LLM: Sonnet) | Keyboard interaction patterns vary by component semantic role (e.g., listbox vs. dialog vs. combobox); requires contextual judgement beyond rule lookup |
| Patch TSX source for a11y compliance | Agent 19 (LLM: Sonnet) | Code-level patching requires understanding existing code structure and producing syntactically valid TypeScript |
| Validate focus trap implementation | Deterministic (`focus_trap_validator.py`) | Pattern-based AST check for modal/overlay components; presence/absence of known focus trap primitives |
| Append a11y test blocks to .test.tsx | Agent 19 (LLM: Sonnet) | A11y test cases require meaningful assertions based on component semantics; not pure template expansion |
| Retrieve test line coverage | Deterministic (`coverage_reporter.py`) | Reads LCOV JSON output; pure arithmetic |
| Compute composite quality score | Deterministic (`score_calculator.py`) | Weighted average of numeric sub-scores; deterministic formula |
| Apply 70/100 threshold gate | Deterministic (`threshold_gate.py`) | Numerical threshold comparison; no interpretation |
| Re-run `tsc --noEmit` after patching | Deterministic (subprocess in crew) | TypeScript compiler invocation; deterministic pass/fail |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 17: Spec Validation Agent | Tier-3 | Claude Haiku | Fully deterministic tool orchestration — schema validation, token lookup, state graph analysis. LLM only orchestrates tool calls and formats the validation report. |
| Agent 18: Composition Agent | Tier-3 | Claude Haiku | Rule-based AST traversal with deterministic tool output. LLM only collects tool results and structures the composition audit. |
| Agent 19: Accessibility Agent | Tier-2 | Claude Sonnet | Requires interpretation of component semantics to select appropriate keyboard patterns, produce syntactically valid TSX patches, and generate meaningful a11y test assertions. Context window needed for reading and modifying component source. |
| Agent 20: Quality Scoring Agent | Tier-3 | Claude Haiku | Pure aggregation of numeric sub-scores from tool outputs. No generative reasoning required. |

## Architecture Decisions

### Decision: Post-patch re-validation is owned by Agent 19 within T3/T4, not by a separate agent

**Context:** The PRD (§4.4) specifies a re-validation pass after Agent 19 patches source. This re-validation reuses tools from the Design-to-Code Crew (render validation, TypeScript compilation).

**Decision:** Agent 19 owns the re-validation loop directly. After patching, it calls `tsc --noEmit` via subprocess and re-invokes `playwright_renderer.py` / `render_error_detector.py` tools on the patched files. Failures trigger Agent 19 self-correction (max 3 attempts). Only if all 3 attempts fail does it escalate to a structured rejection for Agent 6.

**Consequences:** No new agent is required for re-validation, keeping the crew at 4 agents. Re-validation tools are shared with the Design-to-Code Crew (imported from `src/daf/tools/`). The crew is slightly asymmetric (Agent 19 spans T3 and T4) but this mirrors the PRD's task sequence.

---

### Decision: TSX AST parsing uses source-text heuristic pattern matching, not a full TypeScript AST parser

**Context:** Parsing TypeScript AST in Python requires either spawning a `ts-node` subprocess or using a limited regex/text approach. Full AST parsing via `ts-node` adds latency and a Node.js dependency.

**Decision:** `composition_rule_engine.py` and `nesting_validator.py` use a two-pass approach: (1) import statement analysis via regex to detect non-primitive imports, and (2) JSX element name scanning via regex to detect direct DOM element usage and forbidden nesting patterns. If a component's source is structurally complex enough to defeat heuristic scanning, it falls back to spawning `ts-node --eval` for targeted AST queries.

**Consequences:** Most composition violations are caught by the fast heuristic pass (<5ms). The `ts-node` fallback adds latency only for complex components that defeat heuristics. Heuristic false-negative rate is accepted as Warning-level (not Fatal) because composition violations detected here trigger retry, not hard failure.

---

### Decision: `// @accessibility-placeholder` is the append point for a11y test blocks

**Context:** The Design-to-Code Crew (p11) embeds an `// @accessibility-placeholder` comment at the end of each `.test.tsx` file. Agent 19 must add a11y test blocks to these files without overwriting existing tests.

**Decision:** Agent 19 reads the full `.test.tsx` file, locates `// @accessibility-placeholder`, and appends the new `describe('Accessibility', ...)` block immediately after it. If the placeholder is missing (e.g., manually created test files), Agent 19 appends to the end of the file unconditionally and logs a Warning.

**Consequences:** Test files remain single-file-per-component (PRD §4.4). The placeholder convention established in p11 is enforced. Manual test files without the placeholder receive a11y blocks appended to EOF, which is safe.

---

### Decision: Coverage data absence is a Warning, not a Fatal failure

**Context:** `coverage_reporter.py` reads Vitest LCOV/JSON coverage output. This output only exists if Vitest was run with `--coverage`. On first pipeline runs or in environments without coverage instrumentation, coverage data may be absent.

**Decision:** If coverage data is absent for a component, `coverage_reporter.py` returns `None`. `score_calculator.py` treats `None` as `0.0` for the test coverage sub-score and adds a `coverage_unavailable: true` flag to the score breakdown. This is recorded as a Warning in `quality-scorecard.json`.

**Consequences:** Quality scores can still be computed in environments without coverage tooling. Components with `coverage_unavailable: true` are visibly flagged for operators. The composite score worst-cases at 75/100 (assuming other four sub-scores are perfect), which may still pass the 70/100 gate — this is intentional, as missing coverage data is an infrastructure gap, not a code quality failure.

---

### Decision: Rollback cascade is handled by Agent 6 / Rollback Agent — Component Factory only writes structured checkpoints

**Context:** PRD §4.4 notes that Component Factory patches `src/` in place for a11y fixes. If a rollback is triggered, these patches are lost and the crew must re-run. PRD §3.4 assigns rollback cascade management to Agent 6 (First Publish Agent) and Agent 40 (Rollback Agent).

**Decision:** The Component Factory Crew writes a checkpoint marker (`checkpoints/component-factory.json`) after T5 completes. This is the only rollback-related action it takes. Cascade invalidation and re-run orchestration remain with Agent 6 / Agent 40 as specified in §3.4.

**Consequences:** Component Factory is not responsible for its own rollback logic. The checkpoint file is the signal that Agent 6 uses to detect completion and resume-on-failure via `--resume`. This preserves the existing checkpoint protocol established by the pipeline orchestrator.

## Data Flow

```
[Design-to-Code Crew (p11)]
  ──writes──► src/primitives/*.tsx
  ──writes──► src/components/**/*.tsx
  ──writes──► src/components/**/*.test.tsx   (contains // @accessibility-placeholder)
  ──writes──► src/components/**/*.stories.tsx
  ──writes──► reports/generation-summary.json
  ──writes──► screenshots/*
              │
[DS Bootstrap (p06/p07)]
  ──writes──► specs/primitives/*.spec.yaml
  ──writes──► specs/components/**/*.spec.yaml
              │
[Token Engine Crew (p10)]
  ──writes──► tokens/compiled/**
  ──writes──► tokens/semantic.tokens.json
              │
[DS Bootstrap / Interview (p02)]
  ──writes──► brand-profile.json
              │
              ▼
[Component Factory Crew (p12)] ─── T1: Spec Validation (Agent 17)
                                ├── T2: Composition Verification (Agent 18)
                                ├── T3/T4: Accessibility & Re-validation (Agent 19)
                                └── T5: Quality Scoring & Gate (Agent 20)
              │
              ├──patches──► src/components/**/*.tsx         (a11y patches in place)
              ├──appends──► src/components/**/*.test.tsx    (a11y describe blocks)
              ├──writes──► reports/quality-scorecard.json
              ├──writes──► reports/a11y-audit.json
              ├──writes──► reports/composition-audit.json
              └──writes──► checkpoints/component-factory.json
              │
              ▼
[Documentation Crew (Phase 4a)] ── reads src/ (patched), reports/quality-scorecard.json
[Governance Crew (Phase 4b)]    ── reads reports/quality-scorecard.json (80% coverage gate)
[Analytics Crew (Phase 5)]      ── reads reports/quality-scorecard.json, a11y-audit.json
```

## Retry & Failure Behavior

**Agent 17 (Spec Validation) failures:** Invalid spec fields or unresolved token references produce a structured rejection payload (`_rejection_file.py` pattern). Agent 6 reads the rejection and re-invokes the design-to-code → spec authoring path (§3.4). The crew records the invalid components in the validation report and continues processing valid specs (spec validation failure is per-component, not a crew-level fatal).

**Agent 18 (Composition) failures:** Forbidden nesting or non-primitive imports produce a structured rejection. The crew records violations in `composition-audit.json`. Composition failures trigger an Agent 6 retry of Agent 14 (Code Generation) for the failing components, with the composition violation context appended to the generation prompt.

**Agent 19 (Accessibility) post-patch re-validation failure:** If `tsc --noEmit` or renderer fails after an a11y patch, Agent 19 self-corrects (max 3 attempts). After 3 failed attempts, the component is flagged with `patch_failed: true` in `a11y-audit.json` and a structured rejection is written for Agent 6. The original (unpached) source is restored from the pre-patch backup.

**Agent 20 (Quality Scoring) gate failure:** Components below 70/100 are not fatal crew failures. They are flagged in `quality-scorecard.json` with `gate: "failed"` and trigger an Agent 6 retry of the Design-to-Code → Component Factory loop for those components only (max 3 retries at the per-component level, per §3.4). If a component fails the gate after 3 retry cycles, it is marked `gate: "failed-final"` and the crew proceeds without it — downstream crews must handle missing components gracefully.

## File Changes

- `src/daf/crews/component_factory.py` (modified) — replace stub with real CrewAI `Crew` sequencing Agents 17–20 across T1–T5
- `src/daf/agents/spec_validation.py` (new) — Agent 17: Spec Validation Agent (Tier-3 Haiku)
- `src/daf/agents/composition.py` (new) — Agent 18: Composition Agent (Tier-3 Haiku)
- `src/daf/agents/accessibility.py` (new) — Agent 19: Accessibility Agent (Tier-2 Sonnet)
- `src/daf/agents/quality_scoring.py` (new) — Agent 20: Quality Scoring Agent (Tier-3 Haiku)
- `src/daf/tools/json_schema_validator.py` (new) — validates spec dicts against JSON Schema definitions
- `src/daf/tools/token_ref_checker.py` (new) — resolves token references from spec against compiled token files
- `src/daf/tools/state_machine_validator.py` (new) — validates state/transition graphs in spec for reachability and completeness
- `src/daf/tools/composition_rule_engine.py` (new) — applies allowed-children and forbidden-nesting rules to TSX source
- `src/daf/tools/primitive_registry.py` (new) — canonical registry of the 9 base primitives and 11 exports
- `src/daf/tools/nesting_validator.py` (new) — checks TSX for forbidden nesting patterns and depth violations
- `src/daf/tools/aria_generator.py` (new) — maps spec a11y requirements and states to concrete ARIA role/attribute patch instructions
- `src/daf/tools/keyboard_nav_scaffolder.py` (new) — generates onKeyDown handler stubs for component keyboard interaction patterns
- `src/daf/tools/focus_trap_validator.py` (new) — inspects TSX for focus trap correctness in modal/overlay components
- `src/daf/tools/coverage_reporter.py` (new) — reads Vitest LCOV/JSON output and returns line coverage per component file
- `src/daf/tools/score_calculator.py` (new) — computes weighted 0–100 composite quality score from five sub-score inputs
- `src/daf/tools/threshold_gate.py` (new) — applies the 70/100 gate and returns pass/fail list with score breakdown
- `tests/test_json_schema_validator.py` (new) — unit tests for `json_schema_validator.py`
- `tests/test_token_ref_checker.py` (new) — unit tests for `token_ref_checker.py`
- `tests/test_state_machine_validator.py` (new) — unit tests for `state_machine_validator.py`
- `tests/test_composition_rule_engine.py` (new) — unit tests for `composition_rule_engine.py`
- `tests/test_primitive_registry.py` (new) — unit tests for `primitive_registry.py`
- `tests/test_nesting_validator.py` (new) — unit tests for `nesting_validator.py`
- `tests/test_aria_generator.py` (new) — unit tests for `aria_generator.py`
- `tests/test_keyboard_nav_scaffolder.py` (new) — unit tests for `keyboard_nav_scaffolder.py`
- `tests/test_focus_trap_validator.py` (new) — unit tests for `focus_trap_validator.py`
- `tests/test_coverage_reporter.py` (new) — unit tests for `coverage_reporter.py`
- `tests/test_score_calculator.py` (new) — unit tests for `score_calculator.py`
- `tests/test_threshold_gate.py` (new) — unit tests for `threshold_gate.py`
- `tests/test_spec_validation_agent.py` (new) — unit tests for Agent 17
- `tests/test_composition_agent.py` (new) — unit tests for Agent 18
- `tests/test_accessibility_agent.py` (new) — unit tests for Agent 19
- `tests/test_quality_scoring_agent.py` (new) — unit tests for Agent 20
- `tests/test_component_factory_crew.py` (new) — integration test: TSX fixture + spec YAML + compiled tokens → patched source + reports + gate verdicts
