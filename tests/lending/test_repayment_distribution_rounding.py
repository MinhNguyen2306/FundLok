"""Regression test: repayment distribution across >1 holding must not trip
the ledger's OMNIBUS_CASH pass-through balance check due to per-holding
rounding drift (see app/payments/service.py record_repayment).
"""
from decimal import Decimal


async def test_repayment_splits_across_uneven_holdings_without_imbalance(
    open_listing, place_order, make_user, client
):
    setup = await open_listing(target_amount="10000.00", min_ticket="1000.00")
    listing_id = setup["listing"]["id"]

    # Three holdings whose principals sum to the target but split a 100.00
    # repayment unevenly enough to drift a cent under naive per-leg rounding:
    # 33.3333.. / 33.3333.. / 33.3334.. -> 33.33 + 33.33 + 33.33 = 99.99.
    investor_a = await make_user(role="INVESTOR")
    investor_b = await make_user(role="INVESTOR")
    investor_c = await make_user(role="INVESTOR")
    for investor, amount in ((investor_a, "3333.33"), (investor_b, "3333.33"), (investor_c, "3333.34")):
        resp = await place_order(investor, listing_id, amount=amount)
        assert resp.status_code == 201, resp.text

    contract_id = setup["contract"]["id"]
    repayment_body = {
        "contract_id": contract_id,
        "amount": "100.00",
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
    total_distributed = sum(Decimal(b["amount"]) for b in balances)
    assert total_distributed == Decimal("100.00")
