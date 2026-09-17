"""Regression test: repayment distribution across >1 holding must not trip
the ledger's OMNIBUS_CASH pass-through balance check due to per-holding
rounding drift (see app/payments/service.py record_repayment).

Rewritten for T1 (money to integer VND, HANDOFF-03): amounts are whole VND,
there is no sub-unit to round to, so "drift" is now a matter of distributing
whole đồng exactly -- Hamilton's largest-remainder apportionment (see
record_repayment) -- rather than 2-decimal-place rounding.
"""


async def test_repayment_splits_across_uneven_holdings_without_imbalance(
    open_listing, place_order, make_user, client
):
    setup = await open_listing(target_amount="10000000", min_ticket="1000000")
    listing_id = setup["listing"]["id"]

    # Three holdings whose principals sum to the target but split a
    # 100-VND repayment unevenly enough to drift under naive per-leg
    # floor/round: 3,333,333 / 3,333,333 / 3,333,334 sums to 10,000,000;
    # each holding's exact entitlement of a 100 VND repayment is
    # 33.3333.. / 33.3333.. / 33.3334.. VND -- not integers -- so the
    # largest-remainder apportionment must still land on exactly 100.
    investor_a = await make_user(role="INVESTOR")
    investor_b = await make_user(role="INVESTOR")
    investor_c = await make_user(role="INVESTOR")
    for investor, amount in ((investor_a, "3333333"), (investor_b, "3333333"), (investor_c, "3333334")):
        resp = await place_order(investor, listing_id, amount=amount)
        assert resp.status_code == 201, resp.text

    contract_id = setup["contract"]["id"]
    repayment_body = {
        "contract_id": contract_id,
        "amount": "100",
        "paid_at": "2026-07-07T00:00:00Z",
        "reference": "rounding-regression",
    }
    resp = await client.post(
        "/payments/repayments",
        json=repayment_body,
        headers=setup["admin"]["headers"],
    )
    assert resp.status_code == 201, resp.text

    balances = resp.json()["balances"]
    assert len(balances) == 3
    total_distributed = sum(int(b["amount"]) for b in balances)
    assert total_distributed == 100


async def test_repayment_of_one_vnd_across_three_holdings_sums_to_exactly_one(
    open_listing, place_order, make_user, client
):
    """T1 acceptance criterion, verbatim: "a repayment of 1 VND split across
    3 holdings sums to exactly 1." Two of the three holdings' exact
    entitlement floors to 0 -- post_transaction() rejects zero-amount legs,
    so record_repayment must skip those and post the single 1-VND leg to
    whichever holding wins the largest-remainder tie-break, never split
    fractional đồng and never drop the VND entirely.
    """
    setup = await open_listing(target_amount="9000000", min_ticket="1000000")
    listing_id = setup["listing"]["id"]

    investors = [await make_user(role="INVESTOR") for _ in range(3)]
    for investor in investors:
        resp = await place_order(investor, listing_id, amount="3000000")
        assert resp.status_code == 201, resp.text

    contract_id = setup["contract"]["id"]
    repayment_body = {
        "contract_id": contract_id,
        "amount": "1",
        "paid_at": "2026-07-07T00:00:00Z",
        "reference": "one-vnd-regression",
    }
    resp = await client.post(
        "/payments/repayments",
        json=repayment_body,
        headers=setup["admin"]["headers"],
    )
    assert resp.status_code == 201, resp.text

    balances = resp.json()["balances"]
    # Zero-amount legs are never posted -- at most one holding is credited.
    assert len(balances) == 1
    total_distributed = sum(int(b["amount"]) for b in balances)
    assert total_distributed == 1
