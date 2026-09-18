"""Facility origination: schedule generation (T7).

Implements the source-of-truth spec's §4.1 (origination sizing) and §4.5
(backstop day index) exactly, against
`docs/specs/repayment_schedule/fixed-daily-repayment-mechanism-v1.3.md`.
Reproduces the §12.1 worked example to the đồng (see
tests/repayment_schedule/test_origination.py): I, T0, N0, A0, remainder,
final instalment, and N_bs all match.

History: this handoff originally reconstructed N_bs = ceil(4*N0/3) from
the single (N0=88 -> N_bs=118) data point in the worked example, because
the source docx was not committed to the repo at the time. It has since
been committed and confirmed as ceil(4*N0/3), and the §4.5 backstop
table (66->88, 132->176, 264->352) rules out the alternative N0+30
formula that also happened to fit the single original data point.
"""
from __future__ import annotations

import dataclasses
import datetime
import math
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.repayment_schedule.calendar import DEFAULT_WORKING_DAYS_PER_MONTH, BusinessDayCalendar
from app.repayment_schedule.models import Facility, ScheduledPayment, ScheduleVersion, StateTransition

# --------------------------------------------------------------------------
# BACKSTOP -- spec §4.5, confirmed against the committed source-of-truth
# spec: N_bs = min(ceil(4 * N0 / 3), 24 * D). D13/D15/§4.5 table (66->88,
# 132->176, 264->352) all confirm the 4/3 ratio and rule out the N0+30
# alternative once considered when only a single data point was available.
#
# The `24 * D` cap cannot bind today: D15 caps the declared term at 12
# months, so N0 = D * x <= 12*D, and ceil(4*N0/3) <= ceil(16*D) = 16*D,
# which is always <= 24*D. It is included anyway as a guard against a
# future change to D15 (a longer declared term becoming permitted) that
# would otherwise silently let the backstop run past the intended
# proportional bound -- it is dead logic today, not live logic.
# --------------------------------------------------------------------------
BACKSTOP_TERM_MULTIPLIER_NUMERATOR = 4
BACKSTOP_TERM_MULTIPLIER_DENOMINATOR = 3
BACKSTOP_ABSOLUTE_CAP_MONTHS = 24  # "24 x D" in §4.5 -- see comment above


def _ceil_div(numerator: int, denominator: int) -> int:
    """Exact integer ceiling division -- avoids float precision issues
    that `math.ceil(a / b)` can introduce for large numerators."""
    return -(-numerator // denominator)


def compute_backstop_day_index(business_day_count: int, working_days_per_month: int) -> int:
    """N_bs = min(ceil(4 * N0 / 3), 24 * D) -- spec §4.5."""
    proportional = _ceil_div(
        business_day_count * BACKSTOP_TERM_MULTIPLIER_NUMERATOR,
        BACKSTOP_TERM_MULTIPLIER_DENOMINATOR,
    )
    absolute_cap = BACKSTOP_ABSOLUTE_CAP_MONTHS * working_days_per_month
    return min(proportional, absolute_cap)


@dataclasses.dataclass(frozen=True)
class OriginationResult:
    """Every integer-VND output of §4.1 and §4.5 (backstop)."""

    principal_vnd: int
    interest_vnd: int  # I
    total_obligation_vnd: int  # T0 = P + I
    business_day_count: int  # N0
    daily_amount_vnd: int  # A0 = floor(T0 / N0)
    remainder_vnd: int  # T0 - A0*N0
    final_instalment_vnd: int  # A0 + remainder
    backstop_day_index: int  # N_bs -- spec §4.5
    annual_rate_pct: Decimal  # r, as a percentage (e.g. Decimal("12") for 12%)
    contractual_term_months: int  # x -- declared duration, sizing basis only


def compute_origination(
    *,
    principal_vnd: int,
    annual_rate_pct: Decimal,
    contractual_term_months: int,
    working_days_per_month: int = DEFAULT_WORKING_DAYS_PER_MONTH,
) -> OriginationResult:
    """§4.1 exactly. Integer VND throughout; floor division for A0;
    remainder absorbed entirely by the final instalment.

    I = P * r/100 * x/12, rounded to the nearest đồng (round-half-up --
    the worked example's own numbers are exact, so this rounding rule
    is never exercised by it, but a rate/term combination that does not
    divide evenly needs a defined rule, and integer VND leaves no other
    sane one than "round to the nearest whole đồng").
    """
    if principal_vnd <= 0:
        raise ValueError(f"principal_vnd must be positive, got {principal_vnd}")
    if contractual_term_months <= 0:
        raise ValueError(f"contractual_term_months must be positive, got {contractual_term_months}")
    if annual_rate_pct < 0:
        raise ValueError(f"annual_rate_pct must be non-negative, got {annual_rate_pct}")
    if annual_rate_pct > 20:
        # Spec §4.3 / INV-13: require r <= 0.20 (Điều 468 contract-rate ceiling).
        # A rate above the statutory cap is invalid at origination, full stop --
        # this is not something a downstream invariant check should merely flag.
        raise ValueError(f"annual_rate_pct exceeds the statutory 20% cap (Điều 468, INV-13): got {annual_rate_pct}")

    principal = Decimal(principal_vnd)
    rate = Decimal(annual_rate_pct) / Decimal(100)
    term_fraction = Decimal(contractual_term_months) / Decimal(12)

    interest = (principal * rate * term_fraction).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    interest_vnd = int(interest)
    total_obligation_vnd = principal_vnd + interest_vnd

    business_day_count = contractual_term_months * working_days_per_month  # N0
    if business_day_count <= 0:
        raise ValueError(f"business_day_count must be positive, got {business_day_count}")

    daily_amount_vnd, remainder_vnd = divmod(total_obligation_vnd, business_day_count)  # A0, remainder
    final_instalment_vnd = daily_amount_vnd + remainder_vnd

    backstop_day_index = compute_backstop_day_index(business_day_count, working_days_per_month)

    return OriginationResult(
        principal_vnd=principal_vnd,
        interest_vnd=interest_vnd,
        total_obligation_vnd=total_obligation_vnd,
        business_day_count=business_day_count,
        daily_amount_vnd=daily_amount_vnd,
        remainder_vnd=remainder_vnd,
        final_instalment_vnd=final_instalment_vnd,
        backstop_day_index=backstop_day_index,
        annual_rate_pct=annual_rate_pct,
        contractual_term_months=contractual_term_months,
    )


class OriginationInvariantError(Exception):
    """Raised when a post-computation invariant fails. Per the handoff's
    instruction, every invariant "fails loudly and halts the affected
    facility's processing rather than continuing with inconsistent
    state" -- callers must not catch and continue."""


def _assert_origination_invariants(result: OriginationResult, schedule_dates: list[datetime.date], calendar: BusinessDayCalendar) -> None:
    """Checks against the numbered invariants in §10 of the committed
    source-of-truth spec (fixed-daily-repayment-mechanism-v1.3.md). Prior
    to that spec being committed, this function's checks were inferred
    from the T7 task description alone and mislabeled two of them
    (INV-5 and INV-13 were attached to the wrong checks); this version
    corrects the labels and adds the statutory-cap check INV-5 was
    actually about, which nothing previously checked at origination.
    """
    # INV-1: collected_to_date + outstanding = total_repayable, exactly,
    # at all times. At origination, collected=0 and the full obligation
    # is outstanding.
    collected = 0
    outstanding = result.total_obligation_vnd
    if collected + outstanding != result.total_obligation_vnd:
        raise OriginationInvariantError(
            f"INV-1 violated at origination: collected({collected}) + outstanding({outstanding}) "
            f"!= total_obligation_vnd({result.total_obligation_vnd})"
        )

    # INV-5: implied_nominal <= 20% (D12, §4.3). duration_for_cap = max(M, y);
    # at origination y (actual duration) does not exist yet, so it reduces to
    # the declared term.
    duration_for_cap = Decimal(result.contractual_term_months)
    implied_nominal = (
        (Decimal(result.total_obligation_vnd) / Decimal(result.principal_vnd) - 1) * 12 / duration_for_cap
    )
    if implied_nominal > Decimal("0.20"):
        raise OriginationInvariantError(
            f"INV-5 violated: implied_nominal({implied_nominal}) exceeds the 20% statutory cap "
            f"(D12, §4.3) for principal={result.principal_vnd}, total_obligation={result.total_obligation_vnd}, "
            f"contractual_term_months={result.contractual_term_months}"
        )

    # INV-7: sum of scheduled amounts in the active version = outstanding
    # balance. At origination, outstanding balance is the full T0.
    reconstructed_total = result.daily_amount_vnd * (result.business_day_count - 1) + result.final_instalment_vnd
    if reconstructed_total != result.total_obligation_vnd:
        raise OriginationInvariantError(
            f"INV-7 violated: A0*(N0-1) + final = {reconstructed_total}, "
            f"expected total_obligation_vnd = {result.total_obligation_vnd}"
        )
    if result.final_instalment_vnd != result.daily_amount_vnd + result.remainder_vnd:
        raise OriginationInvariantError(
            f"INV-7 violated: final_instalment_vnd({result.final_instalment_vnd}) != "
            f"daily_amount_vnd({result.daily_amount_vnd}) + remainder_vnd({result.remainder_vnd})"
        )
    if not (0 <= result.remainder_vnd < result.business_day_count):
        raise OriginationInvariantError(
            f"INV-7 violated: remainder_vnd({result.remainder_vnd}) is not in [0, business_day_count)"
        )

    # INV-13: late_rate_applied <= 30% and contract rate r <= 20%. The
    # late-rate half only applies to extensions (T3/T4/T5 territory, not
    # origination); compute_origination() already rejects r > 20% before
    # this function is ever reached (see its ValueError check), so this
    # is a defense-in-depth re-check, not the primary enforcement point.
    if result.annual_rate_pct > 20:
        raise OriginationInvariantError(
            f"INV-13 violated: annual_rate_pct({result.annual_rate_pct}) exceeds the statutory 20% cap"
        )

    # Schedule-generation sanity (not a numbered §10 invariant on its own,
    # but a precondition every numbered invariant above assumes): every
    # scheduled slot must be a real, distinct business day, one per index.
    if len(schedule_dates) != result.business_day_count:
        raise OriginationInvariantError(
            f"Schedule generation violated: generated {len(schedule_dates)} schedule dates, "
            f"expected business_day_count={result.business_day_count}"
        )
    for d in schedule_dates:
        if not calendar.is_business_day(d):
            raise OriginationInvariantError(f"Schedule generation violated: scheduled_date {d} is not a business day")
    if len(set(schedule_dates)) != len(schedule_dates):
        raise OriginationInvariantError("Schedule generation violated: duplicate scheduled_date in generated schedule")


def originate_facility(
    db,
    *,
    contract_id: UUID,
    principal_vnd: int,
    annual_rate_pct: Decimal,
    contractual_term_months: int,
    payment_reference: str,
    start_date: datetime.date,
    calendar: BusinessDayCalendar,
    working_days_per_month: int = DEFAULT_WORKING_DAYS_PER_MONTH,
    actor_id: UUID | None = None,
) -> Facility:
    """Compute §4.1, generate the schedule, and write facility +
    schedule_version + scheduled_payment rows (plus the origination
    state_transition). Raises OriginationInvariantError before writing
    anything if a post-computation check fails -- nothing is added to the
    session in that case, matching post_transaction()'s all-or-nothing
    behavior in app/ledger/service.py.
    """
    result = compute_origination(
        principal_vnd=principal_vnd,
        annual_rate_pct=annual_rate_pct,
        contractual_term_months=contractual_term_months,
        working_days_per_month=working_days_per_month,
    )
    schedule_dates = calendar.generate_business_days(start_date, result.business_day_count)

    # Validate before writing anything (see docstring).
    _assert_origination_invariants(result, schedule_dates, calendar)

    backstop_date = calendar.recompute_backstop_date(start_date, result.backstop_day_index)

    facility = Facility(
        contract_id=contract_id,
        principal_vnd=result.principal_vnd,
        annual_rate_pct=annual_rate_pct,
        contractual_term_months=contractual_term_months,
        interest_vnd=result.interest_vnd,
        total_obligation_vnd=result.total_obligation_vnd,
        business_day_count=result.business_day_count,
        backstop_day_index=result.backstop_day_index,  # set once, at INSERT -- the DB trigger only guards UPDATE
        backstop_date=backstop_date,
        status="DRAFT",
        payment_reference=payment_reference,
    )
    db.add(facility)

    db.add(
        StateTransition(
            facility=facility,
            from_status=None,
            to_status="DRAFT",
            trigger="ORIGINATED",
            actor_id=actor_id,
        )
    )

    schedule_version = ScheduleVersion(
        facility=facility,
        version_number=1,
        daily_amount_vnd=result.daily_amount_vnd,
        day_count=result.business_day_count,
        remainder_vnd=result.remainder_vnd,
        final_instalment_vnd=result.final_instalment_vnd,
    )
    db.add(schedule_version)

    for day_index, scheduled_date in enumerate(schedule_dates, start=1):
        is_last = day_index == result.business_day_count
        expected_amount = result.final_instalment_vnd if is_last else result.daily_amount_vnd
        db.add(
            ScheduledPayment(
                facility=facility,
                schedule_version=schedule_version,
                day_index=day_index,
                scheduled_date=scheduled_date,
                expected_amount_vnd=expected_amount,
            )
        )

    return facility
