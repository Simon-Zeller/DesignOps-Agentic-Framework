# Proposal: p15-analytics-crew

## Intent

The Analytics Crew (`src/daf/crews/analytics.py`) is currently a stub that writes placeholder JSON files and performs no real analysis. This means the pipeline produces no actionable quality intelligence: token compliance violations go undetected, spec/code/docs drift is never surfaced, and test failures cannot be correlated to root causes.

This change replaces the stub with a fully implemented five-agent Analytics Crew (Agents 31–35), bringing the DAF pipeline's Phase 5 analytical capability to parity with the already-implemented Documentation and Governance crews. With this change, every generated design system will be accompanied by comprehensive quality reports — token compliance audits, drift analysis, pipeline completeness tracking, and failure correlation — giving consumers a clear picture of output health before adoption.

## Scope

### In scope

- Implement **Agent 31 – Usage Tracking Agent**: scan all generated TSX source for actual token usage vs. defined-but-unused tokens, primitive dependency relationships, and cross-component import graphs. Write `reports/usage-tracking.json`.
- Implement **Agent 32 – Token Compliance Agent**: static analysis of all generated source for hardcoded colour/spacing/font-size values and deprecated token references; report each violation with file, line, and suggested replacement. Write `reports/token-compliance.json` (replacing the stub placeholder).
- Implement **Agent 33 – Drift Detection Agent**: compare canonical spec (YAML) against generated TSX and generated Markdown docs; flag inconsistencies; auto-patch docs where spec is authoritative; emit non-fixable mismatches in `reports/drift-report.json` (replacing the stub placeholder).
- Implement **Agent 34 – Pipeline Completeness Agent**: track each component's stage completeness (spec → code → a11y → tests → docs); report stuck components with recommended interventions. Write `reports/pipeline-completeness.json`.
- Implement **Agent 35 – Breakage Correlation Agent**: analyse all test failures from exhausted-retry records and the Release Crew's `npm test`; build the dependency chain and classify each failure as `root-cause` or `downstream`. Write `reports/breakage-correlation.json`.
- Replace the `StubCrew` factory in `analytics.py` with a real `crewai.Crew` housing all five agents, tasks T1–T5 in sequence.
- Add deterministic helper tools where needed (AST import scanner, token usage mapper, structural comparator, drift reporter, pipeline stage tracker, dependency chain walker).
- Full unit-test coverage for each agent and the crew module, following TDD (tests written first, red→green).
- Update `reports/generation-summary.json` contributions to include analytics crew status.

### Out of scope

- Changes to any other crew (Documentation, Governance, Release, etc.)
- Changes to the pipeline orchestration order (Analytics already runs in Phase 5 alongside AI Semantic Layer per §3.2)
- New exit criteria checks (analytics outputs are non-fatal per §3.4)
- UI / CLI changes for surfacing reports (future concern)
- Re-running the Design-to-Code Crew based on drift findings (flagged but not actioned in this change)

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| Analytics Crew | Agent 31 – Usage Tracking Agent | New implementation |
| Analytics Crew | Agent 32 – Token Compliance Agent | New implementation |
| Analytics Crew | Agent 33 – Drift Detection Agent | New implementation |
| Analytics Crew | Agent 34 – Pipeline Completeness Agent | New implementation |
| Analytics Crew | Agent 35 – Breakage Correlation Agent | New implementation |
| Release Crew | Agent 39 – Publish Agent | Reads `reports/` — output shape must remain compatible |
| DS Bootstrap Crew | Agent 6 – First Publish Agent | Invokes `create_analytics_crew`; no signature change required |

## PRD References

- §3.2 — Pipeline phase ordering (Phase 5: AI Semantic Layer + Analytics, no mutual dependency)
- §3.4 — Retry protocol for Phases 4–6 (crew-level retry, max 2 attempts; Phase 5 failures are non-fatal)
- §4.7 — Analytics Crew specification (Agents 31–35, Tasks T1–T5)
- §3.6 — Crew I/O contracts: Analytics reads `specs/*.spec.yaml`, `src/**/*.tsx`, `docs/components/*.md`, `tokens/*.tokens.json`; writes `reports/token-compliance.json`, `reports/drift-report.json`
- §8 — Exit criteria (Analytics outputs are Warning-level, not Fatal)

## Pipeline Impact

- [ ] Pipeline phase ordering
- [ ] Crew I/O contracts (§3.6)
- [ ] Retry protocol (§3.4)
- [ ] Human gate policy (§5)
- [ ] Exit criteria (§8)
- [x] Brand Profile schema (§6) ← not affected, but see note below

> **I/O note:** The crew I/O contract (§3.6) is satisfied without change — input paths (`specs/`, `src/`, `docs/`, `tokens/`) are already produced by earlier phases; output paths (`reports/token-compliance.json`, `reports/drift-report.json`) are widened with three new report files. This is additive and backwards-compatible with Release Crew consumers.

## Approach

1. **Write tests first** for all five agents and the crew factory (TDD red phase).
2. **Implement helper tools** needed by the agents that do not already exist in `src/daf/tools/` — e.g. `ast_import_scanner.py`, `token_usage_mapper.py`, `structural_comparator.py`, `drift_reporter.py`, `pipeline_stage_tracker.py`, `dependency_chain_walker.py`.
3. **Implement agent factories** in `src/daf/agents/` — `usage_tracking.py`, `token_compliance_agent.py`, `drift_detection.py`, `pipeline_completeness.py`, `breakage_correlation.py` — each following the existing pattern of `create_<agent>_agent(model, output_dir)`.
4. **Rewrite `src/daf/crews/analytics.py`** replacing the `StubCrew` with a real `crewai.Crew`, wiring T1→T2→T3→T4→T5 in sequential order, with a pre-flight guard that checks for required input files.
5. **Run tests green**, ensure no regressions in existing test suite.
6. **Commit** with conventional commit message `feat(analytics): implement Analytics Crew agents 31-35`.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| LLM-based agents produce non-deterministic output in tests | Medium | Stub LLM calls in unit tests; use deterministic tool outputs for assertions |
| AST scanning of generated TSX may fail on complex component shapes | Low | Implement fallback to regex-based scanning; add integration test with real TSX fixture |
| Drift auto-patching modifies docs unexpectedly during tests | Low | Tests run against isolated temp directories; doc patching is scoped to `output_dir` |
| Token compliance tool duplicates logic already in `composition_rule_engine.py` | Medium | Reuse `compute_token_compliance` from `daf.tools.composition_rule_engine` rather than reimplementing |
