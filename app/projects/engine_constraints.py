"""Grading-engine constraints, for validating an SME application at the API edge.

The grading core validates its own inputs and raises `ValueError` on an
industry it does not know, a loan outside `loan_constraints`, or a term that is
not one of `allowed_durations_months` (see
`docs/specs/underwriting/grading-engine-core.md` §7). Those raises are correct
for the engine, but reaching them means an application was already accepted and
stored in a shape that can never be graded — and the applicant found out much
later, via an admin, instead of at the field they typed it in.

So the same rules are enforced when the application is created. Every value
here is read from `grading_params_v1.yaml` through `load_params()`; nothing is
retyped, so a params change cannot silently diverge from what the API accepts.
See `docs/specs/underwriting/grading-input-sources.md` §6.4.

`load_params()` reads the YAML from disk, so it is cached here — validation runs
on every create request and the params file only changes on deploy.
"""
from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from typing import Optional

from app.underwriting.grading import ParamSet, load_params


@lru_cache(maxsize=1)
def params() -> ParamSet:
    """The loaded grading params. Cached for process lifetime — the file is
    read-only at runtime and version-stamped into every score run."""
    return load_params()


def allowed_industries() -> tuple[str, ...]:
    """Supported plus excluded.

    Excluded industries (gambling, alcohol, tobacco, weapons, defence) are
    accepted here on purpose, exactly as `grade()` accepts them: they are
    *recognised* industries that gate 5 rejects after grading, which produces an
    auditable REJECT rather than a validation error. An industry in neither list
    is a typo or a stale client, and that is what this rejects.
    """
    p = params()
    return tuple(p.supported_industries) + tuple(p.excluded_industries)


def validate_industry(value: Optional[str]) -> Optional[str]:
    """Nullable by design: `projects.industry` is nullable and pre-dates the
    grading engine, so an existing client that omits it must keep working. A
    project without an industry simply cannot be graded — the ingest layer
    surfaces that, not this validator."""
    if value is None:
        return None
    industry = value.strip()
    if not industry:
        return None
    if industry not in allowed_industries():
        raise ValueError(
            f"industry {industry!r} is not one of the "
            f"{len(params().supported_industries)} industries the grading "
            "engine supports"
        )
    return industry


def validate_loan_size(value: Decimal) -> Decimal:
    constraints = params().loan_constraints
    minimum = Decimal(str(constraints["min_vnd"]))
    maximum = Decimal(str(constraints["max_vnd"]))
    if not (minimum <= value <= maximum):
        raise ValueError(
            f"requested_amount must be between {minimum:,.0f} and "
            f"{maximum:,.0f} VND"
        )
    return value


def validate_duration_months(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    allowed = tuple(params().loan_constraints["allowed_durations_months"])
    if value not in allowed:
        raise ValueError(
            f"duration_months must be one of {', '.join(str(a) for a in allowed)}"
        )
    return value


def company_size_bands() -> dict[str, dict[str, int]]:
    return {size: dict(band) for size, band in params().company_sizes.items()}


def company_size_for_headcount(count: int) -> Optional[str]:
    """The band a headcount falls in, or None when it is outside every band.

    Derived server-side rather than trusted from the client: the bands live in
    the params file, so the mapping belongs next to it (input-sources spec
    §6.3). A headcount above the largest band has no honest answer — the engine
    only knows micro/small/medium — so it is a validation error, not a
    silent promotion to "medium".
    """
    for size, band in company_size_bands().items():
        if band["min"] <= count <= band["max"]:
            return size
    return None


def validate_employee_count(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    if company_size_for_headcount(value) is None:
        bands = company_size_bands()
        floor = min(band["min"] for band in bands.values())
        ceiling = max(band["max"] for band in bands.values())
        raise ValueError(
            f"employee_count must be between {floor} and {ceiling} — the "
            "grading engine has no company_size band outside that range"
        )
    return value
