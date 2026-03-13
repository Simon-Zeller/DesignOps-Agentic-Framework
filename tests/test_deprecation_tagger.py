"""Unit tests for DeprecationTagger tool — TDD red phase."""
from __future__ import annotations

import pytest


def test_injects_deprecated_extension_into_token():
    """Tags token with $extensions.com.daf.deprecated containing since and reason."""
    from daf.tools.deprecation_tagger import DeprecationTagger

    token_dict = {
        "color": {
            "brand": {
                "accent": {
                    "$type": "color",
                    "$value": "#FF6600",
                }
            }
        }
    }
    metadata = {"since": "1.0.0", "reason": "Replaced by color.brand.secondary"}
    result = DeprecationTagger()._run(
        token_dict=token_dict,
        path="color.brand.accent",
        metadata=metadata,
    )
    tagged = result["color"]["brand"]["accent"]
    assert "$extensions" in tagged
    assert "com.daf.deprecated" in tagged["$extensions"]
    dep = tagged["$extensions"]["com.daf.deprecated"]
    assert dep["since"] == "1.0.0"
    assert dep["reason"] == "Replaced by color.brand.secondary"


def test_deprecated_tokens_still_present_in_compiled_output(tmp_path):
    """Tokens tagged deprecated are NOT removed from the dict."""
    from daf.tools.deprecation_tagger import DeprecationTagger

    token_dict = {
        "color": {
            "brand": {
                "accent": {
                    "$type": "color",
                    "$value": "#FF6600",
                }
            }
        }
    }
    metadata = {"since": "1.0.0", "reason": "Deprecated"}
    result = DeprecationTagger()._run(
        token_dict=token_dict,
        path="color.brand.accent",
        metadata=metadata,
    )
    # Token key must still exist
    assert "accent" in result["color"]["brand"]
    assert result["color"]["brand"]["accent"]["$value"] == "#FF6600"
