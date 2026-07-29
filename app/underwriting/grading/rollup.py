"""4 group premiums + final grade.

Spec: docs/specs/underwriting/grading-engine-core.md, R7.

    bcq        = 0.20 GM + 0.20 CM + 0.20 OM + 0.20 CF + 0.10 LR + 0.10 SCSR
    rsg        = (1/3) VOL + (1/3) TREND + (1/4) SEAS + TOP1/20 + TOP3/20 + RTI/20
    sector     = mean of its 7 factors (1/7 each)
    behavioral = CIC + OWNER_WITHDRAWAL/20 + FOUNDER/20
    final      = 0.40 bcq + 0.25 rsg + 0.25 sector + 0.10 behavioral

Seasonality carries 1/4, not 1/3 -- the RSG core sums to 0.91666..., not 1.0.
CIC carries full weight (1.0) in Behavioral; Tax Discipline is absent from the
roll-up entirely. Both are deliberate (R7) -- do not "fix" them. All weights
come from the YAML (`params.rollup`, `params.final_grade`); nothing here is a
retyped constant.
"""
from __future__ import annotations

from typing import Dict, Mapping, Optional, Tuple

from .params import ParamSet

__all__ = ["compute_group_premium", "compute_rollup"]


def compute_group_premium(
    group_weights: Mapping[str, Mapping[str, float]],
    factor_scores: Mapping[str, Optional[float]],
) -> float:
    """One group's premium.

    Core weights are fixed fractions of the group (e.g. sector's 1/7 each).
    When every core factor is present (true for every deterministic group,
    always, and for `sector` whenever no AI score is missing) this reduces to
    exactly the weighted sum in R7. When an AI-graded core factor is missing
    (`sector`, under `AI_PENDING`), R8 says the group must be "computed over
    the factors present" rather than silently discounted by the missing
    factor's weight -- so the weighted sum is renormalised over the weight
    actually present, which is the same thing as an average over the present
    factors for `sector`'s equal-weighted core.

    Bonus factors are different (R8): a missing bonus contributes exactly 0,
    no renormalisation -- each bonus factor is an independent `score/20` add-on,
    not a share of a fixed pool.
    """
    core = group_weights["core"]
    bonus = group_weights["bonus"]

    weighted_sum = 0.0
    weight_present = 0.0
    for key, weight in core.items():
        score = factor_scores.get(key)
        if score is None:
            continue
        weighted_sum += weight * score
        weight_present += weight

    total_core_weight = sum(core.values())
    if weight_present == 0.0:
        premium = 0.0
    elif weight_present == total_core_weight:
        premium = weighted_sum
    else:
        premium = weighted_sum / weight_present * total_core_weight

    for key, weight in bonus.items():
        score = factor_scores.get(key)
        if score is None:
            continue
        premium += weight * score

    return premium


def compute_rollup(
    params: ParamSet,
    factor_scores: Mapping[str, Optional[float]],
) -> Tuple[Dict[str, float], float]:
    """Returns (premiums, final_grade). Premiums are NOT clamped (R7) --
    empirically none exceeds 100 across the golden set (max: bcq 98.46,
    rsg 92.37, sector 82.65, behavioral 96.03); if one ever does, that's a
    real bug we want a loud failure for, not a silently truncated number."""
    premiums: Dict[str, float] = {}
    for group_name, group_weights in params.rollup.items():
        premium = compute_group_premium(group_weights, factor_scores)
        assert premium <= 100.0, (
            f"{group_name} premium {premium} exceeds 100 -- premiums are not "
            "clamped by design (R7); this indicates drift from the golden "
            "set, not something to silently clamp"
        )
        premiums[group_name] = premium

    final_grade = sum(weight * premiums[group_name] for group_name, weight in params.final_grade.items())
    return premiums, final_grade
