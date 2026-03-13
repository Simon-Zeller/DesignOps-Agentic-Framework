# Design: p15-analytics-crew

## Technical Approach

Replace the `StubCrew` in `src/daf/crews/analytics.py` with a real `crewai.Crew` housing five agents (Agents 31–35). Each agent encapsulates its decision logic via an LLM-backed `crewai.Agent`, while the heavy file-system work (AST scanning, diff comparison, report writing) is delegated to deterministic tool classes in `src/daf/tools/`.

The crew follows the exact same structural pattern established by the Governance and Documentation crews:
1. Factory function `create_analytics_crew(output_dir: str) → Crew`
2. Pre-flight guard checking for required input files
3. Five tasks `T1→T5` wired sequentially (`context=[previous_task]`)
4. Each agent created via a `create_<agent>_agent(model, output_dir)` factory in `src/daf/agents/`

New deterministic tool classes are added to `src/daf/tools/` for capabilities not already covered by existing tools. Where a tool already exists (e.g. `compute_token_compliance` in `composition_rule_engine.py`), it is reused directly rather than reimplemented.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Identify which tokens are "used vs. defined-but-unused" | Deterministic | Pure set-intersection of token keys found in TSX AST vs. DTCG JSON keys — no judgment needed |
| Summarise unused token patterns and recommend removals | Agent (LLM) | Requires contextual reasoning about naming conventions and intent |
| Detect hardcoded colour/spacing/font-size literals in TSX | Deterministic | Regex + AST walk — exact rules, zero ambiguity |
| Suggest replacement token for each violation | Agent (LLM) | Requires semantic matching of a hardcoded value to the nearest semantic token |
| Structural comparison of spec vs. TSX prop list | Deterministic | Parse YAML props array, extract TSX prop types via regex — mechanical diff |
| Classify drift as auto-fixable vs. requires-re-run | Agent (LLM) | Requires understanding authoritativeness hierarchy (spec > code > docs) |
| Patch docs Markdown in place for auto-fixable drift | Deterministic | String/AST replacement — no LLM needed |
| Track component stage completeness | Deterministic | Presence checks on known output file paths per component name |
| Recommend intervention per stuck component | Agent (LLM) | Context-sensitive recommendation based on which stage is missing |
| Build test-failure dependency chain | Deterministic | Graph traversal of `dependency_graph.json`; topological + failure-set intersection |
| Classify failure as root-cause vs. downstream | Agent (LLM) | Requires reasoning over the graph to assign cause attribution |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 31 – Usage Tracking Agent | Tier 3 | `claude-3-5-haiku-20241022` | Summarisation and recommendation over already-computed data; speed > depth |
| Agent 32 – Token Compliance Agent | Tier 3 | `claude-3-5-haiku-20241022` | Pattern matching with token substitution suggestions; structured output, low reasoning load |
| Agent 33 – Drift Detection Agent | Tier 2 | `claude-3-5-sonnet-20241022` | Must reason over authoritativeness hierarchy and decide fixability; moderate complexity |
| Agent 34 – Pipeline Completeness Agent | Tier 3 | `claude-3-5-haiku-20241022` | Completeness summary and remediation advice; structured, low ambiguity |
| Agent 35 – Breakage Correlation Agent | Tier 2 | `claude-3-5-sonnet-20241022` | Graph-based causal reasoning; failure attribution requires Sonnet-level inference |

## Architecture Decisions

### Decision: Reuse `compute_token_compliance` instead of a new tool

**Context:** `src/daf/tools/composition_rule_engine.py` already implements hardcoded-value detection for per-component use during Phase 3 composition checks. Agent 32 needs the same capability at crew scope across all output TSX files.

**Decision:** Agent 32's tool (`TokenComplianceTool`) internally calls `compute_token_compliance` from `composition_rule_engine`, aggregating results across all TSX files in `src/`. A thin wrapper reports per-file violations enriched with the suggested replacement token key from the token map.

**Consequences:** No duplication of scanning logic; any improvements to the underlying detection logic automatically benefit both the Composition Agent and the Analytics Crew.

### Decision: Drift Detection Agent auto-patches docs in place, not via LLM

**Context:** PRD §4.7 specifies that auto-fixable drift (docs missing a prop present in code and spec) should be corrected in place. The LLM determines *what* to fix; the actual file write is deterministic.

**Decision:** The `DriftReporter` tool identifies fixable items and prepares a patch spec; the `DocPatcher` tool applies the literal string substitution. The agent decides *whether* to fix (authoritativeness judgment) and passes the instruction to the tool; the tool applies it exactly.

**Consequences:** Deterministic doc writes are safe to unit-test without LLM mocking. The boundary between LLM decision and deterministic write is explicit.

### Decision: Analytics Crew uses a pre-flight guard on `specs/` directory

**Context:** Agent 31 (Usage Tracking) and Agent 33 (Drift Detection) require `specs/*.spec.yaml` to be present. These are produced by Phase 1 (Token Engine Crew).

**Decision:** `create_analytics_crew` raises `RuntimeError` if no `*.spec.yaml` files are found in `<output_dir>/specs/`. This mirrors the pattern in the Governance Crew (check for `docs/component-index.json`).

**Consequences:** Fast-fail with a descriptive error if the crew is invoked out of pipeline order; no silent empty-report generation.

## Data Flow

```
Token Engine Crew  ──writes──► tokens/*.tokens.json   ──reads──► Agent 32 (Token Compliance)
                   ──writes──► specs/*.spec.yaml       ──reads──► Agent 31, 33 (Usage, Drift)

Design-to-Code Crew ─writes──► src/**/*.tsx            ──reads──► Agent 31, 32 (Usage, Compliance)

Component Factory  ──writes──► dependency_graph.json   ──reads──► Agent 35 (Breakage Correlation)

Documentation Crew ──writes──► docs/components/*.md    ──reads──► Agent 33 (Drift Detection)
                   ──writes──► docs/component-index.json ─reads──► Agent 34 (Pipeline Completeness)

Release Crew       ──writes──► reports/test-results.json ─reads──► Agent 35 (Breakage Correlation)

Analytics Crew     ──writes──► reports/usage-tracking.json
                   ──writes──► reports/token-compliance.json     (replaces stub placeholder)
                   ──writes──► reports/drift-report.json         (replaces stub placeholder)
                   ──writes──► reports/pipeline-completeness.json
                   ──writes──► reports/breakage-correlation.json
```

## Retry & Failure Behavior

Per PRD §3.4, Phases 4–6 use crew-level retry (max 2 attempts), not per-agent retry. If the Analytics Crew fails catastrophically on the first attempt, `First Publish Agent (6)` retries the entire crew once. If the second attempt also fails, the crew is marked `failed` in `reports/generation-summary.json` and the pipeline continues.

Analytics failures are **non-fatal** (Warning-level exit criteria only). A missing or partial `reports/` directory does not block the Output Review gate or prevent the Release Crew from running.

Within a single crew run, tasks are sequential (`T1→T2→T3→T4→T5`). If `T2` (token compliance) raises an exception, the crew raises and triggers the crew-level retry. Tasks do not individually retry.

## File Changes

- `src/daf/crews/analytics.py` (modified) — Replace `StubCrew` with real `crewai.Crew`; add pre-flight guard; wire T1–T5
- `src/daf/agents/usage_tracking.py` (new) — Agent 31 factory
- `src/daf/agents/token_compliance_agent.py` (new) — Agent 32 factory
- `src/daf/agents/drift_detection.py` (new) — Agent 33 factory
- `src/daf/agents/pipeline_completeness.py` (new) — Agent 34 factory
- `src/daf/agents/breakage_correlation.py` (new) — Agent 35 factory
- `src/daf/tools/ast_import_scanner.py` (new) — AST-based import relationship scanner for Agent 31
- `src/daf/tools/token_usage_mapper.py` (new) — Token key usage extractor across TSX files for Agent 31
- `src/daf/tools/structural_comparator.py` (new) — YAML spec vs. TSX props vs. Markdown props diff for Agent 33
- `src/daf/tools/drift_reporter.py` (new) — Categorises drift items as auto-fixable or report-only; delegates patches to doc patcher
- `src/daf/tools/doc_patcher.py` (new) — Applies deterministic string patches to Markdown docs
- `src/daf/tools/pipeline_stage_tracker.py` (new) — Presence-checks output files per component to determine pipeline stage
- `src/daf/tools/dependency_chain_walker.py` (new) — Graph traversal over `dependency_graph.json` for failure correlation
- `src/daf/agents/__init__.py` (modified) — Export five new agent factories
- `src/daf/tools/__init__.py` (modified) — Export seven new tool classes
- `tests/test_usage_tracking_agent.py` (new) — Unit tests for Agent 31
- `tests/test_token_compliance_agent.py` (new) — Unit tests for Agent 32
- `tests/test_drift_detection_agent.py` (new) — Unit tests for Agent 33
- `tests/test_pipeline_completeness_agent.py` (new) — Unit tests for Agent 34
- `tests/test_breakage_correlation_agent.py` (new) — Unit tests for Agent 35
- `tests/test_analytics_crew.py` (modified) — Replace stub assertions with real crew tests
- `tests/test_ast_import_scanner.py` (new) — Unit tests for AST import scanner tool
- `tests/test_token_usage_mapper.py` (new) — Unit tests for token usage mapper tool
- `tests/test_structural_comparator.py` (new) — Unit tests for structural comparator tool
- `tests/test_drift_reporter.py` (new) — Unit tests for drift reporter tool
- `tests/test_pipeline_stage_tracker.py` (new) — Unit tests for pipeline stage tracker tool
- `tests/test_dependency_chain_walker.py` (new) — Unit tests for dependency chain walker tool
