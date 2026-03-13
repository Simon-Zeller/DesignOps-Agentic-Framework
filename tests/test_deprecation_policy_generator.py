"""Tests for deprecation_policy_generator tool."""
from __future__ import annotations


def test_grace_period_defaults_to_90_when_not_specified():
    """Grace period defaults to 90 when lifecycle_config has no gracePeriodDays."""
    from daf.tools.deprecation_policy_generator import generate

    result = generate({}, {})
    assert result["grace_period_days"] == 90


def test_grace_period_from_config():
    """Grace period is read from lifecycle_config gracePeriodDays."""
    from daf.tools.deprecation_policy_generator import generate

    lifecycle_config = {"defaultStatus": "stable", "gracePeriodDays": 60}
    result = generate(lifecycle_config, {})
    assert result["grace_period_days"] == 60


def test_migration_guide_required_when_default_status_is_stable():
    """migration_guide_required is True when defaultStatus is stable."""
    from daf.tools.deprecation_policy_generator import generate

    lifecycle_config = {"defaultStatus": "stable", "gracePeriodDays": 60}
    result = generate(lifecycle_config, {})
    assert result["migration_guide_required"] is True


def test_migration_guide_not_required_for_experimental():
    """migration_guide_required is False when defaultStatus is experimental."""
    from daf.tools.deprecation_policy_generator import generate

    lifecycle_config = {"defaultStatus": "experimental"}
    result = generate(lifecycle_config, {})
    assert result["migration_guide_required"] is False
