"""DeprecationPolicyGenerator — template-driven deprecation policy from lifecycle config.

Generates a ``deprecation-policy.json`` structure from the ``lifecycle`` section
of ``pipeline-config.json``.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

_DEFAULT_GRACE_PERIOD = 90


def generate(
    lifecycle_config: dict[str, Any],
    component_statuses: dict[str, str],
) -> dict[str, Any]:
    """Generate a deprecation policy dict from a lifecycle configuration.

    Args:
        lifecycle_config: The ``lifecycle`` section of ``pipeline-config.json``.
            Recognised keys: ``gracePeriodDays``, ``defaultStatus``.
        component_statuses: Mapping of component name → stability status
            (used for reporting; not currently included in output).

    Returns:
        Deprecation policy dict with keys ``grace_period_days`` and
        ``migration_guide_required``.
    """
    grace_period = int(lifecycle_config.get("gracePeriodDays", _DEFAULT_GRACE_PERIOD))
    default_status = lifecycle_config.get("defaultStatus", "beta")
    migration_guide_required = default_status == "stable"

    return {
        "grace_period_days": grace_period,
        "migration_guide_required": migration_guide_required,
        "default_status": default_status,
    }


class _PolicyInput(BaseModel):
    lifecycle_config: dict[str, Any]
    component_statuses: dict[str, str]


class DeprecationPolicyGenerator(BaseTool):
    """Generate a deprecation policy from lifecycle config."""

    name: str = "deprecation_policy_generator"
    description: str = (
        "Generates a deprecation policy dict from pipeline-config lifecycle settings "
        "including grace period and migration guide requirements."
    )
    args_schema: type[BaseModel] = _PolicyInput

    def _run(
        self,
        lifecycle_config: dict[str, Any],
        component_statuses: dict[str, str],
        **kwargs: Any,
    ) -> dict[str, Any]:
        return generate(lifecycle_config, component_statuses)
