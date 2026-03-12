#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# DAF Bootstrap Script — run the DS pipeline from any stage for manual testing
#
# Usage:
#   ./scripts/bootstrap.sh                    # full run (interview → generate)
#   ./scripts/bootstrap.sh --from init        # start from interactive interview
#   ./scripts/bootstrap.sh --from generate    # skip interview, run Agent 1 + gate
#   ./scripts/bootstrap.sh --from tokens      # skip interview + Agent 1, generate tokens
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
    "neutral": "#5f6368",
    "success": "#34a853",
    "warning": "#f9ab00",
    "error": "#ea4335",
    "info": "#4285f4"
  },
  "typography": {
    "fontFamily": "Inter",
    "headingFontFamily": "Inter",
    "scaleRatio": 1.25,
    "baseSize": 16
  },
  "spacing": {
    "baseUnit": 8,
    "density": "default"
  },
  "borderRadius": "md",
  "elevation": "subtle",
  "motion": "default",
  "themes": {
    "modes": ["light", "dark"],
    "default": "light"
  },
  "accessibility": "AA",
  "componentScope": "standard",
  "breakpoints": {
    "strategy": "mobile-first",
    "values": [640, 768, 1024, 1280]
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

# ── Stage: tokens (Agent 2 — Token Foundation) ──────────────────────────────
stage_tokens() {
  require_profile
  info "Stage: tokens — Token Foundation Agent (Agent 2)"
  cd "$WORKDIR"
  uv run --project "$PROJECT_ROOT" python -c "
import json, sys
from pathlib import Path
from daf.models import BrandProfile
from daf.agents.token_foundation import run_token_foundation

profile_path = Path('$WORKDIR/brand-profile.json')
raw = json.loads(profile_path.read_text())
profile = BrandProfile(**raw)

result = run_token_foundation(profile, output_dir=Path('$WORKDIR'))
print('Token generation complete.')
print(f'  Files written: {len(result.files_written)}')
for f in result.files_written:
    print(f'    • {f}')
"
  ok "Tokens generated"
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
    ;;
  generate)
    stage_generate
    stage_tokens
    ;;
  tokens)
    stage_tokens
    ;;
  *)
    fail "Unknown stage: $FROM_STAGE (valid: init, generate, tokens)"
    ;;
esac

echo ""
ok "Bootstrap complete. Output in $WORKDIR"
echo "  brand-profile.json   — enriched brand profile"
echo "  tokens/              — W3C DTCG token files (if generated)"
