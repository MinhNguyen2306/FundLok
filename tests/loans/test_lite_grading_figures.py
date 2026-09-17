"""PUT /loans/applications/{id}/figures — the Lite grading capture.

The applicant types these figures instead of uploading the VAT and annual
report bundles. That moves the integrity burden from "did we receive a
document" to "is this number possible", so most of what is asserted here is
rejection: the browser validates the same rules, but the browser is not a
security boundary and a posted body can say anything.
"""

import uuid

from conftest import auth_headers


def figures(**overrides) -> dict:
    """A complete, internally consistent set. Override one key per test so the
    assertion is about that key and nothing else."""
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


async def _draft(make_user, make_project, make_loan_application):
    sme = await make_user(role="SME")
    project = await make_project(sme)
    application = await make_loan_application(sme, project["id"])
    return sme, application


# --------------------------------------------------------------------------- #
# The happy path
# --------------------------------------------------------------------------- #


async def test_sme_can_save_figures_on_a_draft(
    client, make_user, make_project, make_loan_application
):
    sme, application = await _draft(make_user, make_project, make_loan_application)

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(),
        headers=auth_headers(sme),
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["revenue_last_12m"] == 4_000_000_000
    assert body["conc_top3_pct"] == 41.0
    assert body["figures_updated_at"] is not None


async def test_optional_figures_may_be_omitted(
    client, make_user, make_project, make_loan_application
):
    """Five of the eleven fields are optional; leaving them out still grades."""
    sme, application = await _draft(make_user, make_project, make_loan_application)

    required_only = {
        "revenue_last_12m": 4_000_000_000,
        "revenue_prior_12m": 3_200_000_000,
        "cogs_y1": 2_400_000_000,
        "fixed_cost_y1": 600_000_000,
        "variable_cost_excl_cogs_y1": 300_000_000,
    }
    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=required_only,
        headers=auth_headers(sme),
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["revenue_best_month"] is None


async def test_zero_is_kept_distinct_from_blank(
    client, make_user, make_project, make_loan_application
):
    """0% concentration is a real answer, not a missing one. Collapsing the two
    would invent data for a company that genuinely has no large customer."""
    sme, application = await _draft(make_user, make_project, make_loan_application)

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(conc_top1_pct=0, conc_top3_pct=0),
        headers=auth_headers(sme),
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["conc_top1_pct"] == 0
    assert resp.json()["conc_top1_pct"] is not None


async def test_saving_twice_replaces_rather_than_merges(
    client, make_user, make_project, make_loan_application
):
    """A second save that omits an optional field must clear it. Merging would
    keep a stale value the applicant believed they had removed."""
    sme, application = await _draft(make_user, make_project, make_loan_application)
    url = f"/loans/applications/{application['id']}/figures"

    await client.put(url, json=figures(), headers=auth_headers(sme))
    second = await client.put(
        url,
        json=figures(revenue_best_month=None, revenue_worst_month=None),
        headers=auth_headers(sme),
    )

    assert second.status_code == 200, second.text
    assert second.json()["revenue_best_month"] is None


# --------------------------------------------------------------------------- #
# Authorisation and lifecycle
# --------------------------------------------------------------------------- #


async def test_another_sme_cannot_write_figures(
    client, make_user, make_project, make_loan_application
):
    _, application = await _draft(make_user, make_project, make_loan_application)
    intruder = await make_user(role="SME")

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(),
        headers=auth_headers(intruder),
    )

    # 404, not 403: a 403 would confirm the id names a real application and
    # turn this endpoint into an enumeration oracle over other SMEs' borrowing.
    assert resp.status_code == 404


async def test_investor_cannot_write_figures(
    client, make_user, make_project, make_loan_application
):
    _, application = await _draft(make_user, make_project, make_loan_application)
    investor = await make_user(role="INVESTOR")

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(),
        headers=auth_headers(investor),
    )

    assert resp.status_code == 403


async def test_anonymous_cannot_write_figures(
    client, make_user, make_project, make_loan_application
):
    _, application = await _draft(make_user, make_project, make_loan_application)

    # Dropping the Authorization header is not enough to be anonymous: the
    # fixtures signed in through the real API, so the client still holds the
    # session cookie the frontend proxy authenticates with. Clearing the jar is
    # what actually makes this an unauthenticated request.
    client.cookies.clear()

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures", json=figures()
    )

    assert resp.status_code in (401, 403)


async def test_unknown_application_is_not_found(client, make_user):
    sme = await make_user(role="SME")

    resp = await client.put(
        f"/loans/applications/{uuid.uuid4()}/figures",
        json=figures(),
        headers=auth_headers(sme),
    )

    assert resp.status_code == 404


async def test_figures_freeze_once_the_application_is_submitted(
    client, make_user, make_project, make_loan_application, submit_loan_application
):
    """Otherwise an applicant could restate their revenue after seeing the
    offer their original numbers produced."""
    sme, application = await _draft(make_user, make_project, make_loan_application)
    url = f"/loans/applications/{application['id']}/figures"

    await client.put(url, json=figures(), headers=auth_headers(sme))
    submitted = await submit_loan_application(sme, application["id"])
    assert submitted.status_code == 200, submitted.text

    resp = await client.put(
        url, json=figures(revenue_last_12m=9_000_000_000), headers=auth_headers(sme)
    )

    assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# Validation — every one of these passes the browser only if it is bypassed
# --------------------------------------------------------------------------- #


async def test_required_figure_cannot_be_missing(
    client, make_user, make_project, make_loan_application
):
    sme, application = await _draft(make_user, make_project, make_loan_application)
    body = figures()
    del body["cogs_y1"]

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=body,
        headers=auth_headers(sme),
    )

    assert resp.status_code == 422


async def test_required_figure_cannot_be_null(
    client, make_user, make_project, make_loan_application
):
    sme, application = await _draft(make_user, make_project, make_loan_application)

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(fixed_cost_y1=None),
        headers=auth_headers(sme),
    )

    assert resp.status_code == 422


async def test_negative_amount_is_rejected(
    client, make_user, make_project, make_loan_application
):
    sme, application = await _draft(make_user, make_project, make_loan_application)

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(revenue_last_12m=-1),
        headers=auth_headers(sme),
    )

    assert resp.status_code == 422


async def test_absurd_amount_is_rejected(
    client, make_user, make_project, make_loan_application
):
    """A slipped extra digit would otherwise grade a corner shop as a
    conglomerate, and the applicant would never see why the band was wrong."""
    sme, application = await _draft(make_user, make_project, make_loan_application)

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(revenue_last_12m=10_000_000_000_000),
        headers=auth_headers(sme),
    )

    assert resp.status_code == 422


async def test_percentage_above_100_is_rejected(
    client, make_user, make_project, make_loan_application
):
    sme, application = await _draft(make_user, make_project, make_loan_application)

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(conc_top1_pct=140),
        headers=auth_headers(sme),
    )

    assert resp.status_code == 422


async def test_worst_month_cannot_beat_best_month(
    client, make_user, make_project, make_loan_application
):
    sme, application = await _draft(make_user, make_project, make_loan_application)

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(revenue_best_month=100_000_000, revenue_worst_month=200_000_000),
        headers=auth_headers(sme),
    )

    assert resp.status_code == 422


async def test_a_month_cannot_out_earn_its_own_year(
    client, make_user, make_project, make_loan_application
):
    sme, application = await _draft(make_user, make_project, make_loan_application)

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(
            revenue_last_12m=1_000_000_000, revenue_best_month=2_000_000_000
        ),
        headers=auth_headers(sme),
    )

    assert resp.status_code == 422


async def test_top1_cannot_exceed_top3(
    client, make_user, make_project, make_loan_application
):
    """The top 3 customers include the top 1 by definition."""
    sme, application = await _draft(make_user, make_project, make_loan_application)

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(conc_top1_pct=60, conc_top3_pct=40),
        headers=auth_headers(sme),
    )

    assert resp.status_code == 422


async def test_unknown_fields_are_rejected(
    client, make_user, make_project, make_loan_application
):
    """The column is schemaless, so an accepted stray key would be stored
    verbatim and reach underwriting as though it were a real input."""
    sme, application = await _draft(make_user, make_project, make_loan_application)

    resp = await client.put(
        f"/loans/applications/{application['id']}/figures",
        json=figures(credit_score=800),
        headers=auth_headers(sme),
    )

    assert resp.status_code == 422
