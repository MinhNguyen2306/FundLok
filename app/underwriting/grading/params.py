"""Loader for `params/grading_params_v1.yaml`.

Spec: docs/specs/underwriting/grading-engine-core.md, R2 -- the YAML is the
source of truth. Nothing in this module retypes a constant from the YAML; it
only parses it into a frozen, in-memory structure and fails loudly if the file
doesn't look like what the rest of the package expects.

`load_params()` is the one place in this package that touches disk (R1). It
reads the file once per call and returns an immutable `ParamSet`; `grade()`
itself never opens anything.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

import yaml

_DEFAULT_PARAMS_PATH = Path(__file__).parent / "params" / "grading_params_v1.yaml"

_REQUIRED_TOP_LEVEL_KEYS = (
    "engine_version",
    "params_version",
    "source_workbook",
    "source_tab",
    "factor_count",
    "derivations",
    "factors",
    "rollup",
    "final_grade",
    "pricing",
    "repayment",
    "gates",
    "excluded_industries",
    "supported_industries",
    "company_sizes",
    "loan_constraints",
    "decision_states",
)


@dataclass(frozen=True)
class FactorParam:
    """One row of `factors:` in the YAML. Not every field applies to every
    `kind` -- e.g. `upper`/`steepness`/`intercept`/`decreasing` only mean
    something for `kind: sigmoid`, `a`/`b`/`c`/`d` only for `kind: cubic`.
    Unused fields are `None`."""

    id: int
    key: str
    group: str
    kind: str  # "sigmoid" | "linear" | "cubic" | "supplied"

    input: Optional[str] = None
    input_unit: Optional[str] = None

    # sigmoid
    upper: Optional[float] = None
    steepness: Optional[float] = None
    intercept: Optional[float] = None
    decreasing: Optional[bool] = None

    # linear
    formula: Optional[str] = None

    # applied to the raw input before scoring, e.g. a percent -> decimal scale
    scale_input_by: Optional[float] = None

    # cubic: score = a*x^3 + b*x^2 + c*x + d
    a: Optional[float] = None
    b: Optional[float] = None
    c: Optional[float] = None
    d: Optional[float] = None

    bonus: bool = False


@dataclass(frozen=True)
class GateParam:
    id: int
    key: str
    severity: str  # "hard" | "soft" | "none"
    rule: str
    enabled: bool = True
    threshold: Optional[float] = None


@dataclass(frozen=True)
class ParamSet:
    engine_version: str
    params_version: str
    source_workbook: str
    source_tab: str
    factor_count: int

    derivations: Mapping[str, str]
    factors: Tuple[FactorParam, ...]

    # {group: {"core": {factor_key: weight}, "bonus": {factor_key: weight}}}
    rollup: Mapping[str, Mapping[str, Mapping[str, float]]]
    final_grade: Mapping[str, float]

    pricing: Mapping[str, float]
    repayment: Mapping[str, float]

    gates: Tuple[GateParam, ...]
    excluded_industries: Tuple[str, ...]
    supported_industries: Tuple[str, ...]
    company_sizes: Mapping[str, Mapping[str, int]]
    loan_constraints: Mapping[str, Any]
    decision_states: Tuple[str, ...]


def _freeze(obj: Any) -> Any:
    """Recursively convert dict -> MappingProxyType and list -> tuple so that
    no container reachable from a `ParamSet` can be mutated in place."""
    if isinstance(obj, dict):
        return MappingProxyType({k: _freeze(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return tuple(_freeze(v) for v in obj)
    return obj


def _build_factor(raw: Mapping[str, Any]) -> FactorParam:
    known = {f.name for f in FactorParam.__dataclass_fields__.values()}
    extra = set(raw) - known
    if extra:
        raise ValueError(f"Unknown key(s) on factor {raw.get('key')!r}: {sorted(extra)}")
    return FactorParam(**raw)


def _build_gate(raw: Mapping[str, Any]) -> GateParam:
    known = {f.name for f in GateParam.__dataclass_fields__.values()}
    extra = set(raw) - known
    if extra:
        raise ValueError(f"Unknown key(s) on gate {raw.get('key')!r}: {sorted(extra)}")
    return GateParam(**raw)


def load_params(path: Optional[Path] = None) -> ParamSet:
    """Read and validate `grading_params_v1.yaml`.

    Fails loudly (rather than silently proceeding on drift) if: a required
    top-level key is missing, `factor_count` disagrees with the number of
    `factors` entries, or a factor/gate row carries a key this loader doesn't
    recognise.
    """
    resolved_path = Path(path) if path is not None else _DEFAULT_PARAMS_PATH
    with open(resolved_path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    missing = [key for key in _REQUIRED_TOP_LEVEL_KEYS if key not in raw]
    if missing:
        raise ValueError(f"grading params YAML missing required key(s): {missing}")

    factors = tuple(_build_factor(f) for f in raw["factors"])
    if raw["factor_count"] != len(factors):
        raise ValueError(
            f"factor_count ({raw['factor_count']}) does not match number of "
            f"factors entries ({len(factors)}) -- params file has drifted"
        )

    gates = tuple(_build_gate(g) for g in raw["gates"])

    return ParamSet(
        engine_version=raw["engine_version"],
        params_version=raw["params_version"],
        source_workbook=raw["source_workbook"],
        source_tab=raw["source_tab"],
        factor_count=raw["factor_count"],
        derivations=_freeze(raw["derivations"]),
        factors=factors,
        rollup=_freeze(raw["rollup"]),
        final_grade=_freeze(raw["final_grade"]),
        pricing=_freeze(raw["pricing"]),
        repayment=_freeze(raw["repayment"]),
        gates=gates,
        excluded_industries=tuple(raw["excluded_industries"]),
        supported_industries=tuple(raw["supported_industries"]),
        company_sizes=_freeze(raw["company_sizes"]),
        loan_constraints=_freeze(raw["loan_constraints"]),
        decision_states=tuple(raw["decision_states"]),
    )
