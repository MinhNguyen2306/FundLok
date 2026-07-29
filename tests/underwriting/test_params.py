"""Params loader -- frozen structure, drift guard.

Spec: docs/specs/underwriting/grading-engine-core.md, R2, section 8.
"""
import dataclasses

import pytest


def test_params_load_and_freeze(params):
    assert params.factor_count == 22
    assert len(params.factors) == 22

    with pytest.raises(dataclasses.FrozenInstanceError):
        params.engine_version = "9.9.9"

    with pytest.raises(dataclasses.FrozenInstanceError):
        params.factors[0].upper = 999.0

    with pytest.raises(TypeError):
        params.rollup["bcq"]["core"]["gross_margin"] = 0.99

    with pytest.raises(TypeError):
        params.company_sizes["micro"]["max"] = 999


def test_params_version_pinned(params):
    # Guards silent YAML drift -- if this ever changes, every test that
    # reconciles against the golden set needs to be re-verified against a
    # freshly-extracted fixture before the version bump is trusted.
    assert params.params_version == "wb-v0-20260728"
    assert params.engine_version == "1.0.0"
