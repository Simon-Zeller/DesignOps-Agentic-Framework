"""Unit tests for DTCGSchemaValidator tool — TDD red phase."""
from __future__ import annotations

import pytest


@pytest.fixture
def valid_token_dict():
    return {
        "color": {
            "brand": {
                "primary": {
                    "$type": "color",
                    "$value": "#005FCC",
                    "$description": "Primary brand colour",
                }
            }
        }
    }


def test_valid_dtcg_document_returns_empty_violations(valid_token_dict):
    """Returns {fatal: [], warnings: []} for a fully DTCG-compliant doc."""
    from daf.tools.dtcg_schema_validator import DTCGSchemaValidator

    result = DTCGSchemaValidator()._run(token_dict=valid_token_dict)
    assert result["fatal"] == []
    assert result["warnings"] == []


def test_missing_type_returns_fatal(valid_token_dict):
    """Token missing $type produces a fatal entry with the affected path."""
    from daf.tools.dtcg_schema_validator import DTCGSchemaValidator

    doc = {
        "color": {
            "brand": {
                "primary": {
                    "$value": "#005FCC",
                    # deliberately missing $type
                }
            }
        }
    }
    result = DTCGSchemaValidator()._run(token_dict=doc)
    assert len(result["fatal"]) >= 1
    # At least one fatal entry must contain the token path
    paths = [entry.get("token_path", "") for entry in result["fatal"]]
    assert any("color.brand.primary" in p for p in paths)


def test_unrecognised_extra_field_returns_warning(valid_token_dict):
    """Token with unknown field $foo produces a warning, not a fatal."""
    from daf.tools.dtcg_schema_validator import DTCGSchemaValidator

    doc = {
        "color": {
            "brand": {
                "primary": {
                    "$type": "color",
                    "$value": "#005FCC",
                    "$foo": "bar",  # unknown field
                }
            }
        }
    }
    result = DTCGSchemaValidator()._run(token_dict=doc)
    assert result["fatal"] == []
    assert len(result["warnings"]) >= 1
