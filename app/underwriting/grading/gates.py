"""8 knockout gates + decision resolution.

Spec: docs/specs/underwriting/grading-engine-core.md, R9.

| # | Gate | Severity | Rule |
|---|---|---|---|
| 1 | operating_history      | soft | operating_months < 24 |
| 2 | history_vs_term        | soft | duration_months > 0.25 * operating_months |
| 3 | low_factor_count       | soft | DISABLED -- count(factor_scores < 50) >= threshold |
| 4 | first_loan_tenor       | n/a  | enforced in the application UI, not here |
| 5 | excluded_industry      | hard | industry in gambling, alcohol, tobacco, weapons, defence |
| 6 | kyc_aml                | hard | not kyc_aml_passed or fraud_flags non-empty |
| 7 | cic_floor              | hard | DISABLED -- cic_score <= 500 |
| 8 | daily_repayment_rate   | soft | daily_repayment_rate >= 0.30 |

Gates 3 and 7 ship `enabled: false` in the YAML and must stay switchable by
config alone -- `evaluate_gates` reads `gate.enabled` off the `GateParam`,
never a hardcoded skip list, so flipping either on is a params-file change,
not a code change.
"""
from __future__ import annotations

from typing import Mapping, Optional, Tuple

from .params import GateParam, ParamSet
from .types import GateResult, GradingInput

__all__ = ["evaluate_gates"]


def _gate_fires(
    gate: GateParam,
    *,
    inputs: GradingInput,
    factor_scores: Mapping[str, Optional[float]],
    daily_repayment_rate: Optional[float],
    params: ParamSet,
) -> bool:
    key = gate.key

    if key == "operating_history":
        return inputs.operating_months < 24

    if key == "history_vs_term":
        return inputs.duration_months > 0.25 * inputs.operating_months

    if key == "low_factor_count":
        if gate.threshold is None:
            return False
        below_50 = sum(1 for score in factor_scores.values() if score is not None and score < 50)
        return below_50 >= gate.threshold

    if key == "first_loan_tenor":
        # Gate 4: enforced in the application UI, not the engine (R9 #4).
        return False

    if key == "excluded_industry":
        return inputs.industry in params.excluded_industries

    if key == "kyc_aml":
        return (not inputs.kyc_aml_passed) or len(inputs.fraud_flags) > 0

    if key == "cic_floor":
        return inputs.cic_score is not None and inputs.cic_score <= 500

    if key == "daily_repayment_rate":
        return daily_repayment_rate is not None and daily_repayment_rate >= 0.30

    raise ValueError(f"Unknown gate key: {key!r}")


def evaluate_gates(
    params: ParamSet,
    inputs: GradingInput,
    factor_scores: Mapping[str, Optional[float]],
    daily_repayment_rate: Optional[float],
) -> Tuple[GateResult, ...]:
    """Returns only the gates that fired -- there is no `fired=False` entry
    for one that didn't (see `GateResult`). Resolution to a final decision
    (any hard fired -> REJECT; else any soft fired -> REVIEW; else APPROVED)
    lives in engine.py, which also has to fold in AI_PENDING."""
    fired = []
    for gate in params.gates:
        if not gate.enabled or gate.severity == "none":
            continue
        if _gate_fires(
            gate,
            inputs=inputs,
            factor_scores=factor_scores,
            daily_repayment_rate=daily_repayment_rate,
            params=params,
        ):
            fired.append(GateResult(id=gate.id, key=gate.key, severity=gate.severity))
    return tuple(fired)
