"""GET /loans/applications/{id}/indicative-rate — the engine wired to the form.

The adapter's own arithmetic is covered by tests/loans/test_lite_grading.py.
What matters here is the wiring: that a stored application plus a stored
project actually assemble into a `GradingInput`, and that every way of being
un-gradeable comes back as a 409 naming the missing thing rather than a 500.

That last part is the point of the endpoint. The applicant is mid-wizard, so
"what is missing" is the only useful content an error can carry.
"""

import uuid
from datetime import date, timedelta

from conftest import auth_headers

INDUSTRY = "Retail Trade"


def figures(**overrides) -> dict:
    """A profitable, internally consistent set — the same shape the wizard
    posts to /figures."""
    body = {
        "revenue_last_12m": 4_000_000_000,
        "revenue_prior_12m": 3_200_000_000,
        "cogs_y1": 2_400_000_000,
        "fixed_cost_y1": 600_000_000,
        "variable_cost_excl_cogs_y1": 300_000_000,
        "revenue_best_month": 480_000_000,
        "revenue_worst_month": 210_000_000,
        "owner_withdrawal_pct": 25.0,
        "conc_top1_pct": 18.0,
        "conc_top3_pct": 41.0,
    }
    body.update(overrides)
    return body


async def make_gradeable_project(client, sme, **overrides) -> dict:
    """A project carrying every field the engine needs, created through the
    real endpoint so the persistence path is what is under test."""
    body = {
        "legal_name": f"Test Co {uuid.uuid4().hex[:8]}",
        "tax_id": f"TAX-{uuid.uuid4().hex[:10]}",
        "industry": INDUSTRY,
        "employee_count": 25,
        "incorporation_date": str(date.today() - timedelta(days=365 * 5)),
    }
    body.update(overrides)
    resp = await client.post("/projects", json=body, headers=auth_headers(sme))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def make_application(client, sme, project_id, **overrides) -> dict:
    body = {
        "business_id": project_id,
        "requested_amount": "800000000.00",
        "duration_months": 9,
    }
    body.update(overrides)
    resp = await client.post("/loans/applications", json=body, headers=auth_headers(sme))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def save_figures(client, sme, application_id, **overrides):
    resp = await client.put(
        f"/loans/applications/{application_id}/figures",
        json=figures(**overrides),
        headers=auth_headers(sme),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def ready(client, make_user, **project_overrides):
    """SME + gradeable project + application + saved figures."""
    sme = await make_user(role="SME")
    project = await make_gradeable_project(client, sme, **project_overrides)
    application = await make_application(client, sme, project["id"])
    await save_figures(client, sme, application["id"])
    return sme, project, application


def get_rate(client, sme, application_id):
    return client.get(
        f"/loans/applications/{application_id}/indicative-rate",
        headers=auth_headers(sme),
    )


# --------------------------------------------------------------------------- #
# The happy path
# --------------------------------------------------------------------------- #


async def test_returns_a_band_not_a_single_rate(client, make_user):
    sme, _, application = await ready(client, make_user)

    resp = await get_rate(client, sme, application["id"])

    assert resp.status_code == 200, resp.text
    body = resp.json()
    # A range, always. The applicant's CIC score is unknown before KYC, so a
    # single figure would be an invention -- and would read as a quote.
    assert body["rate_low_pct"] < body["rate_high_pct"]
    assert body["grade_low"] < body["grade_high"]


async def test_rate_stays_inside_the_statutory_ceiling(client, make_user):
    sme, _, application = await ready(client, make_user)

    body = (await get_rate(client, sme, application["id"])).json()

    # 20%/yr is the legal cap; the pricing formula clamps to it and nothing
    # downstream may present a rate above it.
    assert 0 < body["rate_low_pct"] <= 20.0
    assert 0 < body["rate_high_pct"] <= 20.0


async def test_band_is_stamped_with_the_versions_that_produced_it(client, make_user):
    sme, _, application = await ready(client, make_user)

    body = (await get_rate(client, sme, application["id"])).json()

    # Anything a user is shown has to be reconstructable later.
    assert body["engine_version"]
    assert body["params_version"]
    assert body["sector_reference_version"]


async def test_assumptions_are_returned_with_the_numbers(client, make_user):
    sme, _, application = await ready(client, make_user)

    body = (await get_rate(client, sme, application["id"])).json()

    # The band takes several things on faith and the UI is required to say so.
    assert body["assumptions"], "a band with no stated assumptions reads as a quote"
    assert any("CIC" in line for line in body["assumptions"])


async def test_omitting_the_optional_shape_fields_widens_nothing_but_is_flagged(
    client, make_user
):
    sme = await make_user(role="SME")
    project = await make_gradeable_project(client, sme)
    application = await make_application(client, sme, project["id"])
    await save_figures(
        client, sme, application["id"], revenue_best_month=None, revenue_worst_month=None
    )

    body = (await get_rate(client, sme, application["id"])).json()

    # Without best/worst month the engine sees a flat year, which flatters a
    # seasonal business. The applicant is told rather than left to assume.
    assert any("flat" in line for line in body["assumptions"])


async def test_the_band_tracks_the_figures(client, make_user):
    """A worse cost base must not price better. This is the check that the
    figures actually reach the engine rather than a default being scored."""
    sme, _, application = await ready(client, make_user)
    healthy = (await get_rate(client, sme, application["id"])).json()

    # Still profitable (3.0 + 0.6 + 0.3 against 4.0bn), just thinner — so the
    # engine scores it rather than refusing it, and the rate has to move up.
    await save_figures(client, sme, application["id"], cogs_y1=3_000_000_000)
    thinner = (await get_rate(client, sme, application["id"])).json()

    assert thinner["rate_low_pct"] > healthy["rate_low_pct"]
    assert thinner["grade_low"] < healthy["grade_low"]


# --------------------------------------------------------------------------- #
# Un-gradeable applications: 409 with the reason, never a 500
# --------------------------------------------------------------------------- #


async def test_409_before_any_figures_are_saved(client, make_user):
    sme = await make_user(role="SME")
    project = await make_gradeable_project(client, sme)
    application = await make_application(client, sme, project["id"])

    resp = await get_rate(client, sme, application["id"])

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "NO_FIGURES"


async def test_409_names_the_missing_project_fields(client, make_user):
    sme = await make_user(role="SME")
    project = await make_gradeable_project(
        client, sme, industry=None, employee_count=None
    )
    application = await make_application(client, sme, project["id"])
    await save_figures(client, sme, application["id"])

    resp = await get_rate(client, sme, application["id"])

    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["code"] == "MISSING_INPUTS"
    # Machine names, so the UI can label them in the applicant's own language.
    assert detail["fields"] == ["industry", "employee_count"]


async def test_409_when_the_term_was_never_captured(client, make_user):
    sme = await make_user(role="SME")
    project = await make_gradeable_project(client, sme)
    application = await make_application(client, sme, project["id"], duration_months=None)
    await save_figures(client, sme, application["id"])

    resp = await get_rate(client, sme, application["id"])

    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["code"] == "MISSING_INPUTS"
    assert detail["fields"] == ["duration_months"]


async def test_409_when_costs_swallow_revenue(client, make_user):
    sme = await make_user(role="SME")
    project = await make_gradeable_project(client, sme)
    application = await make_application(client, sme, project["id"])
    # Costs above revenue: the engine has no rule for it, and this is a real
    # answer about the applicant rather than a bug.
    await save_figures(
        client,
        sme,
        application["id"],
        cogs_y1=4_000_000_000,
        fixed_cost_y1=900_000_000,
        variable_cost_excl_cogs_y1=500_000_000,
    )

    resp = await get_rate(client, sme, application["id"])

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "COSTS_EXCEED_REVENUE"


async def test_409_when_the_amount_predates_engine_bounds(client, make_user):
    """A row written before loan-size validation existed must not 500."""
    sme = await make_user(role="SME")
    project = await make_gradeable_project(client, sme)
    application = await make_application(
        client, sme, project["id"], requested_amount="100000.00"
    )
    await save_figures(client, sme, application["id"])

    resp = await get_rate(client, sme, application["id"])

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "OUT_OF_ENGINE_BOUNDS"


async def test_409_without_an_incorporation_date(client, make_user):
    sme = await make_user(role="SME")
    project = await make_gradeable_project(client, sme, incorporation_date=None)
    application = await make_application(client, sme, project["id"])
    await save_figures(client, sme, application["id"])

    resp = await get_rate(client, sme, application["id"])

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "NO_INCORPORATION_DATE"


# --------------------------------------------------------------------------- #
# Access control
# --------------------------------------------------------------------------- #


async def test_another_sme_gets_404_not_403(client, make_user):
    """404, not 403: confirming the application exists would tell a stranger
    which application ids are real, which enumerates other SMEs' borrowing."""
    sme, _, application = await ready(client, make_user)
    intruder = await make_user(role="SME")

    resp = await get_rate(client, intruder, application["id"])

    assert resp.status_code == 404


async def test_investor_cannot_read_a_band(client, make_user):
    sme, _, application = await ready(client, make_user)
    investor = await make_user(role="INVESTOR")

    resp = await get_rate(client, investor, application["id"])

    assert resp.status_code == 403


async def test_anonymous_cannot_read_a_band(client, make_user):
    _, _, application = await ready(client, make_user)

    # Omitting the Authorization header is not enough: the fixtures signed in
    # through the real API, so the client still holds the session cookie the
    # frontend proxy authenticates with. Clearing the jar is what makes this
    # request actually anonymous.
    client.cookies.clear()

    resp = await client.get(f"/loans/applications/{application['id']}/indicative-rate")

    assert resp.status_code == 401
