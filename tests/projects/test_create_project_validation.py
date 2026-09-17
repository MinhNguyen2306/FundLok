"""POST /projects validates against the grading engine's own constraints.

Spec: docs/specs/underwriting/grading-input-sources.md §4, §6.3, §7.

The engine raises ValueError on an unknown industry, a loan outside
`loan_constraints`, or a term outside `allowed_durations_months`. Reaching those
raises means the application was already stored in a shape that can never be
graded, so the same rules are enforced at create time. Every bound here is read
from grading_params_v1.yaml, never retyped — the assertions below use the loaded
params for the same reason.
"""
import uuid

import pytest

from app.projects.engine_constraints import params
from app.projects.schemas import ProjectCreate
from conftest import auth_headers

CONSTRAINTS = params().loan_constraints
MIN_VND = int(CONSTRAINTS["min_vnd"])
MAX_VND = int(CONSTRAINTS["max_vnd"])


def _payload(**overrides):
    payload = {
        "legal_name": f"Validation Co {uuid.uuid4().hex[:8]}",
        "tax_id": f"TAX-{uuid.uuid4().hex[:10]}",
        "industry": "IT Services",
        "employee_count": 25,
        "incorporation_date": "2023-05-10",
        "loan_application": {
            "requested_amount": 800000000,
            "duration_months": 9,
            "purpose": "Working capital",
            "repayment_preference": "MONTHLY",
        },
    }
    payload.update(overrides)
    return payload


def _with_loan(**loan_overrides):
    payload = _payload()
    payload["loan_application"] = {**payload["loan_application"], **loan_overrides}
    return payload


# --- industry ---------------------------------------------------------------


async def test_unsupported_industry_rejected(client, make_user):
    sme = await make_user(role="SME")
    resp = await client.post(
        "/projects",
        json=_payload(industry="Technology & Software"),
        headers=auth_headers(sme),
    )
    assert resp.status_code == 422, resp.text
    assert "grading engine supports" in resp.text


async def test_supported_industry_accepted(client, make_user):
    sme = await make_user(role="SME")
    supported = params().supported_industries[0]
    resp = await client.post(
        "/projects", json=_payload(industry=supported), headers=auth_headers(sme)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["industry"] == supported


async def test_excluded_industry_accepted_so_the_gate_can_reject_it(
    client, make_user
):
    """An excluded industry is a *recognised* one — gate 5 rejects it after
    grading, which is an auditable REJECT rather than a 422. Mirrors the
    engine's own _validate_inputs."""
    sme = await make_user(role="SME")
    excluded = params().excluded_industries[0]
    resp = await client.post(
        "/projects", json=_payload(industry=excluded), headers=auth_headers(sme)
    )
    assert resp.status_code == 201, resp.text


async def test_industry_may_still_be_omitted(client, make_user):
    """`projects.industry` is nullable and predates the engine; an existing
    client that omits it must keep working."""
    sme = await make_user(role="SME")
    payload = _payload()
    payload.pop("industry")
    resp = await client.post("/projects", json=payload, headers=auth_headers(sme))
    assert resp.status_code == 201, resp.text
    assert resp.json()["industry"] is None


# --- loan size --------------------------------------------------------------


@pytest.mark.parametrize("amount", [MIN_VND - 1, 100_000_000, MAX_VND + 1])
async def test_loan_size_outside_engine_bounds_rejected(client, make_user, amount):
    sme = await make_user(role="SME")
    resp = await client.post(
        "/projects", json=_with_loan(requested_amount=amount), headers=auth_headers(sme)
    )
    assert resp.status_code == 422, resp.text
    assert "requested_amount must be between" in resp.text


@pytest.mark.parametrize("amount", [MIN_VND, MAX_VND])
async def test_loan_size_at_the_boundaries_accepted(client, make_user, amount):
    sme = await make_user(role="SME")
    resp = await client.post(
        "/projects", json=_with_loan(requested_amount=amount), headers=auth_headers(sme)
    )
    assert resp.status_code == 201, resp.text


# --- duration ---------------------------------------------------------------


@pytest.mark.parametrize("months", [0, 4, 11, 24])
async def test_disallowed_duration_rejected(client, make_user, months):
    sme = await make_user(role="SME")
    resp = await client.post(
        "/projects", json=_with_loan(duration_months=months), headers=auth_headers(sme)
    )
    assert resp.status_code == 422, resp.text
    assert "duration_months must be one of" in resp.text


async def test_every_allowed_duration_accepted(client, make_user):
    for months in CONSTRAINTS["allowed_durations_months"]:
        sme = await make_user(role="SME")
        resp = await client.post(
            "/projects",
            json=_with_loan(duration_months=months),
            headers=auth_headers(sme),
        )
        assert resp.status_code == 201, f"{months}mo: {resp.text}"


async def test_duration_may_be_omitted(client, make_user):
    """Optional while the column does not exist — an older client must not 422."""
    sme = await make_user(role="SME")
    payload = _payload()
    payload["loan_application"].pop("duration_months")
    resp = await client.post("/projects", json=payload, headers=auth_headers(sme))
    assert resp.status_code == 201, resp.text


# --- headcount and derived company size -------------------------------------


@pytest.mark.parametrize("count", [0, -5, 201, 1000])
async def test_headcount_outside_every_band_rejected(client, make_user, count):
    sme = await make_user(role="SME")
    resp = await client.post(
        "/projects", json=_payload(employee_count=count), headers=auth_headers(sme)
    )
    assert resp.status_code == 422, resp.text
    assert "employee_count must be between" in resp.text


async def test_headcount_may_be_omitted(client, make_user):
    sme = await make_user(role="SME")
    payload = _payload()
    payload.pop("employee_count")
    resp = await client.post("/projects", json=payload, headers=auth_headers(sme))
    assert resp.status_code == 201, resp.text


@pytest.mark.parametrize(
    "count,expected",
    [(1, "micro"), (10, "micro"), (11, "small"), (50, "small"), (51, "medium"), (200, "medium")],
)
def test_company_size_derived_from_headcount(count, expected):
    model = ProjectCreate(legal_name="Derive Co", employee_count=count)
    assert model.company_size == expected


def test_client_supplied_company_size_is_overwritten():
    """A band that contradicts the headcount would put a mis-scored application
    in the queue, so the server recomputes it (input-sources spec §6.3)."""
    model = ProjectCreate(
        legal_name="Derive Co", employee_count=5, company_size="medium"
    )
    assert model.company_size == "micro"
