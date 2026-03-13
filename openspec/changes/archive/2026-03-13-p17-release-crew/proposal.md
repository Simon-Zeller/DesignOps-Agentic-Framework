# Proposal: p17-release-crew

## Intent

The Release Crew (`src/daf/crews/release.py`) is currently a stub that writes a
placeholder `package.json`, an empty `docs/changelog.md`, and a `final_status: "stub"` marker in `reports/generation-summary.json`. This leaves the last phase of the DAF pipeline — package assembly, versioning, changelog authorship, adoption codemod generation, and final validation — entirely unimplemented.

Without a real Release Crew, the pipeline technically "completes" but produces an uninstallable package, no changelog, no adoption guidance, and a misleading `final_status` that masks any downstream failures. The output review gate (Human Gate 2) has no meaningful summary to present, and consumers of the generated design system receive no migration tooling.

This change replaces the stub with a fully implemented five-agent Release Crew (Agents 36–40), completing Phase 6 of the DAF pipeline. After this change, every generated design system will have a valid semantic version, a structured inventory changelog, example adoption codemods, a properly assembled and locally installable npm package, and a checkpoint/rollback system that guards all pipeline phases against catastrophic failure.

## Scope

### In scope

- Implement **Agent 36 – Semver Agent**: read quality gate results from `reports/governance/quality-gates.json`; apply conventional version semantics — `v1.0.0` when all Fatal gates pass, `v0.x.0` when experimental or incomplete; write the chosen version to `reports/generation-summary.json`.
- Implement **Agent 37 – Release Changelog Agent**: read component inventory and quality gate results; write `docs/changelog.md` as structured prose grouped by category — full component inventory with status and quality score, token category summary, gate pass/fail summary, and known issues with failed components.
- Implement **Agent 38 – Codemod Agent**: generate example adoption codemod scripts in `docs/codemods/` that demonstrate how consumers migrate from ad-hoc UI code to design system equivalents (raw `<button>` → `<Button>`, hardcoded `color: #333` → semantic token variable). Scripts are adoption templates, not version-to-version migration codemods.
- Implement **Agent 39 – Publish Agent**: assemble the final `package.json` with correct dependencies, peer dependencies, entry points, TypeScript config, and export maps; then execute `npm install`, `tsc --noEmit`, and `npm test` in sequence; parse all results into `reports/generation-summary.json` with the definitive `final_status` (`success` | `partial` | `failed`).
- Implement **Agent 40 – Rollback Agent**: maintain checkpoints at each pipeline phase boundary; snapshot the output folder before each crew run; restore to the last known-good checkpoint when a crew fails catastrophically; report what was rolled back and why. Note: Agent 40 is instantiated by the First Publish Agent (6) at pipeline start, not as part of the Release Crew's task sequence.
- Replace the `StubCrew` factory in `release.py` with a real `crewai.Crew` wiring tasks T1–T6 in sequential order (T1: calculate version → T2: generate changelog → T3: generate codemods → T4: assemble package → T5: run `npm install && tsc --noEmit && npm test` → T6: validate final status).
- Add deterministic helper tools where needed: `gate_status_reader.py`, `version_calculator.py`, `component_inventory_reader.py`, `quality_report_parser.py`, `ast_pattern_matcher.py`, `codemod_template_generator.py`, `example_suite_builder.py`, `package_json_generator.py`, `dependency_resolver.py`, `test_result_parser.py`, `checkpoint_creator.py`, `restore_executor.py`, `rollback_reporter.py`.
- Rewrite `src/daf/agents/rollback.py` and complete `src/daf/agents/first_publish.py` to use the real tool implementations.
- Full unit-test coverage for each agent and the crew factory, following TDD (tests written first, red→green cycle).

### Out of scope

- Changes to any other crew (Analytics, AI Semantic Layer, Governance, etc.)
- Publishing to a remote npm registry (local package assembly only)
- Automatic changelog generation from git history (changelog is derived from pipeline reports, not commits)
- Version-to-version migration codemods (adoption codemods only, per §4.8)
- Changes to Human Gate 2 review flow — the Release Crew populates data _for_ review but does not alter the gate policy

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| Release Crew | Agent 36 – Semver Agent | New implementation |
| Release Crew | Agent 37 – Release Changelog Agent | New implementation |
| Release Crew | Agent 38 – Codemod Agent | New implementation |
| Release Crew | Agent 39 – Publish Agent | New implementation |
| Release Crew | Agent 40 – Rollback Agent | New implementation (cross-cutting; instantiated by Agent 6) |
| DS Bootstrap Crew | Agent 6 – First Publish Agent | Instantiates Agent 40 at pipeline start; invokes `create_release_crew`; no signature change required |

## PRD References

- §3.2 — Pipeline phase ordering (Phase 6: Release, runs after Analytics and AI Semantic Layer)
- §3.4 — Retry protocol for Phases 4–6 (crew-level retry, max 2 attempts; Phase 6 failures are non-fatal to core design system)
- §3.6 — Crew I/O contracts: Release Crew reads entire output folder; writes `package.json`, `src/index.ts`, `docs/changelog.md`, barrel `index.ts` files, and updates `reports/generation-summary.json` with final test results
- §4.8 — Release Crew specification (Agents 36–40, Tasks T1–T6)
- §5 — Human Gate 2: Output Review gate depends on `reports/generation-summary.json` final_status
- §8 — Exit criteria: 8 Fatal checks (token validity, DTCG schema, reference resolution, WCAG contrast, CSS references, TypeScript compilation, npm build) + 7 Warning checks

## Pipeline Impact

- [ ] Pipeline phase ordering
- [x] Crew I/O contracts (§3.6) — outputs change from stub placeholders to fully populated files; additive and backwards-compatible with Human Gate 2
- [ ] Retry protocol (§3.4)
- [ ] Human gate policy (§5)
- [x] Exit criteria (§8) — Publish Agent (Agent 39) executes the `npm build` and TypeScript compilation Fatal checks
- [ ] Brand Profile schema (§6)

> **I/O note:** The Release Crew I/O contract (§3.6) is satisfied without change — input paths (entire output folder, including `reports/governance/quality-gates.json`, `specs/`, `src/`, `tokens/`) are all produced by earlier phases. Output paths (`package.json`, `docs/changelog.md`, `reports/generation-summary.json`) are already listed in §3.6 and currently written as stubs. This change populates them with real content. New output `docs/codemods/` is additive and does not affect any other crew.

## Approach

1. **Write tests first** for all five agents and the crew factory (TDD red phase).
2. **Implement helper tools** in `src/daf/tools/` — `gate_status_reader.py`, `version_calculator.py`, `component_inventory_reader.py`, `quality_report_parser.py`, `ast_pattern_matcher.py`, `codemod_template_generator.py`, `example_suite_builder.py`, `package_json_generator.py`, `dependency_resolver.py`, `test_result_parser.py`, `checkpoint_creator.py`, `restore_executor.py`, `rollback_reporter.py`.
3. **Implement agent factories** in `src/daf/agents/` — `semver.py`, `release_changelog.py`, `codemod.py`, `publish.py`; rewrite existing `rollback.py` and `first_publish.py` to use real tools — each following the `create_<agent>_agent(model, output_dir)` pattern.
4. **Rewrite `src/daf/crews/release.py`** replacing the `StubCrew` with a real `crewai.Crew`, wiring T1→T2→T3→T4→T5→T6, with a pre-flight guard that checks for required input files (`reports/governance/quality-gates.json`, `src/components/`).
5. **Run tests green**, ensure no regressions in existing test suite.
6. **Commit** with conventional commit message `feat(release): implement Release Crew agents 36-40`.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `npm install` / `npm test` execution in Agent 39 requires a real Node environment in CI | Medium | Wrap npm CLI calls in a thin tool that gracefully degrades (reports `npm_unavailable`) when Node is not present; tests mock the CLI calls |
| `reports/governance/quality-gates.json` may be absent if Governance Crew failed | Medium | Semver Agent falls back to `v0.1.0-experimental` when gate report is missing and logs the fallback reason |
| Rollback Agent snapshot/restore on large output folders may be slow | Low | Checkpoint Creator uses a delta-copy strategy (hardlinks where possible) rather than a full copy |
| Agent 38 codemod AST transforms are brittle against non-standard input patterns | Medium | Codemod scripts are _examples_, not executable transforms; AST Pattern Matcher generates line-commented pseudo-transforms that are human-readable, not runnable |
| LLM-based agents (37, 38) produce non-deterministic output in tests | Medium | Stub LLM calls in unit tests; assert JSON/Markdown structural validity, not exact content |
| Agent 40 (Rollback) is cross-cutting — incorrect wiring to Agent 6 could break all phases | Low | Rollback Agent interface is a narrow protocol (snapshot/restore/report); integration tested via First Publish Agent test suite |
