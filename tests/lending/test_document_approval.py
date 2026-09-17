"""T15 (HANDOFF-03 GAP-1 / Issue 12) -- KYC document approval endpoint.

Before this, nothing anywhere in the codebase ever set
`Document.status = "APPROVED"` through a real code path (see conftest.py's
`approve_kyc_documents` fixture docstring, which used a direct ORM write as
a stopgap for exactly this gap). These tests exercise the real endpoint.
"""
import uuid

from sqlalchemy import select

from app.lending.kyc import KYC_PURPOSES, project_has_verified_kyc
from app.lending.models import AuditLog, Document


async def _make_pending_document(db_session, project_id: str, purpose: str = "KYC_ID") -> Document:
    doc = Document(
        entity_type="PROJECT",
        entity_id=project_id,
        purpose=purpose,
        filename=f"{purpose}.pdf",
        status="PENDING",
        storage_key=f"test/{project_id}/{purpose}.pdf",
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


async def test_approve_document_sets_status_and_verified_at(make_admin, make_user, make_project, db_session, client):
    admin = await make_admin()
    sme = await make_user(role="SME")
    project = await make_project(sme)
    doc = await _make_pending_document(db_session, project["id"])

    resp = await client.post(
        f"/lending/documents/{doc.id}/approve",
        json={"rationale": "ID matches KYC provider response"},
        headers=admin["headers"],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "APPROVED"
    assert body["verified_at"] is not None

    result = await db_session.execute(select(Document).where(Document.id == doc.id))
    refreshed = result.scalar_one()
    assert refreshed.status == "APPROVED"
    assert refreshed.verified_at is not None


async def test_approve_document_writes_audit_log_with_actor_and_rationale(
    make_admin, make_user, make_project, db_session, client
):
    admin = await make_admin()
    sme = await make_user(role="SME")
    project = await make_project(sme)
    doc = await _make_pending_document(db_session, project["id"])

    resp = await client.post(
        f"/lending/documents/{doc.id}/approve",
        json={"rationale": "manual review passed"},
        headers=admin["headers"],
    )
    assert resp.status_code == 200, resp.text

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.entity_type == "DOCUMENT", AuditLog.entity_id == doc.id)
    )
    log = result.scalar_one()
    assert log.action == "APPROVE"
    assert str(log.actor_id) == admin["id"]
    assert log.after_state["rationale"] == "manual review passed"
    assert log.after_state["status"] == "APPROVED"
    assert log.before_state["status"] == "PENDING"


async def test_approve_document_requires_admin_role(make_user, make_project, db_session, client):
    sme = await make_user(role="SME")
    project = await make_project(sme)
    doc = await _make_pending_document(db_session, project["id"])

    resp = await client.post(
        f"/lending/documents/{doc.id}/approve",
        json={"rationale": "self-approval attempt"},
        headers=sme["headers"],
    )
    assert resp.status_code == 403


async def test_approve_document_not_found_returns_404(make_admin, client):
    admin = await make_admin()
    resp = await client.post(
        f"/lending/documents/{uuid.uuid4()}/approve",
        json={"rationale": "n/a"},
        headers=admin["headers"],
    )
    assert resp.status_code == 404


async def test_approve_document_already_approved_rejected(make_admin, make_user, make_project, db_session, client):
    admin = await make_admin()
    sme = await make_user(role="SME")
    project = await make_project(sme)
    doc = await _make_pending_document(db_session, project["id"])

    first = await client.post(
        f"/lending/documents/{doc.id}/approve",
        json={"rationale": "first pass"},
        headers=admin["headers"],
    )
    assert first.status_code == 200, first.text

    second = await client.post(
        f"/lending/documents/{doc.id}/approve",
        json={"rationale": "second pass"},
        headers=admin["headers"],
    )
    assert second.status_code == 400


async def test_project_passes_kyc_check_and_can_be_listed_after_real_approval(
    make_admin, make_user, make_project, make_loan_application, submit_loan_application,
    run_and_lock_score, make_contract, make_listing, db_session, client,
):
    """The GAP-1 acceptance criterion, verbatim: a project with approved
    documents passes project_has_verified_kyc() and can be listed -- using
    the real approval endpoint end to end, not the conftest ORM shortcut.
    """
    admin = await make_admin()
    sme = await make_user(role="SME")
    project = await make_project(sme)

    assert await project_has_verified_kyc(db_session, project["id"]) is False

    for purpose in KYC_PURPOSES:
        doc = await _make_pending_document(db_session, project["id"], purpose=purpose)
        resp = await client.post(
            f"/lending/documents/{doc.id}/approve",
            json={"rationale": f"{purpose} verified"},
            headers=admin["headers"],
        )
        assert resp.status_code == 200, resp.text

    assert await project_has_verified_kyc(db_session, project["id"]) is True

    application = await make_loan_application(sme, project["id"], requested_amount="10000000")
    submit_resp = await submit_loan_application(sme, application["id"])
    assert submit_resp.status_code == 200, submit_resp.text
    score_run_id = await run_and_lock_score(admin, application["id"])
    contract = await make_contract(admin, application["id"], score_run_id)

    listing = await make_listing(admin, contract["id"], target_amount="10000000", min_ticket="1000000")
    assert listing["status"] == "OPEN"
