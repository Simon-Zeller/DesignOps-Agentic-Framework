# Specification: Token Catalog, Narrative, ADRs, and Search Index

## Purpose

Defines the behavioral requirements for Agents 22–25 in the Documentation Crew:
- Agent 22 (Token Catalog Agent) — token catalog with resolved values, tiers, and visual representations
- Agent 23 (Generation Narrative Agent) — human-readable "why" document
- Agent 24 (Decision Record Agent) — Architecture Decision Records per significant generation decision
- Agent 25 (Search Index Agent) — full-text searchable JSON index across all docs

---

## Requirements

### Requirement: Token catalog organized by category

Agent 22 (Token Catalog Agent) MUST generate `docs/tokens/catalog.md` containing every token from the compiled token files, organized by top-level category (e.g., `color`, `spacing`, `typography`, `radius`, `shadow`). Each entry MUST show: token path, resolved value, tier classification (global/semantic/component), and a visual representation where applicable.

Tier classification rules:
- Tokens whose key starts with a tier prefix (`color.global.*`, `space.global.*`) OR whose file origin is `global.tokens.json` → tier: `global`
- Tokens whose key starts with a semantic prefix or originates from `semantic.tokens.json` → tier: `semantic`
- All other tokens → tier: `component`

Visual representation rules:
- Color tokens: render a hex value inline with a text label (e.g., `■ #005FCC`)
- Spacing tokens: render a numeric size value (e.g., `— 8px`)
- Typography tokens: render the value as-is
- All other tokens: render value as plain text

**Acceptance criteria:**
- Given compiled tokens containing `color.interactive.default: "#005FCC"` (semantic tier), when Agent 22 runs, then `docs/tokens/catalog.md` contains an entry with path `color.interactive.default`, value `#005FCC`, tier `semantic`, and visual `■ #005FCC`
- Given tokens from both `global.tokens.json` and `semantic.tokens.json`, when Agent 22 runs, then the catalog groups them under their respective tier sections
- Given an empty token file, when Agent 22 runs, then the catalog is created with an empty section placeholder rather than failing

---

### Requirement: Token usage context description

Agent 22 MUST include a usage context description for each token entry, generated via `_call_llm()` using the token path and value as context. The description explains what the token is used for in the design system.

**Acceptance criteria:**
- Given a token `color.interactive.default` with value `#005FCC`, when Agent 22 runs with `_call_llm` mocked to return "Used as the primary background color for interactive elements", then the catalog entry includes that description
- Given `_call_llm` returning an empty string, when Agent 22 runs, then the catalog entry falls back to `(no description)` rather than an empty field

---

### Requirement: Generation narrative covers key design decisions

Agent 23 (Generation Narrative Agent) MUST generate `docs/decisions/generation-narrative.md` as a human-readable account of *why* the design system looks the way it does. The narrative MUST cover:
1. Which archetype was selected and why (from Brand Profile)
2. Which Brand Profile choices drove which token decisions
3. How the modular scale ratio was chosen
4. What accessibility tier implications affected the palette
5. Any human gate overrides and their justification (if present in generation summary)

The narrative is prose-only (no tables), generated via `_call_llm()`. The `brand_profile_analyzer` and `decision_log_reader` tools provide structured inputs to the LLM prompt.

**Acceptance criteria:**
- Given a brand-profile.json with `{"archetype": "minimalist", "a11y_level": "AA", "modular_scale": 1.25}`, when Agent 23 runs with `_call_llm` mocked, then `docs/decisions/generation-narrative.md` is created and contains non-empty prose
- Given a brand-profile.json with no `archetype` key, when Agent 23 runs, then the narrative notes "archetype not specified" rather than failing
- Given `docs/decisions/` directory does not exist yet, when Agent 23 runs, then the directory is created before writing the file

---

### Requirement: One ADR per significant generation decision

Agent 24 (Decision Record Agent) MUST generate one Architecture Decision Record per significant decision found in `reports/generation-summary.json`. Each ADR MUST follow the standard format: Context → Decision → Consequences. ADR files MUST be written to `docs/decisions/adr-<slug>.md` where `<slug>` is a kebab-case version of the decision title.

ADR generation rules:
- The `decision_extractor` tool reads `decisions[]` from the generation summary
- The `adr_template_generator` tool fills the template for each decision
- If no decisions are found in the summary, Agent 24 writes one default ADR: `adr-no-decisions.md` with a note that no explicit decisions were recorded
- ADR titles MUST be sanitized to valid filenames (lowercase, spaces→dashes, special chars stripped)

**Acceptance criteria:**
- Given a generation summary with `decisions: [{title: "Archetype Selection", context: "...", decision: "...", consequences: "..."}]`, when Agent 24 runs, then `docs/decisions/adr-archetype-selection.md` is created following the ADR template
- Given a generation summary with no `decisions` key, when Agent 24 runs, then `docs/decisions/adr-no-decisions.md` is created with a fallback note
- Given a decision title `"Token Scale Algorithm (v2)"`, when Agent 24 runs, then the file is named `adr-token-scale-algorithm-v2.md`

---

### Requirement: Search index covers all docs with component, token, and decision entries

Agent 25 (Search Index Agent) MUST generate `docs/search-index.json` as an array of index entries. Each entry MUST contain: `id` (unique string), `title`, `content` (searchable text excerpt), `category` (`component` | `token` | `decision` | `readme`), `path` (relative path to the source doc file), and an optional `status` field.

Search index rules:
- One entry per Markdown heading-paragraph chunk in each doc file
- The `metadata_tagger` tool assigns category and status based on file path pattern:
  - `docs/components/*.md` → category: `component`
  - `docs/tokens/catalog.md` → category: `token`
  - `docs/decisions/*.md` → category: `decision`
  - `docs/README.md` → category: `readme`
- Index entries MUST NOT include raw Markdown formatting in `content` (strip `#`, `*`, `` ` ``)
- The index MUST be valid JSON (parseable by `json.loads`)

**Acceptance criteria:**
- Given `docs/components/Button.md` containing an H1 "Button" and a paragraph about its usage, when Agent 25 runs, then `docs/search-index.json` contains at least one entry with `category: "component"`, `title` containing "Button", and non-empty `content`
- Given `docs/tokens/catalog.md` with token entries, when Agent 25 runs, then the index contains entries with `category: "token"`
- Given an empty docs directory, when Agent 25 runs, then `docs/search-index.json` is created as an empty array `[]` rather than failing
- The produced JSON MUST be parseable by `json.loads` without error in all cases
