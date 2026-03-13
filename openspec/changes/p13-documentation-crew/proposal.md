# Proposal: p13-documentation-crew

## Intent

The DAF pipeline generates components, tokens, and quality reports through Phases 1–3, but currently stops short of producing any human-readable documentation. The Documentation Crew (Phase 4a) is the next sequential milestone: it transforms the validated code and token artifacts into a complete documentation layer — component API docs, a token catalog, a generation narrative, Architecture Decision Records, and a full-text search index.

Without this crew the pipeline's output cannot be understood, adopted, or governed. The Governance Crew (Phase 4b) is explicitly blocked on Documentation Crew output because Agent 30's quality gate checks "all components have docs." This proposal specifies the implementation of all five Documentation Crew agents (21–25) and their 14 supporting tools.

## Scope

### In scope

- **Agent 21 — Doc Generation Agent**: generates per-component Markdown docs (prop table, variant showcase, 2+ usage examples, token binding reference) and the project `docs/README.md` (install instructions, quick start, component list, token overview).
- **Agent 22 — Token Catalog Agent**: generates `docs/tokens/catalog.md` — every token with resolved value, tier (global/semantic/component), usage context description, and visual representation (color swatches, type scale, spacing scale), organized by category.
- **Agent 23 — Generation Narrative Agent**: writes `docs/decisions/generation-narrative.md` — a human-readable "why" document: archetype selection rationale, Brand Profile token decision mapping, modular scale reasoning, accessibility tier implications.
- **Agent 24 — Decision Record Agent**: generates one ADR per significant generation decision (archetype selection, token scale algorithm, composition model, accessibility tier). Each ADR follows the standard Context → Decision → Consequences format.
- **Agent 25 — Search Index Agent**: builds `docs/search-index.json` — a full-text searchable index across all docs, tokens, components, and ADRs, tagged by category and status.
- **14 deterministic tools** that back the five agents, covering spec parsing, prop table rendering, example code generation, token resolution, scale visualization, decision extraction, ADR templating, and search index construction.
- **Crew factory** (`create_documentation_crew`): wires agents 21–25 into a sequential pipeline and exposes `.kickoff()`.
- Full TDD test suite: 14 tool tests + 5 agent tests + 1 integration test.

### Out of scope

- `docs/changelog.md` — owned by Release Agent 44 (Phase 6), not this crew.
- `docs/templates/` — RFC templates written by Governance Agent 29 (Phase 4b).
- Visual screenshot rendering — that is Playwright's domain in Phase 3 (Render Validation Crew).
- Storybook story generation — already handled by Agent 14 (Design-to-Code Crew).
- Any post-generation re-run or incremental documentation updates.

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| Documentation Crew (new) | Agents 21–25 | Created from scratch — 5 agents, 14 tools, crew factory |
| DS Bootstrap Crew | Agent 6 (First Publish Agent) | Phase 4–6 retry orchestrator — will call `create_documentation_crew` in its loop |
| Governance Crew | Agent 30 (Quality Gate Agent) | Reads `docs/components/*.md` to verify doc completeness; unblocked by this change |
| Analytics Crew | Agent 33 (Drift Detection Agent) | Reads `docs/components/*.md` for doc completeness drift in Phase 5 |

## PRD References

- §3.1 — Pipeline phase ordering (Phase 4a precedes Phase 4b)
- §3.4 — Phase 4–6 retry protocol (crew-level retry up to 2 attempts, non-fatal)
- §3.6 — Crew I/O contracts: Documentation Crew inputs and outputs
- §4.5 — Documentation Crew specification (Agents 21–25, tools, tasks, NFRs)
- §3.7 — Output folder structure (`docs/`)
- §4.6 — Governance Crew (depends on Documentation Crew output for Agent 30)
- §6 — Brand Profile schema (read by Agent 23 for narrative generation)

## Pipeline Impact

- [x] Crew I/O contracts (§3.6) — this crew introduces the `docs/` output subtree consumed by Agents 30 and 33
- [ ] Pipeline phase ordering — phase order unchanged; this fills the existing Phase 4a slot
- [ ] Retry protocol (§3.4) — retry logic already specified for Phase 4–6; no changes needed
- [ ] Human gate policy (§5) — no changes
- [ ] Exit criteria (§8) — no new Fatal checks; "all components have docs" is enforced by Agent 30 (Governance, Phase 4b)
- [ ] Brand Profile schema (§6) — no schema changes; Brand Profile is read-only input for Agent 23

## Approach

Follow the same TDD-first pattern established by the Component Factory Crew (p12):

1. **Red phase**: Write failing tests for all 14 tools and 5 agents before any implementation.
2. **Green phase**: Implement tools one by one until all tests pass, then implement agents, then the crew factory.
3. **Refactor**: Extract shared utilities (spec parsing, file I/O helpers), update `__init__.py` exports.
4. **Lint/type**: `ruff` + `pyright` on all new files.
5. **Push & merge**: feature branch → main with conventional commits.

All agents use the `_call_llm()` / module-level patchable pattern for LLM calls (same as agents 17–20). Deterministic tool functions are fully testable without LLM mocks.

The 14 tools divide into four groups by responsibility:
- **Doc rendering** (Agents 21): `spec_to_doc_renderer`, `prop_table_generator`, `example_code_generator`, `readme_template`
- **Token catalog** (Agent 22): `token_value_resolver`, `scale_visualizer`, `usage_context_extractor`
- **Narrative & ADR** (Agents 23–24): `decision_log_reader`, `brand_profile_analyzer`, `prose_generator`, `decision_extractor`, `adr_template_generator`
- **Search** (Agent 25): `search_index_builder`, `metadata_tagger`

## Risks

- **LLM prose quality**: Agents 23 (narrative) and 21 (usage examples) rely on LLM for coherent prose. Tests mock `_call_llm()`; actual output quality is out of scope for unit tests.
- **Spec completeness dependency**: Agent 21's prop table depth depends on how completely specs were filled in during Phase 1–2. Partial specs produce partial docs — this is by design (documented in quality gate as "doc completeness" check).
- **Token catalog scale**: Comprehensive tier generates 200+ tokens. `search_index_builder` must handle large payloads without exceeding memory limits — keep index entries flat and minimal.
- **ADR duplication risk**: Agent 24 generates ADRs from generation metadata. If no generation-summary.json exists (skeleton run), the decision extractor must gracefully produce empty ADR shells rather than failing.
