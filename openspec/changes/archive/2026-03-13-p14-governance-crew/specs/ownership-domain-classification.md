# Specification: Ownership & Domain Classification

## Purpose

Defines the behavior of Agent 26 (Ownership Agent) and its tools (`domain_classifier.py`, `relationship_analyzer.py`, `orphan_scanner.py`). The agent assigns each component and token category to exactly one logical domain and produces `governance/ownership.json`.

## Requirements

### Requirement: Domain classifier assigns every component to exactly one domain

Agent 26 MUST classify every component in the component index into exactly one of the domains defined in `pipeline-config.json`'s `domains` section. A component that matches multiple domains SHALL be assigned to the domain with the highest keyword match score. A component that matches no domain SHALL be flagged as an orphan.

The `domain_classifier.py` tool SHALL accept a list of component names and a domain map (domain name → list of keywords), and SHALL return a dict mapping each component name to a domain name or `"__orphan__"`.

#### Acceptance Criteria

- [ ] Every component name in the component index appears in `governance/ownership.json` exactly once.
- [ ] No component is assigned to a domain not present in `pipeline-config.json`'s `domains` section.
- [ ] Components matching zero domain keywords are listed under `ownership.json`'s `orphans` array.
- [ ] Components matching multiple domains are assigned to the highest-score domain, with the alternative matches recorded in `alternate_domains`.
- [ ] `domain_classifier.py` has 100% branch coverage in its unit tests.

#### Scenario: Standard component classification

- GIVEN `pipeline-config.json` defines domains `["forms", "navigation", "feedback", "layout", "data-display"]`
- AND the component index contains `Button`, `Input`, `Select`, `Breadcrumb`, `Toast`, `Card`
- WHEN Agent 26 runs Task T1
- THEN `Button` is classified as `forms`, `Input` as `forms`, `Select` as `forms`, `Breadcrumb` as `navigation`, `Toast` as `feedback`, `Card` as `layout`

#### Scenario: Multi-domain ambiguity resolved by score

- GIVEN `DataGrid` matches both `data-display` (score: 3) and `forms` (score: 1)
- WHEN `domain_classifier.py` processes `DataGrid`
- THEN `DataGrid` is assigned `data-display`
- AND `governance/ownership.json` records `alternate_domains: ["forms"]` for `DataGrid`

#### Scenario: Orphan detection

- GIVEN a custom component `MegaMenu` matches no keyword in any domain
- WHEN `domain_classifier.py` processes `MegaMenu`
- THEN `MegaMenu` is classified as `"__orphan__"`
- AND `governance/ownership.json`'s `orphans` array contains `"MegaMenu"`

---

### Requirement: Relationship analyzer detects cross-domain dependencies

The `relationship_analyzer.py` tool SHALL read `docs/component-index.json` and return a list of cross-domain dependency pairs: `{"component": str, "depends_on": str, "component_domain": str, "dependency_domain": str}`. A cross-domain dependency is any case where a component in domain A imports or composes a component in domain B where A ≠ B.

#### Acceptance Criteria

- [ ] `relationship_analyzer.py` reads `docs/component-index.json` without scanning TSX source.
- [ ] Cross-domain dependency pairs are listed in `governance/ownership.json` under `cross_domain_dependencies`.
- [ ] If `component-index.json` is absent, the tool returns an empty list and logs a Warning (not a Fatal error).

#### Scenario: Cross-domain dependency detected

- GIVEN `Select` (domain: `forms`) depends on `Popover` (domain: `layout`)
- WHEN `relationship_analyzer.py` analyzes the component index
- THEN the pair `{component: "Select", depends_on: "Popover", component_domain: "forms", dependency_domain: "layout"}` appears in `cross_domain_dependencies`

#### Scenario: Missing component-index.json fallback

- GIVEN `docs/component-index.json` does not exist
- WHEN `relationship_analyzer.py` is called
- THEN it returns `[]` and logs `WARNING: component-index.json not found; relationship analysis skipped`
- AND `governance/ownership.json` is still written with no `cross_domain_dependencies` entry

---

### Requirement: ownership.json conforms to required schema

The `governance/ownership.json` file MUST conform to the prescribed schema and be valid JSON.

#### Acceptance Criteria

- [ ] `governance/ownership.json` contains top-level keys: `domains` (array), `orphans` (array), `cross_domain_dependencies` (array).
- [ ] Each entry in `domains` has keys: `name` (str), `components` (array of str), `token_categories` (array of str).
- [ ] File is valid JSON parseable by Python's `json.loads`.
- [ ] File is written atomically (write to temp file, rename to target).
