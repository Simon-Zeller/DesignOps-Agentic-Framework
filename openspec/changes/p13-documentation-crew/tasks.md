# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p13-documentation-crew`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Confirm `uv sync` is up to date — no missing deps for `pyyaml`, `crewai`

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code.
     Each test maps to a case from tdd.md. -->

### 1a. Test Fixtures

- [x] 1.1 Create `tests/fixtures/button.spec.yaml` — Button spec with `props`, `variants`, `states`, `tokens`, `a11y`
- [x] 1.2 Create `tests/fixtures/semantic.tokens.json` — compiled token map (`color.interactive.default`, `space.4`)
- [x] 1.3 Create `tests/fixtures/generation-summary.json` — summary with `archetype`, `decisions` list (≥2 entries), each with `title/context/decision/consequences`
- [x] 1.4 Create `tests/fixtures/brand-profile.json` — profile with `archetype`, `a11y_level`, `modular_scale`

### 1b. Tool Tests (Doc Rendering Group)

- [x] 1.5 Create `tests/test_spec_to_doc_renderer.py` — 5 tests: name, props list, variants, token bindings, missing-props fallback
- [x] 1.6 Create `tests/test_prop_table_generator.py` — 4 tests: header row, required prop dash, optional prop default, empty list note
- [x] 1.7 Create `tests/test_example_code_generator.py` — 3 tests: contains name, TSX fence, variant-aware output
- [x] 1.8 Create `tests/test_readme_template.py` — 4 tests: install instructions, all names listed, doc links, empty-components graceful

### 1c. Tool Tests (Token Catalog Group)

- [x] 1.9 Create `tests/test_token_value_resolver.py` — 5 tests: resolves known, None for unknown, semantic tier, global tier, component tier
- [x] 1.10 Create `tests/test_scale_visualizer.py` — 3 tests: color swatch symbol, spacing value, non-color passthrough
- [x] 1.11 Create `tests/test_usage_context_extractor.py` — 2 tests: returns string for known usage, never raises for unknown

### 1d. Tool Tests (Narrative & ADR Group)

- [x] 1.12 Create `tests/test_decision_log_reader.py` — 3 tests: reads decisions, empty list on missing key, empty list on missing file
- [x] 1.13 Create `tests/test_brand_profile_analyzer.py` — 4 tests: extracts archetype, a11y level, missing archetype default, empty profile defaults
- [x] 1.14 Create `tests/test_prose_generator.py` — 4 tests: prompt contains archetype, prompt contains a11y, non-empty string, empty decisions no crash
- [x] 1.15 Create `tests/test_decision_extractor.py` — 3 tests: all decisions extracted, empty list for no key, required keys present with defaults
- [x] 1.16 Create `tests/test_adr_template_generator.py` — 5 tests: Context section, Decision section, Consequences section, slugify basic, slugify strips specials

### 1e. Tool Tests (Search Index Group)

- [x] 1.17 Create `tests/test_search_index_builder.py` — 4 tests: returns list, required keys, strips Markdown, empty input → empty list
- [x] 1.18 Create `tests/test_metadata_tagger.py` — 4 tests: component category, token category, decision category, readme category

### 1f. Agent Tests

- [x] 1.19 Create `tests/test_doc_generation_agent.py` — 4 tests: creates `docs/components/Button.md`, contains prop table, creates `docs/README.md`, README lists Button
- [x] 1.20 Create `tests/test_token_catalog_agent.py` — 3 tests: creates `docs/tokens/catalog.md`, contains token path, contains resolved value
- [x] 1.21 Create `tests/test_generation_narrative_agent.py` — 3 tests: creates `docs/decisions/generation-narrative.md`, contains LLM output, file created even when summary absent
- [x] 1.22 Create `tests/test_decision_record_agent.py` — 3 tests: creates one ADR per decision, filename is slugified, fallback ADR when no decisions
- [x] 1.23 Create `tests/test_search_index_agent.py` — 5 tests: creates `docs/search-index.json`, valid JSON array, contains component entries, contains token entries, empty docs → empty array

### 1g. Integration Test

- [x] 1.24 Create `tests/test_documentation_crew.py` — 3 tests: all 6 output files exist after `kickoff()`, search index is valid JSON, kickoff does not raise

### 1h. Red Phase Confirmation

- [x] 1.25 Run `uv run pytest tests/test_spec_to_doc_renderer.py tests/test_prop_table_generator.py tests/test_example_code_generator.py tests/test_readme_template.py -x 2>&1 | head -30` — confirm ImportError (red)
- [x] 1.26 Run `uv run pytest tests/test_token_value_resolver.py tests/test_scale_visualizer.py tests/test_usage_context_extractor.py -x 2>&1 | head -20` — confirm ImportError (red)
- [x] 1.27 Run `uv run pytest tests/test_decision_log_reader.py tests/test_brand_profile_analyzer.py tests/test_prose_generator.py tests/test_decision_extractor.py tests/test_adr_template_generator.py -x 2>&1 | head -20` — confirm ImportError (red)
- [x] 1.28 Run `uv run pytest tests/test_search_index_builder.py tests/test_metadata_tagger.py -x 2>&1 | head -20` — confirm ImportError (red)
- [x] 1.29 Run `uv run pytest tests/test_doc_generation_agent.py tests/test_token_catalog_agent.py tests/test_generation_narrative_agent.py tests/test_decision_record_agent.py tests/test_search_index_agent.py tests/test_documentation_crew.py -x 2>&1 | head -20` — confirm ImportError (red)
- [x] 1.30 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p13-documentation-crew"`

## 2. Implementation (TDD — Green Phase)

<!-- Write the minimum production code to make tests pass. -->

### 2a. Doc Rendering Tools

- [x] 2.1 Create `src/daf/tools/spec_to_doc_renderer.py` — `render_spec_to_sections(spec_dict) -> dict`; extract `name`, `props` list, `variants`, `token_bindings`; return defaults for missing keys
- [x] 2.2 Create `src/daf/tools/prop_table_generator.py` — `generate_prop_table(props) -> str`; return `| Prop | Type | Required | Default |` Markdown table; return "No props declared." for empty list
- [x] 2.3 Create `src/daf/tools/example_code_generator.py` — `generate_example_stub(component_name, variant) -> str`; return TSX code fence stub using component name and variant
- [x] 2.4 Create `src/daf/tools/readme_template.py` — `render_readme(component_names, token_categories) -> str`; include install instructions, component links, graceful empty state
- [x] 2.5 Run `uv run pytest tests/test_spec_to_doc_renderer.py tests/test_prop_table_generator.py tests/test_example_code_generator.py tests/test_readme_template.py` — all pass (green)

### 2b. Token Catalog Tools

- [x] 2.6 Create `src/daf/tools/token_value_resolver.py` — `resolve_token(token_path, compiled_tokens) -> str | None`; `classify_tier(token_path) -> str` (global/semantic/component heuristics)
- [x] 2.7 Create `src/daf/tools/scale_visualizer.py` — `visualize_token(token_path, value) -> str`; color tokens → `■ {value}`; spacing tokens → `— {value}`; fallback returns value
- [x] 2.8 Create `src/daf/tools/usage_context_extractor.py` — `extract_usage_context(token_path, spec_tokens_map) -> str`; reverse-lookup token path in spec map; return role name or empty string
- [x] 2.9 Run `uv run pytest tests/test_token_value_resolver.py tests/test_scale_visualizer.py tests/test_usage_context_extractor.py` — all pass (green)

### 2c. Narrative & ADR Tools

- [x] 2.10 Create `src/daf/tools/decision_log_reader.py` — `read_decisions(path) -> list[dict]`; read JSON from path, return `decisions` key or `[]`; return `[]` on missing file
- [x] 2.11 Create `src/daf/tools/brand_profile_analyzer.py` — `analyze_brand_profile(profile_dict) -> dict`; extract `archetype` (default `"unspecified"`), `a11y_level` (default `"AA"`), `modular_scale`
- [x] 2.12 Create `src/daf/tools/prose_generator.py` — `build_narrative_prompt(brand_analysis, decisions) -> str`; compose a prompt string from brand data and decisions list
- [x] 2.13 Create `src/daf/tools/decision_extractor.py` — `extract_decisions(generation_summary) -> list[dict]`; return `decisions` list; ensure each entry has `title`, `context`, `decision`, `consequences` (default `""`)
- [x] 2.14 Create `src/daf/tools/adr_template_generator.py` — `generate_adr(decision) -> str`; output `# ADR: {title}\n\n## Context\n...\n\n## Decision\n...\n\n## Consequences\n...`; `slugify_title(title) -> str` (lowercase, spaces→dashes, strip non-alphanumeric)
- [x] 2.15 Run `uv run pytest tests/test_decision_log_reader.py tests/test_brand_profile_analyzer.py tests/test_prose_generator.py tests/test_decision_extractor.py tests/test_adr_template_generator.py` — all pass (green)

### 2d. Search Index Tools

- [x] 2.16 Create `src/daf/tools/search_index_builder.py` — `build_index_entries(markdown_content, file_path) -> list[dict]`; split on `##` H2 headings; each entry has `id`, `title`, `content` (stripped of `#`/`*`/backtick), `path`; return `[]` for empty input
- [x] 2.17 Create `src/daf/tools/metadata_tagger.py` — `tag_entry(entry, file_path) -> dict`; set `category` from path pattern: `components/` → "component", `tokens/` → "token", `decisions/` → "decision", `README` → "readme"
- [x] 2.18 Run `uv run pytest tests/test_search_index_builder.py tests/test_metadata_tagger.py` — all pass (green)

### 2e. Agents

- [x] 2.19 Create `src/daf/agents/doc_generation.py` — `_call_llm(prompt) -> str`; `run_doc_generation(output_dir)`: load specs YAML, load compiled tokens; for each spec call `render_spec_to_sections`, `generate_prop_table`, `generate_example_stub` (via `_call_llm`); write `docs/components/{Name}.md`; write `docs/README.md` via `render_readme`
- [x] 2.20 Create `src/daf/agents/token_catalog.py` — `_call_llm(prompt) -> str`; `run_token_catalog(output_dir)`: load compiled tokens; for each token call `resolve_token`, `classify_tier`, `scale_visualizer`, `extract_usage_context` (LLM for descriptions); write `docs/tokens/catalog.md`
- [x] 2.21 Create `src/daf/agents/generation_narrative.py` — `_call_llm(prompt) -> str`; `run_generation_narrative(output_dir)`: load `brand-profile.json` and `reports/generation-summary.json`; call `analyze_brand_profile`, `read_decisions`, `build_narrative_prompt`, then `_call_llm`; write `docs/decisions/generation-narrative.md`
- [x] 2.22 Create `src/daf/agents/decision_record.py` — `_call_llm(prompt) -> str`; `run_decision_records(output_dir)`: load generation summary; call `extract_decisions`; for each decision call `generate_adr` + `_call_llm` (enrich consequences); write `docs/decisions/adr-{slugify_title(title)}.md`; if no decisions write `docs/decisions/adr-no-decisions.md`
- [x] 2.23 Create `src/daf/agents/search_index.py` — `run_search_index(output_dir)`: glob `docs/**/*.md`; for each file call `build_index_entries` then `tag_entry`; flatten all entries; write `docs/search-index.json` (JSON array); no `_call_llm`
- [x] 2.24 Run `uv run pytest tests/test_doc_generation_agent.py tests/test_token_catalog_agent.py tests/test_generation_narrative_agent.py tests/test_decision_record_agent.py tests/test_search_index_agent.py` — all pass (green)

### 2f. Crew Factory

- [x] 2.25 Create `src/daf/crews/documentation.py` — `create_documentation_crew(output_dir: str) -> StubCrew`; `kickoff()` calls in sequence: `run_doc_generation`, `run_token_catalog`, `run_generation_narrative`, `run_decision_records`, `run_search_index` — all with `output_dir`
- [x] 2.26 Run `uv run pytest tests/test_documentation_crew.py` — all 3 integration tests pass (green)

### 2g. `__init__.py` Exports

- [x] 2.27 Add 14 tool public exports to `src/daf/tools/__init__.py`
- [x] 2.28 Add 5 agent function exports to `src/daf/agents/__init__.py`
- [x] 2.29 Add `create_documentation_crew` export to `src/daf/crews/__init__.py`
- [x] 2.30 Run full new test suite: `uv run pytest tests/test_spec_to_doc_renderer.py tests/test_prop_table_generator.py tests/test_example_code_generator.py tests/test_readme_template.py tests/test_token_value_resolver.py tests/test_scale_visualizer.py tests/test_usage_context_extractor.py tests/test_decision_log_reader.py tests/test_brand_profile_analyzer.py tests/test_prose_generator.py tests/test_decision_extractor.py tests/test_adr_template_generator.py tests/test_search_index_builder.py tests/test_metadata_tagger.py tests/test_doc_generation_agent.py tests/test_token_catalog_agent.py tests/test_generation_narrative_agent.py tests/test_decision_record_agent.py tests/test_search_index_agent.py tests/test_documentation_crew.py` — all pass
- [x] 2.31 **Git checkpoint:** `git add -A && git commit -m "feat: implement p13-documentation-crew (14 tools, 5 agents, crew factory)"`

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Extract shared `_write_file(path, content)` helper if ≥3 agents repeat the mkdir+write pattern
- [x] 3.2 Extract `_load_json(path, default)` helper if ≥2 tools repeat the try/except file load
- [x] 3.3 Review `search_index.py` agent — confirm deterministic path (no LLM, no `_call_llm` import)
- [x] 3.4 Review design.md ADRs — confirm all 4 architectural decisions are reflected in code
- [x] 3.5 Ensure all tests still pass after refactor: `uv run pytest tests/test_doc_generation_agent.py tests/test_token_catalog_agent.py tests/test_generation_narrative_agent.py tests/test_decision_record_agent.py tests/test_search_index_agent.py tests/test_documentation_crew.py`
- [x] 3.6 **Git checkpoint:** `git add -A && git commit -m "refactor: clean up p13-documentation-crew"`

## 4. Integration & Quality

- [x] 4.1 Run `uv run ruff check src/daf/tools/spec_to_doc_renderer.py src/daf/tools/prop_table_generator.py src/daf/tools/example_code_generator.py src/daf/tools/readme_template.py src/daf/tools/token_value_resolver.py src/daf/tools/scale_visualizer.py src/daf/tools/usage_context_extractor.py src/daf/tools/decision_log_reader.py src/daf/tools/brand_profile_analyzer.py src/daf/tools/prose_generator.py src/daf/tools/decision_extractor.py src/daf/tools/adr_template_generator.py src/daf/tools/search_index_builder.py src/daf/tools/metadata_tagger.py` — zero errors
- [x] 4.2 Run `uv run ruff check src/daf/agents/doc_generation.py src/daf/agents/token_catalog.py src/daf/agents/generation_narrative.py src/daf/agents/decision_record.py src/daf/agents/search_index.py src/daf/crews/documentation.py` — zero errors
- [x] 4.3 Run `uv run pyright src/daf/tools/ src/daf/agents/doc_generation.py src/daf/agents/token_catalog.py src/daf/agents/generation_narrative.py src/daf/agents/decision_record.py src/daf/agents/search_index.py src/daf/crews/documentation.py` — zero type errors
- [x] 4.4 Run full test suite: `uv run pytest` — all pre-existing tests still pass, zero regressions
- [x] 4.5 Confirm new test count: `uv run pytest --collect-only -q | grep "test session starts" -A 5` — 20 new tests listed (14 tool + 5 agent + 1 integration)
- [x] 4.6 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for p13-documentation-crew"` (skip if no changes)

## 5. Final Verification & Push

- [x] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [x] 5.2 `git log --oneline main..HEAD` — review all commits on this branch
- [x] 5.3 Rebase on latest main if needed (`git fetch origin && git rebase origin/main`)
- [x] 5.4 Push feature branch (`git push origin feat/p13-documentation-crew`)

## 6. Delivery

- [x] 6.1 All tasks above are checked
- [x] 6.2 Merge feature branch into main (`git checkout main && git merge feat/p13-documentation-crew`)
- [x] 6.3 Push main (`git push origin main`)
- [x] 6.4 Delete local feature branch (`git branch -d feat/p13-documentation-crew`)
- [x] 6.5 Delete remote feature branch (`git push origin --delete feat/p13-documentation-crew`)
- [x] 6.6 Verify clean state (`git branch -a` — feature branch gone, `git status` — clean)
