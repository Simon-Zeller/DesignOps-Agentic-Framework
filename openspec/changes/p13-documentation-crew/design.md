# Design: p13-documentation-crew

## Technical Approach

The Documentation Crew is implemented as a sequential four-stage pipeline matching the existing pattern of Agent 17–20 in the Component Factory Crew. Five agents (21–25) each invoke deterministic tools, then optionally call `_call_llm()` for prose generation or contextual narration. The crew factory wires them into a single `.kickoff()` call.

The crew reads from the shared output folder produced by Phases 1–3 (specs, compiled tokens, generated components, generation summary) and writes exclusively into the `docs/` subtree. No Phase 1–3 artifacts are modified.

Fourteen new deterministic tools back the five agents. Tools are pure functions with no LLM dependency, making them fully unit-testable in isolation. Agents orchestrate tool outputs, apply LLM reasoning for prose quality, and write final Markdown or JSON files.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Parse `*.spec.yaml` → prop table rows | Deterministic | Pure data extraction — no ambiguity |
| Render prop table as Markdown | Deterministic | Template fill — rule-based |
| Generate usage code examples | Agent (LLM) | Requires context-aware, readable code snippets |
| Resolve token value from compiled JSON | Deterministic | Flat key lookup |
| Classify token tier (global/semantic/component) | Deterministic | Key-prefix heuristic (`global.*`, `semantic.*`) |
| Generate scale visualization (color swatches, type scale) | Deterministic | Value formatting — no reasoning needed |
| Describe token usage context | Agent (LLM) | Requires natural language description of purpose |
| Read decision log JSON and extract fields | Deterministic | Structured data extraction |
| Analyze Brand Profile for archetype/a11y choices | Deterministic | Rule-based field reading |
| Write generation narrative prose | Agent (LLM) | Requires coherent, opinionated prose |
| Generate ADR from decision record | Deterministic (template) | Fill standard ADR sections |
| Build search index entries from Markdown | Deterministic | Text chunking + metadata tagging |
| Tag index entries with category/status | Deterministic | Metadata schema is fixed |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 21 — Doc Generation Agent | Tier 3 Haiku | claude-3-haiku | Usage examples and prose are low-stakes, high-volume — fast and cheap |
| Agent 22 — Token Catalog Agent | Tier 3 Haiku | claude-3-haiku | Catalog entries are structured; LLM only adds usage-context descriptions |
| Agent 23 — Generation Narrative Agent | Tier 2 Sonnet | claude-3-5-sonnet | Narrative prose must be coherent and context-rich; quality matters here |
| Agent 24 — Decision Record Agent | Tier 3 Haiku | claude-3-haiku | ADRs follow a fixed template; LLM fills in consequences only |
| Agent 25 — Search Index Agent | Deterministic | — | Entirely rule-based: Markdown chunking + JSON serialization |

## Architecture Decisions

### Decision: Documentation as derived artifact, never separately authored

**Context:** Design systems often maintain docs in parallel with code, creating drift risk. The PRD §4.5 explicitly specifies "documentation is a derived artifact — never separately authored."

**Decision:** All five agents read from existing pipeline artifacts (specs, tokens, generated files, brand-profile.json) and write to the `docs/` subtree. No new inputs are introduced. The agents transform existing structured data into human-readable form.

**Consequences:** Docs can always be regenerated from scratch with `--from-phase 4`. Docs are guaranteed to be in sync with the actual generated output. If the spec changes, re-running Phase 4a regenerates matching docs.

---

### Decision: 14 tools split by output format, not by agent

**Context:** Several agents need overlapping capabilities (spec parsing, file I/O). Tools should be granular and reusable.

**Decision:** Tools are organized by their output domain: doc rendering (4 tools), token catalog (3 tools), narrative/ADR (5 tools), search (2 tools). Agents compose tools freely — Agent 21 may call `prop_table_generator` and `example_code_generator` sequentially; Agent 22 calls `token_value_resolver` and `scale_visualizer`.

**Consequences:** Tools are individually unit-testable. New agents in future changes can reuse these tools without modification. The tool-to-agent mapping is M:N, not 1:1.

---

### Decision: Search index is fully deterministic (no LLM)

**Context:** Agent 25 in the PRD is labeled "Search Index Agent" with goal to build a full-text index. This could be done with LLM-extracted summaries or with deterministic text chunking.

**Decision:** Agent 25 uses only deterministic tools: `search_index_builder` chunks Markdown into entries (heading + paragraph blocks), `metadata_tagger` adds category/status metadata. No LLM involved. The agent function iterates over all docs files and delegates to tools.

**Consequences:** Agent 25 is fast, predictable, and requires no mock in tests. Search quality depends on Markdown structure quality, which is established by Agents 21–24 upstream.

---

### Decision: `_call_llm()` patchable at module level, same pattern as agents 17–20

**Context:** All agents in the Component Factory Crew expose a module-level `def _call_llm(prompt: str) -> str` that tests patch with `unittest.mock.patch("daf.agents.X._call_llm")`.

**Decision:** Agents 21–24 follow the identical pattern. Agent 25 has no `_call_llm()` since it is fully deterministic.

**Consequences:** All agent tests are consistent with existing patterns. No new test infrastructure needed.

## Data Flow

```
[Token Engine Crew]
  ──writes──► tokens/global.tokens.json
              tokens/semantic.tokens.json
              tokens/component-scoped/*.tokens.json
              tokens/diff.json (optional)

[Design-to-Code + Component Factory]
  ──writes──► specs/*.spec.yaml
              src/components/*.tsx
              reports/generation-summary.json

[DS Bootstrap]
  ──writes──► brand-profile.json

[Documentation Crew — Phase 4a]
  Agent 21 ──reads──► specs/*.spec.yaml, src/components/*.tsx
             ──writes──► docs/components/<Name>.md (per component)
                         docs/README.md

  Agent 22 ──reads──► tokens/*.tokens.json, tokens/diff.json (optional)
             ──writes──► docs/tokens/catalog.md

  Agent 23 ──reads──► brand-profile.json, reports/generation-summary.json
             ──writes──► docs/decisions/generation-narrative.md

  Agent 24 ──reads──► reports/generation-summary.json
             ──writes──► docs/decisions/adr-<slug>.md (one per decision)

  Agent 25 ──reads──► docs/**/*.md (all docs written by agents 21–24)
             ──writes──► docs/search-index.json

[Governance Crew — Phase 4b]
  Agent 30 ──reads──► docs/components/*.md
                      (verifies doc completeness gate)
```

## Retry & Failure Behavior

Per PRD §3.4, Phases 4–6 use crew-level retry (up to 2 attempts), not agent-level retry. This means:
- If any agent in the Documentation Crew raises an unhandled exception, the entire crew is retried from Agent 21.
- If the second attempt also fails, the crew is marked `failed` in `reports/generation-summary.json`.
- Phase 4–6 failures are **non-fatal**: the pipeline continues to Governance, Analytics, and Release. Missing docs degrade the Quality Gate Agent (30)'s doc-completeness check but do not block the output review gate.

Within the crew's sequential flow, each agent fails fast on missing required inputs (e.g., no `specs/` directory) and writes a partial result rather than aborting silently. Agent 25 runs last; it indexes whatever docs exist, so partial doc coverage yields a partial search index rather than a crash.

## File Changes

**New tool files:**
- `src/daf/tools/spec_to_doc_renderer.py` (new) — parses spec YAML, returns structured doc sections
- `src/daf/tools/prop_table_generator.py` (new) — renders a Markdown prop table from spec props dict
- `src/daf/tools/example_code_generator.py` (new) — generates TSX usage example stubs from spec metadata
- `src/daf/tools/readme_template.py` (new) — fills README template with component list, install instructions
- `src/daf/tools/token_value_resolver.py` (new) — resolves token key to value+tier from compiled token files
- `src/daf/tools/scale_visualizer.py` (new) — formats color/spacing/type scale entries as Markdown visuals
- `src/daf/tools/usage_context_extractor.py` (new) — extracts token usage context from spec references
- `src/daf/tools/decision_log_reader.py` (new) — reads and normalizes `reports/generation-summary.json`
- `src/daf/tools/brand_profile_analyzer.py` (new) — extracts archetype, a11y tier, and key decisions from brand-profile.json
- `src/daf/tools/prose_generator.py` (new) — assembles narrative sections from structured decision data
- `src/daf/tools/decision_extractor.py` (new) — extracts decision record list from generation summary
- `src/daf/tools/adr_template_generator.py` (new) — fills ADR Markdown template for a single decision
- `src/daf/tools/search_index_builder.py` (new) — chunks Markdown files into searchable index entries
- `src/daf/tools/metadata_tagger.py` (new) — tags index entries with category, component name, token name, status

**New agent files:**
- `src/daf/agents/doc_generation.py` (new) — Agent 21
- `src/daf/agents/token_catalog.py` (new) — Agent 22
- `src/daf/agents/generation_narrative.py` (new) — Agent 23
- `src/daf/agents/decision_record.py` (new) — Agent 24
- `src/daf/agents/search_index.py` (new) — Agent 25

**New crew file:**
- `src/daf/crews/documentation.py` (new) — `create_documentation_crew(output_dir: str) -> StubCrew`

**Modified files:**
- `src/daf/tools/__init__.py` (modified) — export 14 new tools
- `src/daf/agents/__init__.py` (modified) — export 5 new agent functions

**New test files (14 tool tests + 5 agent tests + 1 integration test = 20):**
- `tests/test_spec_to_doc_renderer.py`
- `tests/test_prop_table_generator.py`
- `tests/test_example_code_generator.py`
- `tests/test_readme_template.py`
- `tests/test_token_value_resolver.py`
- `tests/test_scale_visualizer.py`
- `tests/test_usage_context_extractor.py`
- `tests/test_decision_log_reader.py`
- `tests/test_brand_profile_analyzer.py`
- `tests/test_prose_generator.py`
- `tests/test_decision_extractor.py`
- `tests/test_adr_template_generator.py`
- `tests/test_search_index_builder.py`
- `tests/test_metadata_tagger.py`
- `tests/test_doc_generation_agent.py`
- `tests/test_token_catalog_agent.py`
- `tests/test_generation_narrative_agent.py`
- `tests/test_decision_record_agent.py`
- `tests/test_search_index_agent.py`
- `tests/test_documentation_crew.py`

**New test fixtures:**
- `tests/fixtures/specs/button.spec.yaml` (add props/variants fields needed by Agent 21)
- `tests/fixtures/tokens/compiled.json` (flat token map for resolver tests)
- `tests/fixtures/generation-summary.json` (sample generation metadata for narrative/ADR tests)
