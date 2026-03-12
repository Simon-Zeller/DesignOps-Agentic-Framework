# Design: {{change-name}}

## Technical Approach

<!-- How will this be implemented? Describe the solution. -->

## Agent vs. Deterministic Decisions

<!-- What is agent-driven (LLM) vs. deterministic (tool)? -->

| Capability | Mode | Rationale |
|------------|------|-----------|
|            |      |           |

## Model Tier Assignment

<!-- For any new or modified agents, specify the model tier -->

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
|       |      |       |           |

## Architecture Decisions

### Decision: [Title]

**Context:** <!-- Why this decision was needed -->

**Decision:** <!-- What was decided -->

**Consequences:** <!-- What follows from this decision -->

## Data Flow

<!-- Crew-to-crew file handoffs affected by this change -->

```
[Source Crew] ──writes──► [file(s)] ──reads──► [Target Crew]
```

## Retry & Failure Behavior

<!-- What happens when this logic fails validation? -->
<!-- Which retry boundary applies? (see PRD §3.4) -->

## File Changes

<!-- List of files to create, modify, or delete -->

- `path/to/file.py` (new/modified/deleted) — description
