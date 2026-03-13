# Proposal: p16-ai-semantic-layer-crew

## Intent

The AI Semantic Layer Crew (`src/daf/crews/ai_semantic_layer.py`) is currently a stub that writes placeholder JSON files and produces no real machine-readable knowledge. This means that after a full pipeline run, AI coding assistants (Cursor, GitHub Copilot, Claude) receive zero useful context about the generated design system: they cannot resolve token intent, cannot validate component composition, and cannot enforce design-system rules in generated code.

This change replaces the stub with a fully implemented five-agent AI Semantic Layer Crew (Agents 41–45), completing Phase 5 of the DAF pipeline. With this change, every generated design system will ship a rich, AI-consumable knowledge base — a component registry, a token resolution graph, composition rules, compliance rules, and format-specific context files — allowing any LLM-based tool to generate on-brand, constraint-valid code against the design system without manual documentation.

## Scope

### In scope

- Implement **Agent 41 – Registry Maintenance Agent**: read all canonical spec YAMLs and generated TSX source; build `registry/components.json` with full prop metadata (types, defaults, variants, states, slots, token bindings, a11y attributes, usage examples).
- Implement **Agent 42 – Token Resolution Agent**: traverse the compiled token graph; build `registry/tokens.json` with resolved value per platform, tier, semantic purpose, related tokens, and natural-language description. Enable intent-to-token resolution (e.g. "muted background" → correct semantic token).
- Implement **Agent 43 – Composition Constraint Agent**: read composition rules and generated component trees; build `registry/composition-rules.json` with allowed children, forbidden nesting, required slots, maximum depth, and example valid/invalid trees.
- Implement **Agent 44 – Validation Rule Agent**: compile all compliance rules from token, composition, a11y, and naming checks into `registry/compliance-rules.json` in an exportable, linter-consumable format.
- Implement **Agent 45 – Context Serializer Agent**: read all four registry files; package them into `.cursorrules` (for Cursor), `copilot-instructions.md` (for GitHub Copilot), and `ai-context.json` (unified LLM context). Apply token budget optimisation to keep context files within LLM context window limits.
- Replace the `StubCrew` factory in `ai_semantic_layer.py` with a real `crewai.Crew` housing all five agents and tasks T1–T5 in dependency order.
- Add deterministic helper tools where needed (spec indexer, example generator, registry builder, token graph traverser, semantic mapper, composition rule extractor, tree validator, rule compiler, context formatter, token budget optimizer, multi-format serializer).
- Full unit-test coverage for each agent and the crew factory, following TDD (tests written first, red→green).

### Out of scope

- Changes to any other crew (Analytics, Documentation, Governance, Release, etc.)
- Changes to the pipeline orchestration order (AI Semantic Layer already runs in Phase 5 alongside Analytics per §3.2)
- Dynamic/runtime context updating after initial generation
- Serving the registry over an HTTP API or live MCP server (static files only)
- IDE plugin integration or extension development

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| AI Semantic Layer Crew | Agent 41 – Registry Maintenance Agent | New implementation |
| AI Semantic Layer Crew | Agent 42 – Token Resolution Agent | New implementation |
| AI Semantic Layer Crew | Agent 43 – Composition Constraint Agent | New implementation |
| AI Semantic Layer Crew | Agent 44 – Validation Rule Agent | New implementation |
| AI Semantic Layer Crew | Agent 45 – Context Serializer Agent | New implementation |
| DS Bootstrap Crew | Agent 6 – First Publish Agent | Invokes `create_ai_semantic_layer_crew`; no signature change required |
| Release Crew | Agent 37 – Publish Agent | Reads output folder — registry files and AI context files must be present at completion |

## PRD References

- §3.2 — Pipeline phase ordering (Phase 5: AI Semantic Layer + Analytics, no mutual dependency; may run in either order)
- §3.4 — Retry protocol for Phases 4–6 (crew-level retry, max 2 attempts; Phase 5 failures are non-fatal)
- §3.6 — Crew I/O contracts: AI Semantic Layer reads `specs/*.spec.yaml`, `src/primitives/*.tsx`, `src/components/**/*.tsx`, `tokens/*.tokens.json`, `reports/composition-audit.json`; writes `registry/*.json`, `.cursorrules`, `copilot-instructions.md`, `ai-context.json`
- §4.9 — AI Semantic Layer Crew specification (Agents 41–45, Tasks T1–T5)
- §8 — Exit criteria (AI Semantic Layer outputs are non-fatal to core design system validation)

## Pipeline Impact

- [ ] Pipeline phase ordering
- [x] Crew I/O contracts (§3.6) — outputs change from stub placeholders to fully populated files; additive and backwards-compatible with Release Crew consumers
- [ ] Retry protocol (§3.4)
- [ ] Human gate policy (§5)
- [ ] Exit criteria (§8)
- [ ] Brand Profile schema (§6)

> **I/O note:** The crew I/O contract (§3.6) is satisfied without change — input paths (`specs/`, `src/`, `tokens/`, `reports/composition-audit.json`) are already produced by earlier phases. Output paths (`.cursorrules`, `copilot-instructions.md`, `ai-context.json`, `registry/*.json`) are listed in §3.6 and currently written as stubs. This change populates them with real content. No new output paths are introduced.

## Approach

1. **Write tests first** for all five agents and the crew factory (TDD red phase).
2. **Implement helper tools** in `src/daf/tools/` — `spec_indexer.py`, `example_code_generator.py`, `registry_builder.py`, `token_graph_traverser.py`, `semantic_mapper.py`, `composition_rule_extractor.py`, `tree_validator.py`, `rule_compiler.py`, `context_formatter.py`, `token_budget_optimizer.py`, `multi_format_serializer.py`.
3. **Implement agent factories** in `src/daf/agents/` — `registry_maintenance.py`, `token_resolution.py`, `composition_constraint.py`, `validation_rule.py`, `context_serializer.py` — each following the `create_<agent>_agent(model, output_dir)` pattern.
4. **Rewrite `src/daf/crews/ai_semantic_layer.py`** replacing the `StubCrew` with a real `crewai.Crew`, wiring T1→T2→T3→T4→T5 in sequential order, with a pre-flight guard that checks for required input files (`specs/*.spec.yaml`).
5. **Run tests green**, ensure no regressions in existing test suite.
6. **Commit** with conventional commit message `feat(ai-semantic-layer): implement AI Semantic Layer Crew agents 41-45`.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Token budget for `.cursorrules` / `copilot-instructions.md` may exceed IDE context limits | Medium | Token Budget Optimizer tool truncates or summarises registry entries to fit within configurable token limits |
| `reports/composition-audit.json` may not exist for earlier pipeline stages | Low | Agent 43 falls back to deriving composition rules from spec YAMLs if the audit report is absent |
| Registry builder duplicates logic from `primitive_registry.py` | Medium | Extend `daf.tools.primitive_registry` rather than reimplementing; Agent 41 reads from it |
| LLM-based agents produce non-deterministic output in tests | Medium | Stub LLM calls in unit tests; assert JSON structure validity, not exact content |
| AI context files may reference wrong token names after token rename | Low | Agent 45 reads registry files produced by Agents 41–44 in the same run; no stale cache risk |
