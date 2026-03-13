# Specification: Render Validation & Result Assembly

## Purpose

Defines the behavioral requirements for Agent 15 (Render Validation Agent) and Agent 16 (Result Assembly Agent) in the Design-to-Code Crew. Covers headless rendering validation, baseline screenshot capture, per-component render result classification, confidence scoring, and the structure of `reports/generation-summary.json`.

---

## Requirements

### Requirement: Headless render validation per component and variant

Agent 15 (Render Validation Agent) in the Design-to-Code Crew MUST render each generated component and every declared variant headlessly via Playwright. For each render, Agent 15 MUST verify four classes of constraints and record the result.

Validation constraints:
1. **Non-empty output** — each variant produces non-zero visual output (bounding box > 0×0).
2. **Absence of render errors** — no React exceptions, render failures, or hydration warnings appear in the Playwright console.
3. **Minimum dimension thresholds** — components must exceed platform-defined minimum sizes (default: width ≥ 4px, height ≥ 4px).
4. **Distinct interactive states** — hover, focus, disabled, and active states must render visually (bounding box changes or visual indicator detected).

#### Acceptance Criteria

- [ ] For every generated `.tsx` component file, Agent 15 attempts at least one render per declared variant.
- [ ] Each render attempt is classified as `pass`, `warning`, or `fail`.
- [ ] A `pass` requires all four constraint classes to succeed.
- [ ] A `fail` on constraint 1 or 2 (non-empty output or render error) is recorded as `render_failed: true` in the per-component result.
- [ ] A `fail` on constraint 3 or 4 alone is recorded as a `render_warning: true` (not a fatal failure).
- [ ] All render results (pass/warning/fail per component/variant) are written to the per-component render result dict passed to Agent 16.
- [ ] If Playwright is unavailable, all components receive `render_available: false` and render validation is demoted to Warning-level for the entire run.

#### Scenario: All variants pass render validation

- GIVEN all three Button variants (`primary`, `secondary`, `ghost`) render with non-empty output, no console errors, dimensions exceeding minimums, and distinct focus/disabled states
- WHEN Agent 15 validates Button
- THEN Button's render result is `render_failed: false`, `render_warning: false`

#### Scenario: Variant produces zero-size output

- GIVEN `button--ghost` variant renders with bounding box `width: 0, height: 0`
- WHEN Agent 15 validates Button
- THEN `render_failed: true` is set for `button--ghost`
- AND the failure reason `"zero-dimension render"` is recorded

#### Scenario: React exception in console

- GIVEN Playwright console output contains `"Error: Cannot read properties of undefined"`
- WHEN `render_error_detector.py` parses the console log
- THEN `render_failed: true` is set with `error_type: react_exception`

#### Scenario: Playwright unavailable

- GIVEN no Playwright browser binary is found by `playwright_renderer.py`
- WHEN Agent 15 starts task T4
- THEN `render_available: false` is set for all components
- AND no screenshots are captured
- AND the pipeline continues with Warning-level classification (not a Fatal error)

---

### Requirement: Baseline screenshot capture

Agent 15 MUST capture a screenshot of each variant for each component when Playwright is available. Screenshots are stored as baseline references and used by future regression comparison runs.

#### Acceptance Criteria

- [ ] One screenshot is captured per (component × variant) combination.
- [ ] Screenshots are written to `screenshots/{component}/{variant}.png`.
- [ ] If `screenshots/` does not exist, it is created before writing.
- [ ] Screenshot files are not created if `render_available: false`.
- [ ] Screenshot file paths are recorded in the per-component render result dict.

#### Scenario: Baseline screenshot naming

- GIVEN `Button` with variants `[primary, secondary, ghost]`
- WHEN Agent 15 captures baselines
- THEN three files are written: `screenshots/Button/primary.png`, `screenshots/Button/secondary.png`, `screenshots/Button/ghost.png`

---

### Requirement: Per-component confidence scoring

The `confidence_scorer.py` tool (used by Agent 16) MUST compute a 0–100 confidence score for each generated component. The score is a weighted average of five sub-scores:

| Sub-score | Weight | Source |
|-----------|--------|--------|
| Spec completeness | 20% | All required spec fields present and non-empty |
| Lint pass rate | 25% | Fraction of lint checks passing (1.0 if clean, 0.0 if 2-retry exhausted) |
| Variant coverage | 20% | Fraction of declared variants rendered without error |
| Render pass rate | 20% | Fraction of render checks passing (1.0 if no Playwright = N/A, excluded from average) |
| TypeScript compilation | 15% | Binary: 1.0 if `tsc --noEmit` clean, 0.0 if errors |

#### Acceptance Criteria

- [ ] A confidence score between 0 and 100 (inclusive) is computed for every generated component.
- [ ] If Playwright is unavailable, the render pass rate sub-score is excluded and the remaining sub-scores are re-weighted proportionally.
- [ ] Components with a confidence score below 60 are flagged as `low_confidence: true` in `generation-summary.json`.
- [ ] Components with a confidence score ≥ 80 are flagged as `high_confidence: true`.
- [ ] The confidence score formula is deterministic — same inputs always produce the same score.

#### Scenario: Perfect score

- GIVEN a component with complete spec, zero lint errors, all variants rendering cleanly, and clean TypeScript compilation
- WHEN `confidence_scorer.py` computes the score
- THEN the score is 100 and `high_confidence: true` is set

#### Scenario: Low confidence from lint failures

- GIVEN lint pass rate is 0.0, all other sub-scores are 1.0
- WHEN `confidence_scorer.py` computes the score
- THEN the score is `(0.20 + 0 + 0.20 + 0.20 + 0.15) / 1.0 * 100 = 75`
- AND `low_confidence` is not set (≥ 60)

---

### Requirement: Generation summary report assembly

Agent 16 (Result Assembly Agent) in the Design-to-Code Crew MUST assemble all per-component generation results into a structured `reports/generation-summary.json` report and write it before the crew exits.

Required `generation-summary.json` schema:
```json
{
  "run_id": "string (ISO timestamp)",
  "total_components": "number",
  "generated": "number",
  "failed": "number",
  "render_available": "boolean",
  "components": [
    {
      "component": "string",
      "tier": "primitive | simple | complex",
      "files_written": ["string"],
      "confidence_score": "number (0–100)",
      "high_confidence": "boolean",
      "low_confidence": "boolean",
      "lint_warnings": ["string"],
      "render_failed": "boolean",
      "render_warning": "boolean",
      "render_available": "boolean",
      "screenshots": ["string"],
      "token_warnings": ["string"],
      "compilation_passed": "boolean",
      "spec_path": "string"
    }
  ]
}
```

#### Acceptance Criteria

- [ ] `reports/generation-summary.json` is written before the Design-to-Code Crew exits.
- [ ] The `components` array contains one entry per component in the priority queue, regardless of generation success or failure.
- [ ] `total_components` equals the count of specs in the priority queue.
- [ ] `generated` equals the count of components for which at least a `.tsx` file was written.
- [ ] `failed` equals the count of components for which NO `.tsx` file was written.
- [ ] All file paths in `files_written` and `screenshots` are relative to the output directory.
- [ ] The report is valid JSON (parseable by `json.loads`).

#### Scenario: Full successful run

- GIVEN 10 components (starter scope) all generate successfully with no render failures
- WHEN Agent 16 writes `generation-summary.json`
- THEN `total_components: 10`, `generated: 10`, `failed: 0`
- AND each component entry has `render_failed: false` and `compilation_passed: true`

#### Scenario: Partial failure run

- GIVEN 10 components where 1 fails to generate (unresolvable token) and 9 succeed
- WHEN Agent 16 writes `generation-summary.json`
- THEN `total_components: 10`, `generated: 9`, `failed: 1`
- AND the failing component entry has `files_written: []` and `low_confidence: true`

#### Scenario: Report always written on crew exit

- GIVEN the Design-to-Code Crew encounters failures during T3 generation
- WHEN the crew reaches T5 regardless of error count
- THEN `reports/generation-summary.json` is written with all available data
- AND the file is always valid JSON

---

### Requirement: Spec-to-code-to-test traceability mapping

Agent 16 MUST record a traceability map for each component linking the canonical spec, the generated TSX source, the test file, and the story file. This map is consumed by the Drift Detection Agent (33) in Phase 5.

#### Acceptance Criteria

- [ ] Each component entry in `generation-summary.json` includes a `spec_path` field pointing to the source `*.spec.yaml` file.
- [ ] The `files_written` array includes the `.tsx`, `.test.tsx`, and `.stories.tsx` paths (where generated).
- [ ] If a test or story file was not generated (due to failure), the absence is reflected in `files_written` (file simply absent from the array).

#### Scenario: Traceability for Button

- GIVEN `Button` generates all three files successfully
- WHEN Agent 16 assembles the report
- THEN the Button entry includes `spec_path: "specs/components/button.spec.yaml"` and `files_written: ["src/components/Button/Button.tsx", "src/components/Button/Button.test.tsx", "src/components/Button/Button.stories.tsx"]`
