"""DS Bootstrap Crew agents."""
from daf.agents.brand_discovery import (
    create_brand_discovery_agent,
    create_brand_discovery_task,
    run_brand_discovery,
    run_ds_bootstrap,
)
from daf.agents.token_foundation import (
    create_token_foundation_agent,
    create_token_foundation_task,
)
from daf.agents.primitive_scaffolding import (
    create_primitive_scaffolding_agent,
    create_primitive_scaffolding_task,
)
from daf.agents.core_component import (
    create_core_component_agent,
    create_core_component_task,
)
from daf.agents.pipeline_config import (
    create_pipeline_config_agent,
    create_pipeline_config_task,
)
from daf.agents.token_ingestion import (
    create_token_ingestion_agent,
    create_token_ingestion_task,
)
from daf.agents.token_validation import (
    create_token_validation_agent,
    create_token_validation_task,
)
from daf.agents.token_compilation import (
    create_token_compilation_agent,
    create_token_compilation_task,
)
from daf.agents.token_integrity import (
    create_token_integrity_agent,
    create_token_integrity_task,
)
from daf.agents.token_diff import (
    create_token_diff_agent,
    create_token_diff_task,
)

__all__ = [
    "create_brand_discovery_agent",
    "create_brand_discovery_task",
    "run_brand_discovery",
    "run_ds_bootstrap",
    "create_token_foundation_agent",
    "create_token_foundation_task",
    "create_primitive_scaffolding_agent",
    "create_primitive_scaffolding_task",
    "create_core_component_agent",
    "create_core_component_task",
    "create_pipeline_config_agent",
    "create_pipeline_config_task",
    "create_token_ingestion_agent",
    "create_token_ingestion_task",
    "create_token_validation_agent",
    "create_token_validation_task",
    "create_token_compilation_agent",
    "create_token_compilation_task",
    "create_token_integrity_agent",
    "create_token_integrity_task",
    "create_token_diff_agent",
    "create_token_diff_task",
]

from daf.agents.spec_validation import run_spec_validation
from daf.agents.composition import run_composition_check
from daf.agents.accessibility import run_accessibility_enforcement
from daf.agents.quality_scoring import run_quality_scoring
from daf.agents.doc_generation import run_doc_generation
from daf.agents.token_catalog import run_token_catalog
from daf.agents.generation_narrative import run_generation_narrative
from daf.agents.decision_record import run_decision_records
from daf.agents.search_index import run_search_index
from daf.agents.usage_tracking import create_usage_tracking_agent
from daf.agents.token_compliance_agent import create_token_compliance_agent
from daf.agents.drift_detection import create_drift_detection_agent
from daf.agents.pipeline_completeness import create_pipeline_completeness_agent
from daf.agents.breakage_correlation import create_breakage_correlation_agent
from daf.agents.registry_maintenance import create_registry_maintenance_agent
from daf.agents.token_resolution import create_token_resolution_agent
from daf.agents.composition_constraint import create_composition_constraint_agent
from daf.agents.validation_rule import create_validation_rule_agent
from daf.agents.context_serializer import create_context_serializer_agent
from daf.agents.semver import create_semver_agent
from daf.agents.release_changelog import create_release_changelog_agent
from daf.agents.codemod import create_codemod_agent
from daf.agents.publish import create_publish_agent
from daf.agents.rollback import create_rollback_agent

__all__ += [
    "run_spec_validation",
    "run_composition_check",
    "run_accessibility_enforcement",
    "run_quality_scoring",
    "run_doc_generation",
    "run_token_catalog",
    "run_generation_narrative",
    "run_decision_records",
    "run_search_index",
    "create_usage_tracking_agent",
    "create_token_compliance_agent",
    "create_drift_detection_agent",
    "create_pipeline_completeness_agent",
    "create_breakage_correlation_agent",
    "create_registry_maintenance_agent",
    "create_token_resolution_agent",
    "create_composition_constraint_agent",
    "create_validation_rule_agent",
    "create_context_serializer_agent",
    "create_semver_agent",
    "create_release_changelog_agent",
    "create_codemod_agent",
    "create_publish_agent",
    "create_rollback_agent",
]
