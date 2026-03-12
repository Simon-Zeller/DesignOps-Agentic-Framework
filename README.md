# DAF Local — DesignOps Agentic Framework

AI-orchestrated design system generation pipeline. Provide a brand profile and let the agent crews generate a complete, token-driven component library.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | ≥ 3.11 | Required by the CrewAI orchestration layer |
| Node.js | ≥ 18 | Required for downstream output (Vite build, Vitest, Storybook) |
| `ANTHROPIC_API_KEY` | — | Anthropic API key for Claude model tiers |

---

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd daf

# 2. Create and activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows (PowerShell)

# 3. Install the package with dev dependencies
pip install -e ".[dev]"

# 4. Configure environment variables
cp .env.example .env
# Open .env and set ANTHROPIC_API_KEY=<your-key>
```

---

## First Run

```bash
daf init
```

This starts the interactive brand interview (11-step Q&A) which collects brand information and queues the generation pipeline.

**Non-interactive mode** (skip the interview, use a pre-written Brand Profile):

```bash
daf init --profile ./my-brand-profile.json
```

**Resume an interrupted run** (continue from the last completed step):

```bash
daf init --resume ./output-dir
```

---

## CLI Reference

```
daf --help          Top-level help (lists all commands)
daf init --help     Init subcommand help (flags, descriptions)
```

---

## Environment Variables

See `.env.example` for all supported variables. The minimum required variable is `ANTHROPIC_API_KEY`.

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | API key for Anthropic Claude (used by all agent tiers) |
| `DAF_LOG_LEVEL` | No | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`) |

---

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=daf --cov-report=term-missing

# Lint
ruff check src/ tests/

# Type check
mypy src/daf/
```

---

## Project Structure

```
src/daf/
├── __init__.py     # Package init — exports __version__
├── cli.py          # Typer CLI entry point (daf command)
├── crews/          # CrewAI Crew definitions (added in P03–P09)
├── agents/         # CrewAI Agent definitions (added in P03–P09)
└── tools/          # CrewAI Tool definitions (added in P03–P09)

tests/
├── test_package.py           # Import and version tests
├── test_cli_entrypoint.py    # Subprocess-level smoke tests
└── test_cli_init.py          # Unit tests for daf init command
```
