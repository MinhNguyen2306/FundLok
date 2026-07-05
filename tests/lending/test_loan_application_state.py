"""HANDOFF-01 §5 + §3.4: LoanApplication state machine, as reachable via the API.

Known gap (documented for Edward, not fixed here per the "characterize, don't
fix" guardrail): there is no endpoint anywhere in the app that moves a
LoanApplication to APPROVED or REJECTED. The only reachable transitions are
DRAFT -> SUBMITTED (POST /loans/applications/{id}/submit) and
SUBMITTED -> UNDER_REVIEW, which happens as a side effect of starting a score
run (POST /underwriting/score-runs), not through any explicit
approve/reject-application action.
"""


async def test_loan_application_draft_to_submitted(client, make_user, make_project, make_loan_application,
                                                     submit_loan_application):
    sme = await make_user(role="SME")
    project = await make_project(sme)
    application = await make_loan_application(sme, project["id"])
    assert application["status"] == "DRAFT"

    resp = await submit_loan_application(sme, application["id"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "SUBMITTED"


async def test_loan_application_cannot_resubmit_from_submitted(client, make_user, make_project,
                                                                make_loan_application, submit_loan_application):
    sme = await make_user(role="SME")
    project = await make_project(sme)
    application = await make_loan_application(sme, project["id"])
    first = await submit_loan_application(sme, application["id"])
    assert first.status_code == 200

    second = await submit_loan_application(sme, application["id"])
    assert second.status_code == 400
    assert second.json() == {"detail": "Application is not in DRAFT status"}


async def test_loan_application_submitted_to_approved_and_rejected_paths(client, make_user, make_admin, make_project,
                                                                          make_loan_application,
                                                                          submit_loan_application):
    """Characterizes actual current behavior: scoring moves the application to
    UNDER_REVIEW, and that is as far as any reachable endpoint takes it. There
    is no APPROVED or REJECTED transition available through the API today."""
    sme = await make_user(role="SME")
    admin = await make_admin()
    project = await make_project(sme)
    application = await make_loan_application(sme, project["id"])
    await submit_loan_application(sme, application["id"])

    score_start = await client.post(
        "/underwriting/score-runs",
        json={"application_id": application["id"], "mode": None},
        headers=admin["headers"],
    )
    assert score_start.status_code == 201

    projects_resp = await client.get("/projects", headers=sme["headers"])
    assert projects_resp.status_code == 200
    matching = [p for p in projects_resp.json() if p["id"] == project["id"]]
    assert len(matching) == 1
    assert matching[0]["loan_application"]["status"] == "UNDER_REVIEW"
