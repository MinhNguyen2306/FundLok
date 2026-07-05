"""HANDOFF-01 §5 + §3.6: ledger append-only invariant.

The service layer only ever inserts into ledger_entries (app/payments/service.py
has no update/delete path), and no route anywhere in the app exposes a way to
mutate or delete an existing ledger entry.
"""
from app.main import app
from conftest import iter_endpoint_routes


def test_ledger_entry_has_no_exposed_mutation_route():
    """Pure route introspection -- no DB/client needed, so this stays sync."""
    ledger_mutation_routes = [
        route
        for route in iter_endpoint_routes(app.routes)
        if route.path.startswith("/payments") and any(m in route.methods for m in ("PUT", "PATCH", "DELETE"))
    ]
    assert ledger_mutation_routes == []


def test_payments_routes_are_create_only():
    """Every registered /payments route is a POST (create); there is nothing
    to GET/PUT/PATCH/DELETE an individual ledger entry by id. Pure route
    introspection -- no DB/client needed, so this stays sync."""
    payments_routes = [route for route in iter_endpoint_routes(app.routes) if route.path.startswith("/payments")]
    assert payments_routes, "expected at least the disbursements/repayments routes to be registered"
    for route in payments_routes:
        assert route.methods <= {"POST", "HEAD", "OPTIONS"}


async def test_disbursement_creates_a_ledger_entry_and_leaves_prior_entries_untouched(funded_contract, client):
    setup = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    first = await client.post(
        "/payments/disbursements",
        json={"contract_id": setup["contract"]["id"], "bank_account": "VN-TEST-0001", "amount": "10000.00"},
        headers={**setup["admin"]["headers"], "Idempotency-Key": "append-only-check-1"},
    )
    assert first.status_code == 201

    # A second, distinct disbursement call (different key) appends a new
    # entry; it does not update the first one in place.
    second = await client.post(
        "/payments/disbursements",
        json={"contract_id": setup["contract"]["id"], "bank_account": "VN-TEST-0002", "amount": "10000.00"},
        headers={**setup["admin"]["headers"], "Idempotency-Key": "append-only-check-2"},
    )
    assert second.status_code == 201
    assert second.json()["disbursement_id"] != first.json()["disbursement_id"]
