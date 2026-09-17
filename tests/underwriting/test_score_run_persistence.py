"""T4 (HANDOFF-03) -- score-run persistence and replay.

Requires the real Postgres `db_session` fixture (conftest.py's autouse
`_migrate_schema`) -- these are DB-integration tests, unlike
test_sector_reference.py and the rest of the grading-core suite, which
are pure-function tests with no DB. See the module docstring in
app/underwriting/service.py for what each function does.
"""
import uuid
from datetime import date, timedelta

import pytest

from app.lending.models import LoanApplication, Project, ScoreRun
from app.underwriting.models import BankRateConfig, ScoreRunInput
from app.underwriting.schemas import ScoreRunCreate
from app.underwriting.service import (
    approve_score_run,
    get_current_bank_rate,
    replay_score_run,
    set_bank_rate,
    start_score_run,
)


def _make_score_run_create(application_id, **overrides) -> ScoreRunCreate:
    defaults = dict(
        application_id=application_id,
        company_code="SME-TEST-0001",
        industry="IT Services",
        company_size="micro",
        loan_size_vnd=300_000_000,
        duration_months=3,
        operating_months=36,
        monthly_revenue_vnd=[100_000_000] * 24,
        cogs_y1_vnd=500_000_000,
        fixed_cost_y1_vnd=200_000_000,
        variable_cost_excl_cogs_y1_vnd=100_000_000,
        conc_top1_pct=30.0,
        conc_top3_pct=50.0,
        crr=60.0,
        rri=60.0,
        tcp=60.0,
        owner_withdrawal=50.0,
        cic_score=650,
        kyc_aml_passed=True,
        fraud_flags=[],
    )
    defaults.update(overrides)
    return ScoreRunCreate(**defaults)


@pytest.fixture
async def submitted_application(db_session, project_factory):
    """A LoanApplication in SUBMITTED status -- the precondition
    start_score_run enforces (unchanged from before this handoff)."""
    project = await project_factory()
    app = LoanApplication(
        id=uuid.uuid4(),
        project_id=project.id,
        requested_amount=300_000_000,
        status="SUBMITTED",
    )
    db_session.add(app)
    await db_session.flush()
    return app


async def test_score_run_persists_full_precision_grade_and_rate(db_session, submitted_application):
    body = _make_score_run_create(submitted_application.id)
    sr, grading_result = await start_score_run(db_session, body)
    await db_session.commit()

    assert sr.final_grade_precise == grading_result.final_grade
    # D24: never truncated to 2dp in the field this handoff introduces.
    # (overall_score, the legacy column, IS rounded -- that's the point.)
    assert sr.final_grade_precise != float(sr.overall_score)
    assert sr.interest_rate_pct == grading_result.interest_rate_pct


async def test_score_run_records_engine_and_params_version(db_session, submitted_application):
    body = _make_score_run_create(submitted_application.id)
    sr, grading_result = await start_score_run(db_session, body)
    await db_session.commit()

    assert sr.engine_version == grading_result.engine_version
    assert sr.params_version == grading_result.params_version
    assert sr.sector_reference_version is not None  # IT Services is supported -> resolver was used
    assert sr.bank_rate_pct is not None
    assert sr.bank_rate_effective_from is not None


async def test_score_run_is_replayable_from_stored_inputs(db_session, submitted_application):
    body = _make_score_run_create(submitted_application.id)
    sr, original_result = await start_score_run(db_session, body)
    await db_session.commit()

    replayed_sr, replayed_result = await replay_score_run(db_session, sr.id)
    assert replayed_sr.id == sr.id
    assert replayed_result.final_grade == original_result.final_grade
    assert replayed_result.decision == original_result.decision
    assert replayed_result.interest_rate_pct == original_result.interest_rate_pct
    assert dict(replayed_result.factor_scores) == dict(original_result.factor_scores)


async def test_score_run_input_is_append_only(db_session, submitted_application):
    """DB-level immutability, mirroring state_transition (T6) and the
    ledger tables: a score_run_inputs row can never be updated or
    deleted, only superseded by a new score run."""
    body = _make_score_run_create(submitted_application.id)
    sr, _ = await start_score_run(db_session, body)
    await db_session.commit()

    from sqlalchemy import select

    result = await db_session.execute(select(ScoreRunInput).where(ScoreRunInput.score_run_id == sr.id))
    stored = result.scalar_one()
    stored.company_code = "TAMPERED"
    with pytest.raises(Exception):  # DB trigger raises; exact exception class is driver-specific
        await db_session.flush()
    await db_session.rollback()


async def test_insufficient_data_produces_no_grade_not_a_low_one(db_session, submitted_application):
    body = _make_score_run_create(submitted_application.id, monthly_revenue_vnd=[None] * 24)
    sr, grading_result = await start_score_run(db_session, body)
    await db_session.commit()

    assert sr.decision == "INSUFFICIENT_DATA"
    assert sr.final_grade_precise is None
    assert sr.interest_rate_pct is None
    assert sr.overall_score is None


async def test_bank_rate_config_effective_dating(db_session, admin_user):
    today = date.today()
    baseline = await get_current_bank_rate(db_session, as_of=today)
    assert baseline.rate_pct == pytest.approx(12.0)

    future_date = today + timedelta(days=30)
    await set_bank_rate(db_session, rate_pct=13.5, effective_from=future_date, actor_id=admin_user.id)
    await db_session.commit()

    # Not yet in force today.
    still_current = await get_current_bank_rate(db_session, as_of=today)
    assert still_current.rate_pct == pytest.approx(12.0)

    # In force once its effective date arrives.
    new_current = await get_current_bank_rate(db_session, as_of=future_date)
    assert new_current.rate_pct == pytest.approx(13.5)


async def test_score_run_records_bank_rate_in_force_at_scoring_time(db_session, submitted_application, admin_user):
    """T0b: 'the rate in force must be recorded on every score run so any
    quote is traceable' -- change the rate, confirm the OLD run keeps its
    original rate rather than reflecting the new one."""
    body = _make_score_run_create(submitted_application.id)
    sr, _ = await start_score_run(db_session, body)
    await db_session.commit()
    original_rate = sr.bank_rate_pct

    await set_bank_rate(db_session, rate_pct=15.0, effective_from=date.today(), actor_id=admin_user.id)
    await db_session.commit()

    from sqlalchemy import select

    result = await db_session.execute(select(ScoreRun).where(ScoreRun.id == sr.id))
    reloaded = result.scalar_one()
    assert reloaded.bank_rate_pct == original_rate  # unchanged by the later rate revision
