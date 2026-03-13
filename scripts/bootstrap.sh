#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# DAF Bootstrap Script — run the DS pipeline from any stage for manual testing
#
# Usage:
#   ./scripts/bootstrap.sh                    # full run (interview → generate)
#   ./scripts/bootstrap.sh --from init        # start from interactive interview
#   ./scripts/bootstrap.sh --from generate    # skip interview, run Agent 1 + gate
#   ./scripts/bootstrap.sh --from tokens      # skip interview + Agent 1, generate tokens
#   ./scripts/bootstrap.sh --from resume-smoke    # verify --resume flag is wired (p09)
#   ./scripts/bootstrap.sh --profile <file>   # non-interactive: load profile, then generate
#   ./scripts/bootstrap.sh --sample           # create a sample profile, then generate
#
# Flags:
#   --yes           auto-approve Human Gate (skip interactive approval)
#   --workdir DIR   working directory for output (default: .daf-sandbox)
#   --clean         wipe workdir before starting
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Defaults ──────────────────────────────────────────────────────────────────
FROM_STAGE="init"
WORKDIR="$PROJECT_ROOT/.daf-sandbox"
PROFILE_PATH=""
SAMPLE=false
YES_FLAG=""
CLEAN=false

# ── Parse arguments ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)
      FROM_STAGE="$2"
      shift 2
      ;;
    --profile)
      PROFILE_PATH="$2"
      FROM_STAGE="generate"
      shift 2
      ;;
    --sample)
      SAMPLE=true
      FROM_STAGE="generate"
      shift
      ;;
    --yes)
      YES_FLAG="--yes"
      shift
      ;;
    --workdir)
      WORKDIR="$2"
      shift 2
      ;;
    --clean)
      CLEAN=true
      shift
      ;;
    -h|--help)
      head -17 "$0" | tail -14
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
info()  { echo "▸ $*"; }
ok()    { echo "✓ $*"; }
fail()  { echo "✗ $*" >&2; exit 1; }

require_profile() {
  if [[ ! -f "$WORKDIR/brand-profile.json" ]]; then
    fail "No brand-profile.json in $WORKDIR — run an earlier stage first or use --sample"
  fi
}

# ── Setup workdir ─────────────────────────────────────────────────────────────
if $CLEAN && [[ -d "$WORKDIR" ]]; then
  info "Cleaning $WORKDIR"
  rm -rf "$WORKDIR"
fi

mkdir -p "$WORKDIR"

# ── Sample profile ────────────────────────────────────────────────────────────
write_sample_profile() {
  cat > "$WORKDIR/brand-profile.json" << 'SAMPLE_JSON'
{
  "name": "Acme Design System",
  "archetype": "enterprise-b2b",
  "colors": {
    "primary": "#1a73e8",
    "secondary": "#34a853",
    "neutral": "#5f6368"
  },
  "typography": {
    "headingFont": "Inter",
    "bodyFont": "Inter",
    "monoFont": "Roboto Mono",
    "scaleRatio": 1.25,
    "baseSize": 16
  },
  "spacing": {
    "baseUnit": 8,
    "density": "default"
  },
  "borderRadius": "moderate",
  "elevation": "subtle",
  "motion": "standard",
  "themes": {
    "modes": ["light", "dark"]
  },
  "accessibility": "AA",
  "componentScope": "standard",
  "breakpoints": {
    "strategy": "mobile-first"
  }
}
SAMPLE_JSON
  ok "Sample brand-profile.json written to $WORKDIR"
}

# ── Stage: init (interactive interview) ──────────────────────────────────────
stage_init() {
  info "Stage: init — running interactive interview"
  cd "$WORKDIR"
  uv run --project "$PROJECT_ROOT" daf init
  ok "Interview complete — brand-profile.json written"
}

# ── Stage: generate (Agent 1 + Human Gate) ───────────────────────────────────
stage_generate() {
  require_profile
  info "Stage: generate — Brand Discovery Agent + Human Gate"
  cd "$WORKDIR"
  uv run --project "$PROJECT_ROOT" daf generate --profile "$WORKDIR/brand-profile.json" $YES_FLAG
  ok "Generate complete — enriched profile saved"
}

# ── Stage: tokens (Agent 2 — Token Foundation via CrewAI) ───────────────────
stage_tokens() {
  require_profile
  info "Stage: tokens — Token Foundation Agent (Agent 2) [requires ANTHROPIC_API_KEY]"

  if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    info "⚠  ANTHROPIC_API_KEY not set — skipping tokens stage"
    info "   Set it with: export ANTHROPIC_API_KEY=sk-ant-..."
    info "   Token generation requires a live LLM call via CrewAI."
    return 0
  fi

  cd "$WORKDIR"
  uv run --project "$PROJECT_ROOT" python -c "
import json, sys
from pathlib import Path
from daf.agents.brand_discovery import run_ds_bootstrap

profile_path = Path('$WORKDIR/brand-profile.json')
raw = json.loads(profile_path.read_text())

enriched, token_result = run_ds_bootstrap(raw, output_dir='$WORKDIR')

# Write the enriched profile back
profile_path.write_text(json.dumps(
    enriched.model_dump(by_alias=True, mode='json', exclude_none=True),
    indent=2,
))

print('Token generation complete.')
if token_result:
    files = getattr(token_result, 'files_written', None) or getattr(token_result, 'written_files', None) or []
    print(f'  Files written: {len(files)}')
    for f in files:
        print(f'    • {f}')
else:
    print('  (No structured output returned — check tokens/ directory)')
"
  ok "Tokens generated"
}

# ── Stage: resume-smoke (p09 — verify --resume flag is wired) ───────────────
stage_resume_smoke() {
  info "Stage: resume-smoke — verify daf init --resume handles a Phase 1 checkpoint correctly"

  local smoke_dir
  smoke_dir="$(mktemp -d)"
  trap 'rm -rf "$smoke_dir"' EXIT

  # Write a minimal brand-profile.json so CheckpointManager can create a valid manifest
  cat > "$smoke_dir/brand-profile.json" << 'RESUME_PROFILE'
{"name": "Smoke Test DS"}
RESUME_PROFILE

  # Create a Phase 1 checkpoint programmatically
  uv run --project "$PROJECT_ROOT" python -c "
from daf.tools.checkpoint_manager import CheckpointManager
cm = CheckpointManager()
cm.create(output_dir='$smoke_dir', phase=1)
print('Phase 1 checkpoint created.')
"

  # daf init --resume should find the Phase 1 checkpoint and exit 1 (no LLM available)
  # OR exit 0 if run_first_publish_agent is stubbed.  We only verify the flag is
  # recognised (no 'Unknown option' error) and it doesn't crash with exit 2.
  set +e
  uv run --project "$PROJECT_ROOT" daf init --resume "$smoke_dir" 2>&1 | head -3
  local exit_code=$?
  set -e

  if [[ $exit_code -eq 2 ]]; then
    fail "daf init --resume exited with code 2 (typer usage error) — flag not wired correctly"
  fi
  ok "resume-smoke complete (exit $exit_code — --resume flag is wired)"
}

# ── Stage: primitive-specs (Agent 3 — Primitive Scaffolding via PrimitiveSpecGenerator) ──
stage_primitive_specs() {
  info "Stage: primitive-specs — Primitive Scaffolding Agent (Agent 3) [deterministic, no LLM]"
  cd "$WORKDIR"
  uv run --project "$PROJECT_ROOT" python -c "
from daf.tools.primitive_spec_generator import generate_all_primitive_specs
result = generate_all_primitive_specs('$WORKDIR')
print(f'Generated {len(result)} primitive specs in $WORKDIR/specs/')
for name, path in result.items():
    print(f'  • {name}: {path}')
"
  ok "Primitive specs generated in $WORKDIR/specs/"
}

# ── Orchestrate from the chosen stage ────────────────────────────────────────
info "DAF Bootstrap — starting from stage: $FROM_STAGE"
info "Workdir: $WORKDIR"
echo ""

if $SAMPLE; then
  write_sample_profile
fi

if [[ -n "$PROFILE_PATH" ]]; then
  info "Copying profile from $PROFILE_PATH"
  cp "$PROFILE_PATH" "$WORKDIR/brand-profile.json"
  ok "Profile copied to workdir"
fi

case "$FROM_STAGE" in
  init)
    stage_init
    stage_generate
    stage_tokens
    stage_primitive_specs
    ;;
  generate)
    stage_generate
    stage_tokens
    stage_primitive_specs
    ;;
  tokens)
    stage_tokens
    stage_primitive_specs
    ;;
  primitive-specs)
    stage_primitive_specs
    ;;
  resume-smoke)
    stage_resume_smoke
    ;;
  *)
    fail "Unknown stage: $FROM_STAGE (valid: init, generate, tokens, primitive-specs, resume-smoke)"
    ;;
esac

echo ""
ok "Bootstrap complete. Output in $WORKDIR"
echo "  brand-profile.json   — enriched brand profile"
echo "  tokens/              — W3C DTCG token files (if generated)"
echo "  specs/               — primitive spec YAMLs (if generated)"
