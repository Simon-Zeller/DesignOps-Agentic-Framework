---
description: Autonomous AI debug pass — run the DAF CLI end-to-end and fix any issues found
---

You are an autonomous debugger for the DAF CLI pipeline. Your job is to run the CLI, read all generated output, compare it against the completed specs in the OpenSpec archive, find problems, fix them, and re-run until the output is fully correct.

**This is not a test suite.** You do not write assertions. You read files, reason about correctness, and fix code when something is wrong.

## How to run

1. **Execute the bootstrap script:**
   ```bash
   ./scripts/bootstrap.sh --sample --yes --clean
   ```
   This runs the full pipeline with a sample brand profile, auto-approves the Human Gate, and starts from a clean sandbox.

2. **Read all generated output** in `.daf-sandbox/`:
   - `brand-profile.json` — the enriched brand profile
   - `tokens/` directory — all W3C DTCG token files (if generated)
   - Any other files the pipeline produced
   - The terminal output from the script itself

3. **Read the reference material from the OpenSpec archive:**
   - `openspec/changes/archive/` — all completed change artifacts (proposal.md, specs/, design.md, tdd.md, tasks.md)
   - `openspec/specs/` — synced spec files from completed changes
   - If a specific change is being debugged, read its artifacts under `openspec/changes/<change-name>/` (active) or `openspec/changes/archive/<change-name>/` (completed)
   - Do NOT use PRD.md — the OpenSpec archive is the single source of truth

4. **Inspect and reason — check everything by reading, not by running validators:**
   - Are all expected files present? Any missing or unexpected?
   - Can every JSON file be parsed? Is the structure sensible?
   - Does the output match what the archived specs describe?
   - Do the generated values match the archetype and configuration from the specs?
   - Do token files follow W3C DTCG format? Are the three tiers present (base, semantic, component)?
   - Do cross-file references resolve? (semantic tokens reference base tokens that exist, component tokens reference semantic tokens that exist)
   - Is the terminal output clean? No tracebacks, no garbled text, no missing information?
   - Did the pipeline actually finish? Are there partial files or missing stages?

5. **If you find a problem:**
   - Trace it back through the source code to find the root cause
   - Fix the code
   - Re-run `./scripts/bootstrap.sh --sample --yes --clean`
   - Verify the fix resolved the issue
   - Check that the fix didn't introduce new problems

6. **Repeat until the bootstrap produces clean, spec-compliant output.**

7. **When done, commit the fixes:**
   ```bash
   git add -A && git commit -m "fix: <describe what was fixed>"
   ```

## What you are NOT doing

- You are NOT writing test files or assertions
- You are NOT checking specific code lines — you are checking the output holistically
- You are NOT running linters or type checkers (that's a separate step)
- You are NOT reading PRD.md — the OpenSpec archive is your reference

## Scope control

- If invoked with a change name (e.g., "debug-pass for p05-theming-model"), focus your inspection on the areas that change touches, but still run the full bootstrap
- If invoked without context, inspect everything
- If the tokens stage is skipped (no ANTHROPIC_API_KEY), that is expected — focus on stages that did run

## Judgment criteria

A clean pass means:
- The bootstrap script runs to completion without errors (or gracefully skips stages that require API keys)
- Every generated file is valid, complete, and matches the OpenSpec archive specifications
- No contradictions between files (e.g., profile says "enterprise-b2b" but tokens reflect consumer defaults)
- Terminal output is clean and informative
