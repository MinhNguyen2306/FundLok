"""Orders must have a positive amount, independent of min_ticket.

Found by an input-validation sweep of the write surface. `OrderCreate.amount`
carried no bound, and the service's only lower bound was `amount < min_ticket`
— which is skipped entirely when a listing has no min_ticket (the column is
nullable) while `amount > remaining` cannot catch a negative. A negative order
would therefore have been FILLED, decrementing the listing's funded_amount.
"""

import pytest
from sqlalchemy import select

from app.lending.models import Listing, Order


@pytest.mark.parametrize("amount", ["-1000.00", "0", "0.00", "-0.01"])
async def test_non_positive_order_is_rejected(open_listing, make_user, place_order, amount):
    setup = await open_listing(target_amount="10000.00", min_ticket="1000.00")
    investor = await make_user(role="INVESTOR")

    resp = await place_order(investor, setup["listing"]["id"], amount=amount)

    # 422 from the schema bound; the request never reaches the service.
    assert resp.status_code == 422, resp.text


async def test_negative_order_is_rejected_even_without_a_min_ticket(
    open_listing, make_user, place_order, db_session
):
    """The regression case: min_ticket NULL removes the service's lower bound.

    The API refuses to create such a listing (min_ticket must be positive), so
    the column is nulled directly here — which is exactly how a seeded or
    hand-migrated row could look.
    """
    setup = await open_listing(target_amount="10000.00", min_ticket="1000.00")
    listing_id = setup["listing"]["id"]

    listing = (
        await db_session.execute(select(Listing).where(Listing.id == listing_id))
    ).scalar_one()
    listing.min_ticket = None
    db_session.add(listing)
    await db_session.commit()

    investor = await make_user(role="INVESTOR")
    resp = await place_order(investor, listing_id, amount="-5000.00")

    assert resp.status_code == 422, resp.text

    # And nothing was written: no Order row, funded_amount untouched.
    orders = (
        await db_session.execute(select(Order).where(Order.listing_id == listing_id))
    ).scalars().all()
    assert orders == []

    await db_session.refresh(listing)
    assert listing.funded_amount == 0


async def test_a_positive_order_still_works(open_listing, make_user, place_order):
    # Guard against over-tightening: the bound must not break the happy path.
    setup = await open_listing(target_amount="10000.00", min_ticket="1000.00")
    investor = await make_user(role="INVESTOR")

    resp = await place_order(investor, setup["listing"]["id"], amount="1000.00")

    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "FILLED"


@pytest.mark.parametrize(
    "target_amount,min_ticket",
    [("0", "1000.00"), ("-10000.00", "1000.00"), ("10000.00", "0"), ("10000.00", "-5.00")],
)
async def test_listing_amounts_must_be_positive(
    make_admin, make_user, make_project, make_loan_application, submit_loan_application,
    run_and_lock_score, make_contract, approve_kyc_documents, client, target_amount, min_ticket
):
    """Same missing-bound class one level up: a non-positive target_amount used
    to create a listing that no order could ever fill (remaining <= 0)."""
    admin = await make_admin()
    sme = await make_user(role="SME")
    project = await make_project(sme)
    application = await make_loan_application(sme, project["id"])
    await submit_loan_application(sme, application["id"])
    # run_and_lock_score returns the score-run id itself, not a row.
    score_run_id = await run_and_lock_score(admin, application["id"])
    contract = await make_contract(admin, application["id"], score_run_id)
    await approve_kyc_documents(project["id"])

    resp = await client.post(
        "/market/listings",
        json={
            "contract_id": contract["id"],
            "target_amount": target_amount,
            "min_ticket": min_ticket,
        },
        headers=admin["headers"],
    )

    assert resp.status_code == 422, resp.text
