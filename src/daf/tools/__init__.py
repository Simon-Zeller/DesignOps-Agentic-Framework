"""DAF tools — deterministic CrewAI BaseTool implementations."""
from daf.tools.archetype_resolver import ArchetypeResolver
from daf.tools.brand_profile_validator import BrandProfileSchemaValidator
from daf.tools.color_palette_generator import ColorPaletteGenerator
from daf.tools.consistency_checker import ConsistencyChecker
from daf.tools.contrast_safe_pairer import ContrastSafePairer
from daf.tools.core_component_spec_generator import (
    CoreComponentSpecGenerator,
    generate_component_specs,
)
from daf.tools.default_filler import DefaultFiller
from daf.tools.dtcg_formatter import WC3DTCGFormatter
from daf.tools.modular_scale_calculator import ModularScaleCalculator
from daf.tools.config_generator import ConfigGenerator
from daf.tools.project_scaffolder import ProjectScaffolder
from daf.tools.primitive_registry import is_primitive, get_all_primitives
from daf.tools.json_schema_validator import validate_spec_schema
from daf.tools.token_ref_checker import check_token_refs
from daf.tools.state_machine_validator import validate_state_machine
from daf.tools.composition_rule_engine import check_composition, compute_token_compliance
from daf.tools.nesting_validator import validate_nesting
from daf.tools.aria_generator import generate_aria_patches
from daf.tools.keyboard_nav_scaffolder import scaffold_keyboard_handlers
from daf.tools.focus_trap_validator import validate_focus_trap
from daf.tools.coverage_reporter import get_coverage
from daf.tools.score_calculator import calculate_score
from daf.tools.threshold_gate import apply_gate, gate_components

__all__ = [
    "ArchetypeResolver",
    "BrandProfileSchemaValidator",
    "ColorPaletteGenerator",
    "ConsistencyChecker",
    "ContrastSafePairer",
    "CoreComponentSpecGenerator",
    "DefaultFiller",
    "WC3DTCGFormatter",
    "ModularScaleCalculator",
    "generate_component_specs",
    "ConfigGenerator",
    "ProjectScaffolder",
    "is_primitive",
    "get_all_primitives",
    "validate_spec_schema",
    "check_token_refs",
    "validate_state_machine",
    "check_composition",
    "compute_token_compliance",
    "validate_nesting",
    "generate_aria_patches",
    "scaffold_keyboard_handlers",
    "validate_focus_trap",
    "get_coverage",
    "calculate_score",
    "apply_gate",
    "gate_components",
]
