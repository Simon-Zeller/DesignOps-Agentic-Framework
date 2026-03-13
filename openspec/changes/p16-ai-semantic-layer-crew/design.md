# Design: p16-ai-semantic-layer-crew

## Technical Approach

Replace the `StubCrew` in `src/daf/crews/ai_semantic_layer.py` with a real `crewai.Crew` housing five agents (Agents 41–45). Each agent encapsulates its knowledge-building logic via an LLM-backed `crewai.Agent`, while the heavy file-system and structural work (spec parsing, graph traversal, JSON assembly, format serialization) is delegated to deterministic tool classes in `src/daf/tools/`.

The crew follows the same structural pattern established by the Analytics and Governance crews:

1. Factory function `create_ai_semantic_layer_crew(output_dir: str) → Crew`
2. Pre-flight guard checking for required input files (`specs/*.spec.yaml`)
3. Five tasks `T1→T2→T3→T4→T5` wired sequentially (`context=[previous_task]`)
4. Each agent created via a `create_<agent>_agent(model, output_dir)` factory in `src/daf/agents/`

New deterministic tool classes are added to `src/daf/tools/` for capabilities not covered by existing tools. The existing `primitive_registry.py` tool is extended rather than duplicated, and Agent 41's `RegistryBuilder` reads from it directly.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Parse spec YAML and extract prop/variant/state/slot metadata | Deterministic | Mechanical YAML deserialization — no judgment needed |
| Write natural-language descriptions for registry entries | Agent (LLM) | Requires phrasing intent for human + AI readability |
| Resolve token references to final values per platform/tier | Deterministic | Pure graph traversal of compiled DTCG token trees |
| Map token semantic purpose and relate tokens by category | Agent (LLM) | Semantic grouping and natural language intent description requires reasoning |
| Extract allowed/forbidden children from composition rules YAML | Deterministic | Rule parsing — exact schema, no ambiguity |
| Generate example valid/invalid composition trees | Agent (LLM) | Constructing illustrative examples requires reasoning about valid vs. pathological combinations |
| Compile token/composition/a11y/naming rules into exportable schema | Deterministic | Rule aggregation from existing validated sources — mechanical assembly |
| Enrich compliance rule descriptions for LLM consumption | Agent (LLM) | Natural language explanations of *why* a rule exists requires contextual reasoning |
| Calculate token budget and truncate/summarise context | Deterministic | Token counting and space-allocation algorithms — deterministic by design |
| Format registry data into Cursor/Copilot/generic LLM output | Deterministic | Template-driven serialization — exact format specifications |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 41 – Registry Maintenance Agent | Tier 3 | `claude-3-5-haiku-20241022` | Structured data extraction and description generation from already-parsed spec data; speed preferred over depth |
| Agent 42 – Token Resolution Agent | Tier 3 | `claude-3-5-haiku-20241022` | Natural language description of token intent from resolved values and tier metadata; structured output, low reasoning load |
| Agent 43 – Composition Constraint Agent | Tier 2 | `claude-3-5-sonnet-20241022` | Must reason about valid vs. invalid composition trees and generate semantically meaningful examples; moderate complexity |
| Agent 44 – Validation Rule Agent | Tier 3 | `claude-3-5-haiku-20241022` | Aggregates and re-phrases already-validated rules; structured assembly with light natural language enrichment |
| Agent 45 – Context Serializer Agent | Tier 2 | `claude-3-5-sonnet-20241022` | Must reason about which registry content is highest-signal for each AI consumer format and apply token-budget prioritisation; moderate complexity |

## Architecture Decisions

### Decision: Agent 41 extends `primitive_registry.py` rather than re-implementing

**Context:** `src/daf/tools/primitive_registry.py` already builds a registry of primitive component exports. Agent 41's `RegistryBuilder` tool needs similar functionality at full component scope.

**Decision:** `RegistryBuilder` accepts the existing `PrimitiveRegistry` as a data source for primitive entries and extends it with data from spec YAMLs and generated TSX for full components. No duplication of file-crawling logic.

**Consequences:** Primitives are represented consistently in `registry/components.json`. Changes to primitive discovery logic propagate automatically to the AI semantic layer.

### Decision: `registry/tokens.json` is built from compiled tokens, not source YAML

**Context:** The Token Engine Crew compiles all DTCG source tokens into `tokens/*.tokens.json`. Accessing pre-compiled tokens means resolved values (including theme overrides) are available without Agent 42 needing to re-run Style Dictionary.

**Decision:** Token Resolution Agent reads `tokens/*.tokens.json` (the compiled DTCG files) as its source, not the raw YAML specs. Platform resolution and `$extensions` theme values are already resolved by the time Phase 5 runs.

**Consequences:** Agent 42 always sees the final resolved state. If a token source YAML changes but `tokens/*.tokens.json` is stale, Agent 42's graph reflects the stale state — but this is acceptable because Phase 5 always runs after Phase 1 in a clean pipeline run.

### Decision: Context Serializer applies token-budget optimisation before writing AI context files

**Context:** `registry/components.json` for a Comprehensive scope design system (25+ components × full prop metadata × usage examples) may exceed 100k tokens, which violates the context window limits of Cursor and GitHub Copilot.

**Decision:** Agent 45's `TokenBudgetOptimizer` tool applies a priority-ordered truncation strategy: (1) trim low-signal usage examples first, (2) abbreviate slot descriptions, (3) drop internal-only props, (4) summarize token bindings. The optimised output is written to `.cursorrules` and `copilot-instructions.md`; the full untruncated registry is kept in `ai-context.json` for generic LLM use.

**Consequences:** IDE-facing files remain within practical context limits. The full registry is always available in `ai-context.json` for tools without hard limits.

### Decision: Pre-flight guard on `specs/*.spec.yaml`

**Context:** Agent 41 (Registry Maintenance) requires spec files to build the component registry. These are produced by Phase 1 (Token Engine Crew). Without them, the entire crew produces empty or stub output.

**Decision:** `create_ai_semantic_layer_crew` raises `RuntimeError` if no `*.spec.yaml` files are found in `<output_dir>/specs/`. This mirrors the Analytics Crew pattern.

**Consequences:** Fast-fail with a descriptive error if the crew is invoked out of pipeline order. No silent stub-passthrough.

## Data Flow

```
Token Engine Crew   ──writes──► specs/*.spec.yaml         ──reads──► Agent 41 (Registry Maintenance)
                    ──writes──► tokens/*.tokens.json       ──reads──► Agent 42 (Token Resolution)

Design-to-Code Crew ──writes──► src/primitives/*.tsx       ──reads──► Agent 41 (Registry Maintenance)
                    ──writes──► src/components/**/*.tsx    ──reads──► Agent 41 (Registry Maintenance)

Component Factory   ──writes──► reports/composition-audit.json ──reads──► Agent 43 (Composition Constraint)

AI Semantic Layer   ──writes──► registry/components.json   ──reads──► Agent 43, 44, 45
                    ──writes──► registry/tokens.json        ──reads──► Agent 44, 45
                    ──writes──► registry/composition-rules.json ──reads──► Agent 44, 45
                    ──writes──► registry/compliance-rules.json  ──reads──► Agent 45
                    ──writes──► .cursorrules                (replaces stub placeholder)
                    ──writes──► copilot-instructions.md      (replaces stub placeholder)
                    ──writes──► ai-context.json              (replaces stub placeholder)
```

## Retry & Failure Behavior

Per PRD §3.4, Phases 4–6 use crew-level retry (max 2 attempts), not per-agent retry. If the AI Semantic Layer Crew fails catastrophically on the first attempt, `First Publish Agent (6)` retries the entire crew once. If the second attempt also fails, the crew is marked `failed` in `reports/generation-summary.json` and the pipeline continues.

AI Semantic Layer failures are **non-fatal** (Warning-level only). Missing or incomplete registry files do not block the Output Review gate or prevent the Release Crew from running.

Within a single crew run, tasks are sequential (`T1→T2→T3→T4→T5`). If `T2` (token resolution) raises an exception, the crew raises and triggers the crew-level retry. Tasks do not individually retry.

If `reports/composition-audit.json` is absent (e.g. Component Factory skipped), Agent 43 falls back to deriving composition rules from `specs/*.spec.yaml` directly.

## File Changes

- `src/daf/crews/ai_semantic_layer.py` (modified) — Replace `StubCrew` with real `crewai.Crew`; add pre-flight guard; wire T1–T5
- `src/daf/agents/registry_maintenance.py` (new) — Agent 41 factory
- `src/daf/agents/token_resolution.py` (new) — Agent 42 factory
- `src/daf/agents/composition_constraint.py` (new) — Agent 43 factory
- `src/daf/agents/validation_rule.py` (new) — Agent 44 factory
- `src/daf/agents/context_serializer.py` (new) — Agent 45 factory
- `src/daf/tools/spec_indexer.py` (new) — Parses `specs/*.spec.yaml` into structured component metadata for Agent 41
- `src/daf/tools/example_code_generator.py` (new) — Generates JSX usage examples from spec prop definitions for Agent 41
- `src/daf/tools/registry_builder.py` (new) — Assembles `registry/components.json` from spec metadata + TSX analysis for Agent 41
- `src/daf/tools/token_graph_traverser.py` (new) — Traverses compiled DTCG token trees to resolve values per platform/tier for Agent 42
- `src/daf/tools/semantic_mapper.py` (new) — Groups tokens by semantic category and maps them to natural language intent for Agent 42
- `src/daf/tools/composition_rule_extractor.py` (new) — Extracts allowed/forbidden nesting rules from composition audit and spec data for Agent 43
- `src/daf/tools/tree_validator.py` (new) — Validates component trees against composition rules for Agent 43
- `src/daf/tools/rule_compiler.py` (new) — Aggregates token, composition, a11y, and naming rules into `registry/compliance-rules.json` for Agent 44
- `src/daf/tools/context_formatter.py` (new) — Formats registry JSON into `.cursorrules` and `copilot-instructions.md` structures for Agent 45
- `src/daf/tools/token_budget_optimizer.py` (new) — Applies priority-ordered truncation to fit AI context within configurable token limits for Agent 45
- `src/daf/tools/multi_format_serializer.py` (new) — Writes the three AI context output files in their target formats for Agent 45
- `src/daf/agents/__init__.py` (modified) — Export five new agent factories
- `src/daf/tools/__init__.py` (modified) — Export twelve new tool classes
- `tests/test_registry_maintenance_agent.py` (new) — Unit tests for Agent 41
- `tests/test_token_resolution_agent.py` (new) — Unit tests for Agent 42
- `tests/test_composition_constraint_agent.py` (new) — Unit tests for Agent 43
- `tests/test_validation_rule_agent.py` (new) — Unit tests for Agent 44
- `tests/test_context_serializer_agent.py` (new) — Unit tests for Agent 45
- `tests/test_ai_semantic_layer_crew.py` (new) — Integration tests for the crew factory
- `tests/test_spec_indexer.py` (new) — Unit tests for SpecIndexer tool
- `tests/test_example_code_generator.py` (new) — Unit tests for ExampleCodeGenerator tool
- `tests/test_registry_builder.py` (new) — Unit tests for RegistryBuilder tool
- `tests/test_token_graph_traverser.py` (new) — Unit tests for TokenGraphTraverser tool
- `tests/test_semantic_mapper.py` (new) — Unit tests for SemanticMapper tool
- `tests/test_composition_rule_extractor.py` (new) — Unit tests for CompositionRuleExtractor tool
- `tests/test_tree_validator.py` (new) — Unit tests for TreeValidator tool
- `tests/test_rule_compiler.py` (new) — Unit tests for RuleCompiler tool
- `tests/test_context_formatter.py` (new) — Unit tests for ContextFormatter tool
- `tests/test_token_budget_optimizer.py` (new) — Unit tests for TokenBudgetOptimizer tool
- `tests/test_multi_format_serializer.py` (new) — Unit tests for MultiFormatSerializer tool
