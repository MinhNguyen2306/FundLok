"""22 factor scores.

Spec: docs/specs/underwriting/grading-engine-core.md, R2, R3, R8.
"""
from __future__ import annotations

from typing import Dict, Mapping, Optional

from . import curves
from .params import FactorParam, ParamSet
from .types import GradingInput

# The seven AI-graded factors (R3). Their `kind` in the params file is
# "supplied": the core never calls an AI service, it just reads a
# already-committed 0-100 number out of `GradingInput.ai_scores`. Absence of
# any of these is what drives `AI_PENDING` (R8), computed by engine.py from
# `factor_scores` using this same key set.
AI_SCORE_KEYS = frozenset(
    {
        "regulatory",
        "input_cost_vol",
        "cyclicality",
        "competitor",
        "macro",
        "uncontrollable",
        "founder",
    }
)

__all__ = ["AI_SCORE_KEYS", "score_factor", "score_all_factors"]


def _raw_value(
    factor: FactorParam,
    inputs: GradingInput,
    derived: Mapping[str, Optional[float]],
) -> Optional[float]:
    """Resolve the raw x that feeds a factor's curve. AI-graded factors read
    `ai_scores`; everything else is either a `GradingInput` field the
    derivation layer doesn't touch (concentration, sector CAGR, CIC), or a
    key in the `derived` mapping produced by `derive.compute_derived`."""
    if factor.kind == "supplied":
        return inputs.ai_scores.get(factor.key)

    if factor.key == "owner_withdrawal":
        # D22 (deviations register): the params file models this as a cubic
        # over a 0-1 raw ratio, but production/golden-set input supplies it
        # as an already-computed 0-100 score. See the note in score_factor().
        return inputs.owner_withdrawal

    direct_inputs: Dict[str, Optional[float]] = {
        "conc_top1_pct": inputs.conc_top1_pct,
        "conc_top3_pct": inputs.conc_top3_pct,
        "sector_cagr_pct": inputs.sector_cagr_pct,
        "cic_score": None if inputs.cic_score is None else float(inputs.cic_score),
    }
    if factor.input in direct_inputs:
        return direct_inputs[factor.input]

    return derived.get(factor.input)


def score_factor(
    factor: FactorParam,
    inputs: GradingInput,
    derived: Mapping[str, Optional[float]],
) -> Optional[float]:
    """Score one factor. Returns `None` when the factor isn't scorable
    (missing AI score, missing bonus input) -- never 0 (R8)."""
    raw = _raw_value(factor, inputs, derived)
    if raw is None:
        return None

    if factor.key == "owner_withdrawal":
        # Interim behaviour per deviations register D22: accept the supplied
        # value directly as a 0-100 score, as the golden set does (confirmed:
        # `expect_owner_withdrawal == owner_withdrawal_raw` exactly, for
        # every reconciled row). `curves.cubic` is retained and exercised
        # directly (test_cubic_owner_withdrawal_matches_band_anchors) for
        # when a raw 0-1 ratio becomes the production input -- do not wire
        # it in here until that's confirmed; doing so today would score
        # every application against a curve fit to a completely different
        # input domain.
        return float(raw)

    if factor.kind == "sigmoid":
        x = float(raw)
        if factor.scale_input_by is not None:
            x = x * factor.scale_input_by
        return curves.sigmoid(
            x,
            upper=factor.upper,
            steepness=factor.steepness,
            intercept=factor.intercept,
            decreasing=bool(factor.decreasing),
        )

    if factor.kind == "linear":
        return curves.linear(float(raw), formula=factor.formula or "100 - x")

    if factor.kind == "cubic":
        return curves.cubic(float(raw), a=factor.a, b=factor.b, c=factor.c, d=factor.d)

    if factor.kind == "supplied":
        # AI-graded factors are committed 0-100 numbers already (R3) -- no
        # curve, no clamp. If one arrives out of range, the assertion below
        # should catch it as a genuine upstream bug rather than this
        # function silently clamping it away.
        return float(raw)

    raise ValueError(f"Unknown factor kind: {factor.kind!r}")


def score_all_factors(
    params: ParamSet,
    inputs: GradingInput,
    derived: Mapping[str, Optional[float]],
) -> Dict[str, Optional[float]]:
    scores: Dict[str, Optional[float]] = {}
    for factor in params.factors:
        score = score_factor(factor, inputs, derived)
        if score is not None:
            assert 0.0 <= score <= 100.0, (
                f"factor {factor.key!r} scored {score}, outside [0, 100] "
                "after clamping -- this indicates a params or code bug, "
                "see spec section 7 (Error Cases)"
            )
        scores[factor.key] = score
    return scores
