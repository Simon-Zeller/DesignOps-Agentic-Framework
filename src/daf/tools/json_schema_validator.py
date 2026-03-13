"""JSON Schema Validator — validates spec dicts against JSON Schema definitions."""
from __future__ import annotations

from typing import Any

import jsonschema


def validate_spec_schema(
    spec_dict: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    """Validate *spec_dict* against *schema* using jsonschema.

    Returns:
        ``{"valid": True, "errors": []}`` on success, or
        ``{"valid": False, "errors": [{"field": ..., "message": ...}, ...]}`` on failure.
    """
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(spec_dict))

    if not errors:
        return {"valid": True, "errors": []}

    structured: list[dict[str, str]] = []
    for err in errors:
        field = ".".join(str(p) for p in err.absolute_path) if err.absolute_path else err.validator_value
        if err.validator == "required":
            # err.message like "'variants' is a required property"
            missing = err.message.split("'")[1] if "'" in err.message else str(err.validator_value)
            structured.append({"field": missing, "message": "required field missing"})
        else:
            structured.append({
                "field": str(field) if field else err.validator,
                "message": err.message,
            })

    return {"valid": False, "errors": structured}
