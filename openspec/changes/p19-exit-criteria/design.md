# Design: p19-exit-criteria

## Technical Approach

The change introduces a single `ExitCriteriaEvaluator` (`BaseTool`) that acts as an orchestrator over existing deterministic tools. For each of the 15 §8 criteria, a private helper function (`_check_c1` … `_check_c15`) invokes the appropriate existing tool (or reads files directly), normalises the result to a `CriterionResult` dataclass, and returns it. The evaluator aggregates all 15 results, computes `isComplete` (True iff every Fatal criterion passes), and writes `reports/exit-criteria.json`.

A thin `ExitCriteriaAgent` (Agent 30-bis, Governance Crew) wraps this tool. Its single task calls the evaluator with the output directory, then delegates to `ReportWriter` to persist the summary alongside other governance reports.

The Governance Crew gains a fifth task (`t5_exit_criteria`) that runs after `t4_quality_gate` and before the crew completes. The Release Crew's `t6_final_status` task is updated to read `reports/exit-criteria.json` rather than re-deriving `isComplete` from raw npm/tsc output.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Invoking each of the 15 criterion checks | Deterministic (tool) | All 15 checks are computable from files on disk — no LLM judgment needed |
| Normalising varied tool return shapes to `CriterionResult` | Deterministic (tool internal) | Pure data transformation; deterministic |
| Writing `reports/exit-criteria.json` | Deterministic (tool + ReportWriter) | File write, no inference needed |
| Orchestrating the Governance Crew task sequence | Agent (CrewAI task wiring) | Task dependencies and handoffs follow the existing CrewAI pattern |
| Interpreting `isComplete` for `final_status` mapping in Release Crew | Deterministic (task description) | `success` / `partial` / `failed` mapping is deterministic from the JSON |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 30-bis – Exit Criteria Agent | Tier 3 (Haiku) | `claude-3-haiku-20240307` | The agent does no creative generation; it invokes one tool, reads one file, and writes a report. Haiku is sufficient and economical. |

## Architecture Decisions

### Decision: Single evaluator tool with internal helpers (not 15 separate tools)

**Context:** Each of the 15 criteria could have been its own `BaseTool`, matching the fine-grained tool pattern elsewhere in the codebase. However, the exit criteria evaluation is always executed as an atomic operation — there is no use case for executing a single criterion in isolation.

**Decision:** Implement all 15 criterion runners as private helper functions inside `exit_criteria_evaluator.py`. Expose a single `ExitCriteriaEvaluator` `BaseTool` that runs all 15 and returns the structured report.

**Consequences:** The evaluator is testable as a unit via its internal helpers (called directly in tests); the single-tool interface keeps the Governance Crew's task simple. Future criteria can be added with minimal boilerplate.

---

### Decision: Delegate to existing tools rather than re-implementing logic

**Context:** Several checks (C2 DTCG schema, C5 WCAG contrast, C6 CSS refs) have full implementations in existing tools. Duplicating logic would create drift risk.

**Decision:** The evaluator imports and instantiates existing tools (`DtcgSchemaValidator`, `ContrastSafePairer`, `TokenRefChecker`, `TokenGraphTraverser`, `AstPatternMatcher`, `GateStatusReader`, `DependencyResolver`) and calls their `_run` methods directly from within `_check_cN` helper functions. This is a Python-to-Python call, not an agent tool invocation, so no LLM round-trip occurs.

**Consequences:** The evaluator is tightly coupled to the tool return shapes documented below. Changes to those tools must preserve the fields the evaluator reads. The shapes are documented in the [Tool Interface Reference](#tool-interface-reference) section.

---

### Decision: `isComplete` source of truth moves to `exit-criteria.json`

**Context:** Currently `isComplete` is implicitly derived from `final_status` in `reports/generation-summary.json`, which is set by the Publish Agent (39) based on npm/tsc/test results only (Fatal checks C7/C8/C9). Checks C1–C6 are never aggregated into a single pass/fail signal.

**Decision:** After this change, `reports/exit-criteria.json` becomes the canonical source of truth for `isComplete`. The Release Crew's `t6_final_status` task reads `isComplete` from `exit-criteria.json` and maps it to `final_status: success | partial | failed `.

**Consequences:** The pipeline's completion signal is now complete and spec-accurate. The Publish Agent (39) no longer needs to re-derive `isComplete` from raw subprocess output.

---

### Decision: Graceful degradation for missing upstream artifacts

**Context:** If an upstream crew failed and didn't produce expected files (e.g., no `tokens/` directory, no `reports/governance/quality-gates.json`), individual criterion runners must not raise unhandled exceptions.

**Decision:** Each `_check_cN` helper wraps its IO and tool calls in a `try/except` block. On `FileNotFoundError` or malformed JSON, the criterion returns `passed=False` with `detail="<artifact> not found: <path>"`. The evaluator continues to evaluate all remaining criteria.

**Consequences:** `isComplete` will be `False` when any Fatal criterion cannot be evaluated due to missing files, which is the correct behavior. The report surfaces the cause in the `detail` field.

## Data Flow

```
[Governance Crew]
    t4_quality_gate (Agent 30)
        writes ──► reports/governance/quality-gates.json

    t5_exit_criteria (Agent 30-bis) NEW
        reads  ──► tokens/*.tokens.json              (C1, C2, C3, C4)
        reads  ──► reports/governance/quality-gates.json (C12)
        reads  ──► reports/generation-summary.json   (C9, C15)
        reads  ──► src/components/**/*.tsx            (C10, C11)
        reads  ──► reports/governance/drift-report.json (C13)
        reads  ──► reports/component-registry.json   (C14)
        runs   ──► tsc --noEmit subprocess            (C7)
        runs   ──► npm build subprocess               (C8)
        writes ──► reports/exit-criteria.json

[Release Crew]
    t6_final_status (Agent 39)
        reads  ──► reports/exit-criteria.json
        writes ──► reports/generation-summary.json (isComplete, final_status)
```

## Retry & Failure Behavior

- The Governance Crew runs in Phase 3a (§3.2). Per §3.4, Phase 4–6 crews retry at crew level (max 2 attempts, no per-agent retry).
- If `t5_exit_criteria` fails (tool error, not criterion failure), the Governance Crew re-runs entirely on the second attempt.
- A criterion returning `passed=False` is not a tool error — the evaluator succeeds and records the failure in the report. Retries are not triggered by criterion failures; they are surfaced in Human Gate 2 review.
- `isComplete: false` (all Fatal criteria pass but some Warning criteria fail) does not trigger a crew retry — the pipeline continues, and the report surfaces warnings for Human Gate 2.

## File Changes

- `src/daf/tools/exit_criteria_evaluator.py` (new) — `CriterionResult` dataclass, 15 private check helpers, `ExitCriteriaEvaluator` BaseTool
- `src/daf/agents/exit_criteria.py` (new) — `create_exit_criteria_agent(model, output_dir)` factory for Agent 30-bis
- `src/daf/crews/governance.py` (modified) — add `t5_exit_criteria` Task after `t4_quality_gate`; import `create_exit_criteria_agent`
- `src/daf/crews/release.py` (modified) — update `t6_final_status` task description to read from `reports/exit-criteria.json`
- `tests/test_exit_criteria_evaluator.py` (new) — unit tests for all 15 check helpers and the evaluator aggregation logic
- `tests/test_exit_criteria_agent.py` (new) — unit test for agent factory

## Tool Interface Reference

The following tool return shapes are consumed by `ExitCriteriaEvaluator`:

| Tool | `_run` Return Shape | Fields Used |
|------|---------------------|-------------|
| `DtcgSchemaValidator` | `{"fatal": [...], "warnings": [...]}` | `fatal` (empty → passed) |
| `ContrastSafePairer` | `{"pairs": [...], "all_pass": bool}` | `all_pass` |
| `TokenRefChecker.check_token_refs` | `{"unresolved": [...], "all_resolved": bool}` | `all_resolved` |
| `TokenGraphTraverser` | `{"tokens": [...], "unresolved_refs": [...]}` | `unresolved_refs` (empty → passed) |
| `AstPatternMatcher` | `{"targets": [...]}` | `targets` filtered by `type == "hardcoded_color"` |
| `GateStatusReader` | `{"fatal_pass": int, "fatal_fail": int, ...}` | quality score pass counts |
| `DependencyResolver` | `{"success": bool, "errors": [...]}` | `success` |
