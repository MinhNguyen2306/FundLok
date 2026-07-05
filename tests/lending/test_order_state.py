"""HANDOFF-01 §5 + §3.4: Order state, as reachable via the API.

Known gap (documented for Edward, not fixed here): the Order model defaults
to status="PENDING_PAYMENT" (app/lending/models.py), and HANDOFF-01 assumed a
PENDING_PAYMENT -> FILLED transition plus CANCELLED/EXPIRED terminal states.
Actual behavior: app/market/service.py::place_order always sets status
directly to "FILLED" on successful placement -- PENDING_PAYMENT is never
actually observed, and there is no cancel or expire endpoint anywhere in the
app. These tests characterize what the app does today, not what the model's
default column value implies.
"""
from app.main import app
from conftest import iter_endpoint_routes


def test_order_pending_to_filled(open_listing, place_order, make_user):
    """Named per HANDOFF-01 §5. Characterizes actual behavior -- see module
    docstring: there is no observable PENDING_PAYMENT state in practice, a
    successful placement lands directly on FILLED."""
    setup = open_listing(target_amount="10000.00", min_ticket="1000.00")
    investor = make_user(role="INVESTOR")

    resp = place_order(investor, setup["listing"]["id"], amount="1000.00")
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "FILLED"


def test_order_cannot_transition_from_terminal_state(open_listing, place_order, make_user):
    """Once FILLED, there is no reachable mutation route for an order at all:
    no PATCH/PUT/DELETE is registered under /market for orders."""
    order_mutation_routes = [
        route
        for route in iter_endpoint_routes(app.routes)
        if route.path.startswith("/market") and "order" in route.path
        and any(m in route.methods for m in ("PUT", "PATCH", "DELETE"))
    ]
    assert order_mutation_routes == []


def test_duplicate_idempotency_key_returns_same_order_without_double_charging(open_listing, place_order, make_user):
    """Bonus coverage beyond the literal terminal-state check: placing a
    second order against a FILLED order's key doesn't create a second FILLED
    order or double-fund the listing."""
    setup = open_listing(target_amount="10000.00", min_ticket="1000.00")
    investor = make_user(role="INVESTOR")
    key = "order-terminal-check-1"

    first = place_order(investor, setup["listing"]["id"], amount="1000.00", idempotency_key=key)
    second = place_order(investor, setup["listing"]["id"], amount="1000.00", idempotency_key=key)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
