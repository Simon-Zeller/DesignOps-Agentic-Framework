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
from daf.tools.spec_to_doc_renderer import render_spec_to_sections
from daf.tools.prop_table_generator import generate_prop_table
from daf.tools.example_code_generator import generate_example_stub
from daf.tools.readme_template import render_readme
from daf.tools.token_value_resolver import resolve_token, classify_tier
from daf.tools.scale_visualizer import visualize_token
from daf.tools.usage_context_extractor import extract_usage_context
from daf.tools.decision_log_reader import read_decisions
from daf.tools.brand_profile_analyzer import analyze_brand_profile
from daf.tools.prose_generator import build_narrative_prompt
from daf.tools.decision_extractor import extract_decisions
from daf.tools.adr_template_generator import generate_adr, slugify_title
from daf.tools.search_index_builder import build_index_entries
from daf.tools.metadata_tagger import tag_entry
from daf.tools.ast_import_scanner import ASTImportScanner
from daf.tools.token_usage_mapper import TokenUsageMapper
from daf.tools.structural_comparator import StructuralComparator
from daf.tools.drift_reporter import DriftReporter
from daf.tools.doc_patcher import DocPatcher
from daf.tools.pipeline_stage_tracker import PipelineStageTracker
from daf.tools.dependency_chain_walker import DependencyChainWalker
from daf.tools.token_compliance_scanner import TokenComplianceScannerTool
from daf.tools.spec_indexer import SpecIndexer
from daf.tools.example_code_generator import ExampleCodeGenerator
from daf.tools.registry_builder import RegistryBuilder
from daf.tools.token_graph_traverser import TokenGraphTraverser
from daf.tools.semantic_mapper import SemanticMapper
from daf.tools.composition_rule_extractor import CompositionRuleExtractor
from daf.tools.tree_validator import TreeValidator
from daf.tools.rule_compiler import RuleCompiler
from daf.tools.context_formatter import ContextFormatter
from daf.tools.token_budget_optimizer import TokenBudgetOptimizer
from daf.tools.multi_format_serializer import MultiFormatSerializer

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
    "render_spec_to_sections",
    "generate_prop_table",
    "generate_example_stub",
    "render_readme",
    "resolve_token",
    "classify_tier",
    "visualize_token",
    "extract_usage_context",
    "read_decisions",
    "analyze_brand_profile",
    "build_narrative_prompt",
    "extract_decisions",
    "generate_adr",
    "slugify_title",
    "build_index_entries",
    "tag_entry",
    "ASTImportScanner",
    "TokenUsageMapper",
    "StructuralComparator",
    "DriftReporter",
    "DocPatcher",
    "PipelineStageTracker",
    "DependencyChainWalker",
    "TokenComplianceScannerTool",
    "SpecIndexer",
    "ExampleCodeGenerator",
    "RegistryBuilder",
    "TokenGraphTraverser",
    "SemanticMapper",
    "CompositionRuleExtractor",
    "TreeValidator",
    "RuleCompiler",
    "ContextFormatter",
    "TokenBudgetOptimizer",
    "MultiFormatSerializer",
]
