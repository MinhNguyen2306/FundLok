"""POST /projects with an inline loan_application — the shape the SME
application form actually submits.

Regression: the endpoint returns ProjectWithApplicationOut, whose
loan_application carries a `documents` list. On the create path the freshly
inserted LoanApplication had that relationship unloaded, so Pydantic's
model_validate() read triggered a lazy load inside an AsyncSession and raised
MissingGreenlet -> 500 on every create-with-loan request.

The existing `make_project` fixture posts without `loan_application`, which
leaves `loan_app is None` and skips the validation entirely — which is why the
suite stayed green while the real form 500'd. These tests exercise the inline
path directly.
"""
import uuid

from conftest import auth_headers


def _payload(**overrides):
    payload = {
        "legal_name": f"Inline Co {uuid.uuid4().hex[:8]}",
        "tax_id": f"TAX-{uuid.uuid4().hex[:10]}",
        "industry": "IT Services",
        "incorporation_date": "2023-05-10",
        "address": {
            "street": "12 Nguyen Hue",
            "city": "Ho Chi Minh",
            "country": "Vietnam",
        },
        "loan_application": {
            "requested_amount": 800000000,
            "purpose": "Working capital to fulfil new orders",
            "repayment_preference": "MONTHLY",
        },
    }
    payload.update(overrides)
    return payload


async def test_create_project_with_inline_loan_application_returns_201(
    client, make_user
):
    sme = await make_user(role="SME")

    resp = await client.post("/projects", json=_payload(), headers=auth_headers(sme))

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["loan_application"] is not None
    assert body["loan_application"]["status"] == "DRAFT"
    assert body["loan_application"]["project_id"] == body["id"]


async def test_inline_loan_application_documents_serialize_as_empty_list(
    client, make_user
):
    """The `documents` relationship must be loaded, not lazily touched. A new
    application has no documents, so an empty list is the correct answer — the
    bug was that reading it at all raised."""
    sme = await make_user(role="SME")

    resp = await client.post("/projects", json=_payload(), headers=auth_headers(sme))

    assert resp.status_code == 201, resp.text
    assert resp.json()["loan_application"]["documents"] == []


async def test_created_inline_application_is_visible_on_list(client, make_user):
    """The create response and the list endpoint must agree — the list path
    already eager-loaded documents, the create path did not."""
    sme = await make_user(role="SME")
    created = await client.post("/projects", json=_payload(), headers=auth_headers(sme))
    assert created.status_code == 201, created.text
    created_app = created.json()["loan_application"]

    listed = await client.get("/projects", headers=auth_headers(sme))
    assert listed.status_code == 200, listed.text
    projects = listed.json()
    assert len(projects) == 1
    listed_app = projects[0]["loan_application"]

    assert listed_app["id"] == created_app["id"]
    assert listed_app["requested_amount"] == created_app["requested_amount"]
    assert listed_app["documents"] == created_app["documents"]


async def test_create_project_without_loan_application_still_works(
    client, make_user
):
    """The inline block is optional; omitting it must not start returning one."""
    sme = await make_user(role="SME")
    payload = _payload()
    payload.pop("loan_application")

    resp = await client.post("/projects", json=payload, headers=auth_headers(sme))

    assert resp.status_code == 201, resp.text
    assert resp.json()["loan_application"] is None


async def test_public_listing_carries_the_loan_terms(client, make_user, db_session):
    """FE-008: the marketplace card shows the asking amount, so the public
    listing has to carry the application — otherwise an investor must open every
    project to find out what the deal is."""
    from sqlalchemy import select

    from app.lending.models import Project

    sme = await make_user(role="SME")
    created = await client.post("/projects", json=_payload(), headers=auth_headers(sme))
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]

    # Only ACTIVE projects are listed; creation leaves them DRAFT.
    row = (
        await db_session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one()
    row.status = "ACTIVE"
    await db_session.commit()

    investor = await make_user(role="INVESTOR")
    listed = await client.get("/projects/public", headers=auth_headers(investor))
    assert listed.status_code == 200, listed.text

    match = next(p for p in listed.json() if p["id"] == project_id)
    assert match["loan_application"] is not None
    assert match["loan_application"]["requested_amount"] == "800000000.00"
    assert match["loan_application"]["documents"] == []


async def test_public_listing_without_an_application_returns_null(
    client, make_user, db_session
):
    from sqlalchemy import select

    from app.lending.models import Project

    sme = await make_user(role="SME")
    payload = _payload()
    payload.pop("loan_application")
    created = await client.post("/projects", json=payload, headers=auth_headers(sme))
    project_id = created.json()["id"]

    row = (
        await db_session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one()
    row.status = "ACTIVE"
    await db_session.commit()

    investor = await make_user(role="INVESTOR")
    listed = await client.get("/projects/public", headers=auth_headers(investor))
    match = next(p for p in listed.json() if p["id"] == project_id)
    assert match["loan_application"] is None
