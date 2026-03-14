#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# DAF Bootstrap Script — run the DS pipeline from any stage for manual testing
#
# Usage:
#   ./scripts/bootstrap.sh                    # full run (interview → all stages)
#   ./scripts/bootstrap.sh --from init        # start from interactive interview
#   ./scripts/bootstrap.sh --from generate    # skip interview, run Agent 1 + gate
#   ./scripts/bootstrap.sh --from tokens      # skip interview + Agent 1, generate tokens
#   ./scripts/bootstrap.sh --from primitive-specs   # generate primitive spec YAMLs
#   ./scripts/bootstrap.sh --from core-specs  # generate core component spec YAMLs
#   ./scripts/bootstrap.sh --from pipeline-config   # generate pipeline-config.json + scaffolding
#   ./scripts/bootstrap.sh --from full-pipeline     # run 8-crew downstream pipeline (Agent 6)
#   ./scripts/bootstrap.sh --from resume-smoke      # verify --resume flag is wired (p09)
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

# ── Load .env if present ─────────────────────────────────────────────────────
if [[ -f "$PROJECT_ROOT/.env" ]]; then
  set -a
  source "$PROJECT_ROOT/.env"
  set +a
fi

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
import json, sys, os
from pathlib import Path

profile_path = Path('$WORKDIR/brand-profile.json')
raw = json.loads(profile_path.read_text())

# Step 1: Run Brand Discovery (Agent 1) via CrewAI for the enriched profile
from daf.agents.brand_discovery import (
    create_brand_discovery_agent,
    create_brand_discovery_task,
    BrandProfile,
)
from crewai import Crew

agent_t1 = create_brand_discovery_agent()
task_t1 = create_brand_discovery_task(raw)
task_t1.agent = agent_t1
crew_t1 = Crew(agents=[agent_t1], tasks=[task_t1], verbose=False)
result_t1 = crew_t1.kickoff()

enriched = getattr(result_t1, 'pydantic', None)
if enriched is None:
    raw_out = getattr(result_t1, 'raw', None)
    if raw_out:
        enriched = BrandProfile.model_validate(json.loads(raw_out))
if enriched is None:
    raise ValueError('Task T1 did not return a valid BrandProfile.')

# Write the enriched profile back
profile_path.write_text(json.dumps(
    enriched.model_dump(by_alias=True, mode='json', exclude_none=True),
    indent=2,
))
print('Brand profile enriched.')

# Step 2: Run the 4 token tools deterministically (bypass LLM hallucination)
from daf.tools.color_palette_generator import ColorPaletteGenerator
from daf.tools.modular_scale_calculator import ModularScaleCalculator
from daf.tools.contrast_safe_pairer import ContrastSafePairer
from daf.tools.dtcg_formatter import WC3DTCGFormatter

colors = {}
if enriched.colors:
    colors = {k: v for k, v in enriched.colors.model_dump().items() if v is not None}
color_notes = enriched.color_notes or {}
accessibility = enriched.accessibility or 'AA'
typo = None
if enriched.typography:
    typo = {k: v for k, v in enriched.typography.model_dump().items() if v is not None}
spacing = None
if enriched.spacing:
    spacing = {k: v for k, v in enriched.spacing.model_dump().items() if v is not None}
archetype = enriched.archetype or 'enterprise-b2b'
themes_modes = enriched.themes.modes if enriched.themes and enriched.themes.modes else []

# Tool 1: ColorPaletteGenerator
palette = ColorPaletteGenerator()._run(colors=colors, color_notes=color_notes)
print(f'  Tool 1 (ColorPaletteGenerator): {len(palette)} tokens')

# Tool 2: ModularScaleCalculator
scales = ModularScaleCalculator()._run(typography=typo, spacing=spacing, archetype=archetype)
print(f'  Tool 2 (ModularScaleCalculator): {len(scales)} tokens')

# Tool 3: ContrastSafePairer
overrides, pairs = ContrastSafePairer()._run(palette=palette, accessibility=accessibility)
print(f'  Tool 3 (ContrastSafePairer): {len(overrides)} overrides, {len(pairs)} contrast pairs')

# Tool 4: WC3DTCGFormatter
files = WC3DTCGFormatter()._run(
    global_palette=palette,
    scale_tokens=scales,
    semantic_overrides=overrides,
    component_overrides={},
    themes=themes_modes,
    output_dir='$WORKDIR',
)
print(f'Token generation complete.')
print(f'  Files written: {len(files)}')
for f in files:
    print(f'    \u2022 {f}')

# Verify files actually exist
for f in files:
    if not os.path.exists(f):
        print(f'  WARNING: {f} was not written!')
        sys.exit(1)
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

# ── Stage: core-component-specs (Agent 4 — Core Component via CoreComponentSpecGenerator) ──
stage_core_component_specs() {
  require_profile
  info "Stage: core-component-specs — Core Component Agent (Agent 4) [deterministic, no LLM]"
  cd "$WORKDIR"
  uv run --project "$PROJECT_ROOT" python -c "
import json
from pathlib import Path
from daf.tools.core_component_spec_generator import generate_component_specs

profile = json.loads(Path('$WORKDIR/brand-profile.json').read_text())
scope = profile.get('componentScope', 'starter')
result = generate_component_specs(scope, '$WORKDIR')
print(f'Generated {len(result)} core component specs (scope={scope}) in $WORKDIR/specs/')
for name, path in result.items():
    print(f'  • {name}: {path}')
"
  ok "Core component specs generated in $WORKDIR/specs/"
}

# ── Stage: pipeline-config (Agent 5 — Pipeline Config + Project Scaffolder) ─
stage_pipeline_config() {
  require_profile
  info "Stage: pipeline-config — Pipeline Configuration Agent (Agent 5) [deterministic, no LLM]"
  cd "$WORKDIR"
  uv run --project "$PROJECT_ROOT" python -c "
import json
from pathlib import Path
from daf.tools.config_generator import generate_pipeline_config
from daf.tools.project_scaffolder import scaffold_project_files

profile = json.loads(Path('$WORKDIR/brand-profile.json').read_text())
config_path = generate_pipeline_config(profile, '$WORKDIR')
print(f'  pipeline-config.json: {config_path}')
scaffolded = scaffold_project_files(profile, '$WORKDIR')
for name, path in scaffolded.items():
    print(f'  {name}: {path}')
"
  ok "Pipeline config and project scaffolding generated"
}

# ── Stage: full-pipeline (Agent 6 — First Publish Orchestrator + 8 Crews) ───
stage_full_pipeline() {
  require_profile
  info "Stage: full-pipeline — First Publish Agent (Agent 6) + 8-crew downstream pipeline"

  if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    info "⚠  ANTHROPIC_API_KEY not set — skipping full-pipeline stage"
    info "   The 8-crew downstream pipeline requires a live LLM via CrewAI."
    return 0
  fi

  cd "$WORKDIR"

  uv run --project "$PROJECT_ROOT" python -c "
import json
from daf.agents.first_publish import run_first_publish_agent

summary = run_first_publish_agent('$WORKDIR')
print(json.dumps(summary, indent=2))
"
  ok "Full pipeline complete"
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
    stage_core_component_specs
    stage_pipeline_config
    stage_full_pipeline
    ;;
  generate)
    stage_generate
    stage_tokens
    stage_primitive_specs
    stage_core_component_specs
    stage_pipeline_config
    stage_full_pipeline
    ;;
  tokens)
    stage_tokens
    stage_primitive_specs
    stage_core_component_specs
    stage_pipeline_config
    stage_full_pipeline
    ;;
  primitive-specs)
    stage_primitive_specs
    stage_core_component_specs
    stage_pipeline_config
    stage_full_pipeline
    ;;
  core-specs)
    stage_core_component_specs
    stage_pipeline_config
    stage_full_pipeline
    ;;
  pipeline-config)
    stage_pipeline_config
    stage_full_pipeline
    ;;
  full-pipeline)
    stage_full_pipeline
    ;;
  resume-smoke)
    stage_resume_smoke
    ;;
  *)
    fail "Unknown stage: $FROM_STAGE (valid: init, generate, tokens, primitive-specs, core-specs, pipeline-config, full-pipeline, resume-smoke)"
    ;;
esac

echo ""
ok "Bootstrap complete. Output in $WORKDIR"
echo "  brand-profile.json   — enriched brand profile"
echo "  tokens/              — W3C DTCG token files (if generated)"
echo "  specs/               — primitive + core component spec YAMLs"
echo "  pipeline-config.json — pipeline configuration"
echo "  src/                 — generated TypeScript/TSX components"
echo "  docs/                — component docs, token catalog, ADRs"
echo "  governance/          — ownership, workflow, quality gates"
echo "  registry/            — AI-consumable component + token registry"
echo "  reports/             — quality reports, exit criteria"
