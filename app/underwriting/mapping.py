"""Maps a `ScoreRun` ORM row + the `GradingResult` that produced (or
replayed) it onto the `ScoreRunOut` response shape (spec §5.1, T0e).

Kept separate from `service.py` (persistence/business logic) and
`schemas.py` (shape declarations) so the "how do these two objects become
one response" question has one place to live.
"""
from app.lending.models import ScoreRun
from app.underwriting.grading import GradingResult
from app.underwriting.schemas import GateOut, GradeOut, PricingOut, ScoreRunOut, VersionsOut


def to_score_run_out(sr: ScoreRun, grading_result: GradingResult) -> ScoreRunOut:
    # §5.1: pricing and grade.value are null when INSUFFICIENT_DATA or
    # AI_PENDING -- never 0 or 0.0. GradingResult already returns None in
    # those branches (R8); this mapper does not clamp or default them.
    grade_value = grading_result.final_grade
    grade_display = round(grade_value, 2) if grade_value is not None else None

    pricing = None
    if grading_result.interest_rate_pct is not None:
        pricing = PricingOut(
            interest_rate_pct=grading_result.interest_rate_pct,
            # Money as a string of integer VND (§5.1) -- Decimal division
            # in pricing.py is not floored to an integer (see
            # grading-engine-deviations.md D29), so this truncates only for
            # display; the underlying Decimal is never used for arithmetic
            # downstream of this response.
            target_payment_vnd=str(int(grading_result.target_payment_vnd)),
            target_daily_vnd=str(int(grading_result.target_daily_vnd)),
            avg_daily_revenue_vnd=str(int(grading_result.avg_daily_revenue_vnd)),
            daily_repayment_rate=grading_result.daily_repayment_rate,
        )

    return ScoreRunOut(
        id=sr.id,
        application_id=sr.application_id,
        status=sr.status,
        created_at=sr.created_at.isoformat() if sr.created_at else None,
        locked_at=sr.locked_at.isoformat() if sr.locked_at else None,
        decision=grading_result.decision,
        grade=GradeOut(value=grade_value, display=grade_display),
        pricing=pricing,
        premiums=dict(grading_result.premiums),
        factor_scores=dict(grading_result.factor_scores),
        fired_gates=[GateOut(id=g.id, key=g.key, severity=g.severity) for g in grading_result.fired_gates],
        versions=VersionsOut(
            engine=grading_result.engine_version,
            params=grading_result.params_version,
            sector_reference=sr.sector_reference_version,
            bank_rate_pct=float(sr.bank_rate_pct) if sr.bank_rate_pct is not None else 0.0,
            bank_rate_effective_from=sr.bank_rate_effective_from,
        ),
    )
