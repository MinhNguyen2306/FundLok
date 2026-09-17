"""T4 (HANDOFF-03) -- score-run persistence and replay.

Requires the real Postgres `db_session`/`client` fixtures from the root
`conftest.py` (autouse `_migrate_schema`) -- these are DB-integration
tests, unlike test_sector_reference.py and the rest of the grading-core
suite, which are pure-function tests with no DB.

Goes entirely through the real HTTP API (`client`), using the same
fixtures the rest of the suite uses (`make_user`, `make_admin`,
`make_project`, `make_loan_application`, `submit_loan_application`) --
never a hand-built `ScoreRunCreate`/service-layer call with invented
fields, because `POST /underwriting/score-runs` only ever accepts
`{application_id, mode}` (see `run_and_lock_score` in the root
conftest.py, which this suite must not diverge from). An application's
financial data is submitted separately via
`PUT /underwriting/applications/{id}/financials` before scoring.
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.underwriting.models import BankRateConfig, ScoreRunInput
from app.underwriting.service import get_current_bank_rate, set_bank_rate

FULL_FINANCIALS = {
    "industry": "IT Services",
    "company_size": "micro",
    "duration_months": 3,
    "operating_months": 36,
    "monthly_revenue_vnd": [100_000_000] * 24,
    "cogs_y1_vnd": 500_000_000,
    "fixed_cost_y1_vnd": 200_000_000,
    "variable_cost_excl_cogs_y1_vnd": 100_000_000,
    "conc_top1_pct": 30.0,
    "conc_top3_pct": 50.0,
    "crr": 60.0,
    "rri": 60.0,
    "tcp": 60.0,
    "owner_withdrawal": 50.0,
    "cic_score": 650,
    "kyc_aml_passed": True,
    "fraud_flags": [],
}


@pytest.fixture
async def scored_setup(client, make_user, make_admin, make_project, make_loan_application, submit_loan_application):
    """SME project -> submitted loan application, admin ready to score it."""
    sme = await make_user(role="SME")
    admin = await make_admin()
    project = await make_project(sme)
    application = await make_loan_application(sme, project["id"], requested_amount="300000000.00")
    resp = await submit_loan_application(sme, application["id"])
    assert resp.status_code == 200
    return {"sme": sme, "admin": admin, "project": project, "application": application}


async def _put_financials(client, admin, application_id, **overrides):
    body = dict(FULL_FINANCIALS)
    body.update(overrides)
    resp = await client.put(
        f"/underwriting/applications/{application_id}/financials",
        json=body,
        headers=admin["headers"],
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _start_score_run(client, admin, application_id, mode=None):
    resp = await client.post(
        "/underwriting/score-runs",
        json={"application_id": application_id, "mode": mode},
        headers=admin["headers"],
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_score_run_with_no_financials_is_insufficient_data(client, scored_setup):
    """An application with no `LoanApplicationFinancials` row yet must
    still start a score run successfully (this is exactly the path
    `run_and_lock_score` exercises throughout the rest of the suite,
    which never submits financials) -- it resolves to INSUFFICIENT_DATA,
    per R8, rather than erroring."""
    admin = scored_setup["admin"]
    application = scored_setup["application"]

    body = await _start_score_run(client, admin, application["id"])

    assert body["decision"] == "INSUFFICIENT_DATA"
    assert body["grade"]["value"] is None
    assert body["grade"]["display"] is None
    assert body["pricing"] is None


async def test_score_run_with_financials_produces_a_real_grade(client, scored_setup, db_session):
    admin = scored_setup["admin"]
    application = scored_setup["application"]

    await _put_financials(client, admin, application["id"])
    body = await _start_score_run(client, admin, application["id"])

    assert body["decision"] in ("APPROVED", "REVIEW", "REJECT", "AI_PENDING")
    assert body["versions"]["engine"]
    assert body["versions"]["params"]
    assert body["versions"]["sector_reference"] is not None  # IT Services is supported -> resolver was used

    result = await db_session.execute(select(ScoreRunInput).where(ScoreRunInput.score_run_id == body["id"]))
    stored = result.scalar_one()
    assert stored.industry == "IT Services"


async def test_score_run_is_replayable_from_stored_inputs(client, scored_setup):
    admin = scored_setup["admin"]
    application = scored_setup["application"]

    await _put_financials(client, admin, application["id"])
    started = await _start_score_run(client, admin, application["id"])

    replayed = await client.get(f"/underwriting/score-runs/{started['id']}", headers=admin["headers"])
    assert replayed.status_code == 200, replayed.text
    replayed_body = replayed.json()

    assert replayed_body["decision"] == started["decision"]
    assert replayed_body["grade"]["value"] == started["grade"]["value"]
    assert replayed_body["factor_scores"] == started["factor_scores"]


async def test_score_run_input_is_append_only(client, scored_setup, db_session):
    """DB-level immutability, mirroring state_transition (T6) and the
    ledger tables: a score_run_inputs row can never be updated or
    deleted, only superseded by a new score run."""
    admin = scored_setup["admin"]
    application = scored_setup["application"]

    await _put_financials(client, admin, application["id"])
    started = await _start_score_run(client, admin, application["id"])

    result = await db_session.execute(select(ScoreRunInput).where(ScoreRunInput.score_run_id == started["id"]))
    stored = result.scalar_one()
    stored.industry = "TAMPERED"
    with pytest.raises(Exception):  # DB trigger raises; exact exception class is driver-specific
        await db_session.flush()
    await db_session.rollback()


async def test_bank_rate_config_effective_dating(db_session, make_admin):
    admin = await make_admin()
    today = date.today()
    baseline = await get_current_bank_rate(db_session, as_of=today)
    assert baseline.rate_pct == pytest.approx(12.0)

    future_date = today + timedelta(days=30)
    await set_bank_rate(db_session, rate_pct=13.5, effective_from=future_date, actor_id=admin["id"])
    await db_session.commit()

    # Not yet in force today.
    still_current = await get_current_bank_rate(db_session, as_of=today)
    assert still_current.rate_pct == pytest.approx(12.0)

    # In force once its effective date arrives.
    new_current = await get_current_bank_rate(db_session, as_of=future_date)
    assert new_current.rate_pct == pytest.approx(13.5)


async def test_score_run_records_bank_rate_in_force_at_scoring_time(client, scored_setup, db_session):
    """T0b: 'the rate in force must be recorded on every score run so any
    quote is traceable' -- change the rate, confirm the OLD run keeps its
    original rate rather than reflecting the new one."""
    admin = scored_setup["admin"]
    application = scored_setup["application"]

    await _put_financials(client, admin, application["id"])
    started = await _start_score_run(client, admin, application["id"])
    original_rate = started["versions"]["bank_rate_pct"]

    # A date distinct from the migration's seed row's effective_from
    # (2026-09-17) -- `effective_from` is unique, and in this environment
    # "today" collides with the seed date exactly.
    await set_bank_rate(
        db_session, rate_pct=15.0, effective_from=date.today() + timedelta(days=1), actor_id=admin["id"]
    )
    await db_session.commit()

    result = await db_session.execute(select(BankRateConfig).order_by(BankRateConfig.effective_from.desc()))
    assert float(result.scalars().first().rate_pct) == pytest.approx(15.0)

    replayed = await client.get(f"/underwriting/score-runs/{started['id']}", headers=admin["headers"])
    assert replayed.status_code == 200
    assert replayed.json()["versions"]["bank_rate_pct"] == pytest.approx(original_rate)
