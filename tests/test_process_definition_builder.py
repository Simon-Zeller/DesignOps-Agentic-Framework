"""Tests for process_definition_builder tool (BaseTool)."""
from __future__ import annotations

import json


def test_process_definition_always_includes_required_rfc_triggers():
    """rfc_required_for always contains new_primitive and breaking_token_change."""
    from daf.tools.process_definition_builder import ProcessDefinitionBuilder

    builder = ProcessDefinitionBuilder()
    result = builder._run(workflow_config={})

    rfc_for = result["rfc_required_for"]
    assert "new_primitive" in rfc_for
    assert "breaking_token_change" in rfc_for


def test_process_definition_is_json_serializable():
    """ProcessDefinitionBuilder output is JSON-serializable."""
    from daf.tools.process_definition_builder import ProcessDefinitionBuilder

    builder = ProcessDefinitionBuilder()
    result = builder._run(workflow_config={"approval_required": True})
    json.dumps(result)  # should not raise
