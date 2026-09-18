"""Grading engine core -- deterministic 22-factor SME risk grade.

Spec: docs/specs/underwriting/grading-engine-core.md (ACCEPTED v1.0).

Public surface:

    from app.underwriting.grading import grade, load_params, GradingInput, GradingResult

    params = load_params()                    # or load_params(path=...) in tests
    result: GradingResult = grade(inputs, params)

This package imports nothing from `app/` and performs no I/O other than
`load_params()` reading the YAML (R1). It is a pure library, not a service --
see R1 in the spec for why every function here is a plain `def`, never
`async def`.
"""
from .engine import grade
from .params import FactorParam, GateParam, ParamSet, load_params
from .sector_reference import SectorReference, load_sector_reference, resolve_sector_inputs
from .types import GateResult, GradingInput, GradingResult

__all__ = [
    "grade",
    "load_params",
    "ParamSet",
    "FactorParam",
    "GateParam",
    "GradingInput",
    "GradingResult",
    "GateResult",
    "SectorReference",
    "load_sector_reference",
    "resolve_sector_inputs",
]
