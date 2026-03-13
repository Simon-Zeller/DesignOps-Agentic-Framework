# Specification: Component Documentation Generation

## Purpose

Defines the behavioral requirements for Agent 21 (Doc Generation Agent) in the Documentation Crew. Covers per-component Markdown doc generation — prop tables, variant showcases, usage examples, and token binding references — as well as the project-level `docs/README.md`.

---

## Requirements

### Requirement: Per-component Markdown doc with prop table

Agent 21 (Doc Generation Agent) MUST generate a Markdown file at `docs/components/<ComponentName>.md` for every component spec found in `specs/*.spec.yaml`. The doc MUST include a prop table rendered from the spec's `props` section: columns for prop name, type, required flag, default value, and description.

Prop table rules:
- All props declared in the spec's `props` dict MUST appear as rows
- Required props MUST be visually marked (bold or asterisk convention)
- Props with no default MUST show `—` in the default column
- Type values MUST be rendered verbatim as declared in the spec

**Acceptance criteria:**
- Given a spec with 3 props (`label: string required`, `disabled: boolean default false`, `onPress: function required`), when Agent 21 runs, then `docs/components/Button.md` contains a Markdown table with exactly 3 rows matching those props
- Given a spec with no `props` key, when Agent 21 runs, then the doc omits the prop table section with a note "No props declared"

---

### Requirement: Variant showcase section

Agent 21 MUST include a variant showcase section listing every declared variant with a short description and a Markdown code block demonstrating usage for that variant.

Variant showcase rules:
- Each variant from the spec's `variants` list MUST appear as a subsection
- Each variant MUST include at least one TSX code block
- Code blocks MUST use triple-backtick fenced code with `tsx` language tag

**Acceptance criteria:**
- Given a Button spec with `variants: [primary, secondary, destructive]`, when Agent 21 runs, then `docs/components/Button.md` contains three variant subsections each with a TSX code block
- Given a spec with `variants: []`, when Agent 21 runs, then the variant section shows "No variants declared"

---

### Requirement: Minimum two usage examples per component

Agent 21 MUST generate at least two usage examples per component: one basic (minimal props) and one advanced (all significant props used). These are written via `_call_llm()` to ensure readable, contextually appropriate code.

**Acceptance criteria:**
- Given any component spec, when Agent 21 runs with `_call_llm` mocked to return valid TSX, then `docs/components/<Name>.md` contains two or more TSX code blocks outside the variant section
- Given `_call_llm` returning an empty string, when Agent 21 runs, then the agent falls back to a stub usage example rather than writing an empty code block

---

### Requirement: Token binding reference section

Agent 21 MUST include a token binding reference section showing which design tokens the component consumes, pulled from the spec's `tokens` dict.

Token binding rules:
- Each entry in `tokens: {}` MUST appear as a row: token key (prop role) | token path | resolved value
- Resolved values are looked up from `tokens/semantic.tokens.json` using `token_value_resolver`
- Unresolved tokens MUST still appear in the table with `(unresolved)` as the value

**Acceptance criteria:**
- Given a Button spec with `tokens: {background: "color.interactive.default"}` and compiled tokens containing that key, when Agent 21 runs, then the token binding table shows the resolved hex value
- Given a token path that is not in compiled tokens, when Agent 21 runs, then the table shows `(unresolved)` rather than an empty cell

---

### Requirement: Project README generation

Agent 21 MUST generate `docs/README.md` covering: npm install instructions, quick-start import example, available components list (from all generated specs), available tokens overview (top-level categories), and links to individual component docs.

**Acceptance criteria:**
- Given 3 component specs (Button, Badge, Input) processed by Agent 21, when Agent 21 runs, then `docs/README.md` lists all three components with links to `docs/components/<Name>.md`
- Given an output dir with no specs, when Agent 21 runs, then `docs/README.md` is still created with empty component list and a note that no components were generated
