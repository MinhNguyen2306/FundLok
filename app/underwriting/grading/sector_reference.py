"""Sector reference table loader + resolver (T3).

Spec: docs/specs/underwriting/sector-reference-table.md (ACCEPTED v1.0).

Supplies the seven per-industry values (six AI-graded sector factors plus
the Founder Experience constant) that the grading engine cannot compute
from an SME's own financials, from a versioned, replayable YAML file
rather than an inline LLM call.

R2 is the single most important constraint in the source spec: this module
is an ALTERNATIVE input source for production callers assembling a
`GradingInput`. It is never called inside `grade()`, `engine.py`,
`factors.py` or `rollup.py` -- the golden-set fixture supplies its own
per-row sector values, and reading this table inside the scoring path
would make all 10,000 regression rows stop reconciling.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

import yaml

_DEFAULT_SECTOR_REFERENCE_PATH = Path(__file__).parent / "params" / "sector_reference_v1.yaml"

# The six sector AI-score columns (score kind, 0-100). `cagr_pct` is
# deliberately excluded -- it is `kind: raw_percent` and must never be
# validated as a 0-100 score, nor merged into `ai_scores` (R4, "Resolution"
# acceptance criteria: "CAGR must not appear in ai_scores").
_SCORE_COLUMNS: Tuple[str, ...] = (
    "regulatory",
    "input_cost_vol",
    "cyclicality",
    "competitor",
    "macro",
    "uncontrollable",
)
_RAW_PERCENT_COLUMNS: Tuple[str, ...] = ("cagr_pct",)
_REQUIRED_COLUMNS: Tuple[str, ...] = _SCORE_COLUMNS + _RAW_PERCENT_COLUMNS
_REQUIRED_INDUSTRY_COUNT = 15


@dataclass(frozen=True)
class ColumnSpec:
    factor_id: int
    kind: str  # "score" | "raw_percent"
    valid_range: Tuple[float, float]


@dataclass(frozen=True)
class SectorReference:
    """A loaded, validated, immutable sector reference table."""

    sector_reference_version: str
    status: str  # "DRAFT_UNREVIEWED" | "REVIEWED"
    columns: Mapping[str, ColumnSpec]
    industries: Mapping[str, Mapping[str, float]]
    founder_constant: int

    @property
    def provisional(self) -> bool:
        return self.status != "REVIEWED"


def _freeze(obj: Any) -> Any:
    if isinstance(obj, dict):
        return MappingProxyType({k: _freeze(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return tuple(_freeze(v) for v in obj)
    return obj


def load_sector_reference(
    path: Optional[Path] = None,
    *,
    supported_industries: Optional[Tuple[str, ...]] = None,
) -> SectorReference:
    """Read, validate and freeze `sector_reference_v1.yaml`.

    Fails loudly at load time (R4/R5 error cases), never at scoring time:
    missing/extra industries, missing columns, out-of-range values, and (if
    `supported_industries` is given -- normally `load_params().supported_industries`)
    a name mismatch against the grading params' industry list.
    """
    resolved_path = Path(path) if path is not None else _DEFAULT_SECTOR_REFERENCE_PATH
    if not resolved_path.exists():
        raise FileNotFoundError(f"sector reference file not found: {resolved_path}")

    with open(resolved_path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    for key in ("sector_reference_version", "status", "columns", "industries", "constants"):
        if key not in raw:
            raise ValueError(f"sector reference YAML missing required key: {key!r}")

    raw_columns = raw["columns"]
    missing_columns = [c for c in _REQUIRED_COLUMNS if c not in raw_columns]
    if missing_columns:
        raise ValueError(f"sector reference YAML missing column spec(s): {missing_columns}")

    columns: dict[str, ColumnSpec] = {}
    for name in _REQUIRED_COLUMNS:
        col = raw_columns[name]
        kind = col["kind"]
        expected_kind = "score" if name in _SCORE_COLUMNS else "raw_percent"
        if kind != expected_kind:
            raise ValueError(f"column {name!r} has kind {kind!r}, expected {expected_kind!r}")
        valid_range = tuple(col["valid_range"])
        if len(valid_range) != 2:
            raise ValueError(f"column {name!r} valid_range must be [min, max], got {valid_range}")
        columns[name] = ColumnSpec(factor_id=col["factor_id"], kind=kind, valid_range=valid_range)

    industries_raw = raw["industries"]
    if len(industries_raw) != _REQUIRED_INDUSTRY_COUNT:
        raise ValueError(
            f"sector reference table has {len(industries_raw)} industries, "
            f"expected exactly {_REQUIRED_INDUSTRY_COUNT}"
        )

    if supported_industries is not None:
        expected = set(supported_industries)
        actual = set(industries_raw.keys())
        if expected != actual:
            only_in_table = sorted(actual - expected)
            only_in_params = sorted(expected - actual)
            raise ValueError(
                "sector reference industries do not match supported_industries exactly "
                f"(only in table: {only_in_table}, only in params: {only_in_params})"
            )

    industries: dict[str, dict[str, float]] = {}
    for industry_name, values in industries_raw.items():
        missing = [c for c in _REQUIRED_COLUMNS if c not in values]
        if missing:
            raise ValueError(f"industry {industry_name!r} is missing column(s): {missing}")
        row: dict[str, float] = {}
        for name in _REQUIRED_COLUMNS:
            value = float(values[name])
            lo, hi = columns[name].valid_range
            if not (lo <= value <= hi):
                raise ValueError(
                    f"industry {industry_name!r} column {name!r} = {value} outside "
                    f"valid_range [{lo}, {hi}]"
                )
            row[name] = value
        industries[industry_name] = row

    founder_constant = int(raw["constants"]["founder"])

    return SectorReference(
        sector_reference_version=raw["sector_reference_version"],
        status=raw["status"],
        columns=_freeze(columns),
        industries=_freeze(industries),
        founder_constant=founder_constant,
    )


def resolve_sector_inputs(industry: str, reference: SectorReference) -> Mapping[str, Any]:
    """Resolve one industry's sector inputs for assembling a `GradingInput`.

    Returns a frozen mapping:
        ai_scores               -- the 6 sector factors + founder, all 0-100
        sector_cagr_pct         -- raw percent, kept OUT of ai_scores (may be negative)
        sector_reference_version
        provisional             -- True while status is DRAFT_UNREVIEWED
    """
    if industry not in reference.industries:
        valid = sorted(reference.industries.keys())
        raise KeyError(f"industry {industry!r} not in sector reference table. Valid industries: {valid}")

    row = reference.industries[industry]
    ai_scores = {key: row[key] for key in _SCORE_COLUMNS}
    ai_scores["founder"] = float(reference.founder_constant)

    return MappingProxyType(
        {
            "ai_scores": MappingProxyType(ai_scores),
            "sector_cagr_pct": row["cagr_pct"],
            "sector_reference_version": reference.sector_reference_version,
            "provisional": reference.provisional,
        }
    )
