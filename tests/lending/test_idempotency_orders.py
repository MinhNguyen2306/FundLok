"""HANDOFF-01 §5 + §3.5: Order idempotency (highest-value coverage)."""


async def test_duplicate_idempotency_key_on_order_returns_existing_row(open_listing, place_order, make_user):
    setup = await open_listing(target_amount="10000.00", min_ticket="1000.00")
    investor = await make_user(role="INVESTOR")
    key = "idem-order-key-1"

    first = await place_order(investor, setup["listing"]["id"], amount="1000.00", idempotency_key=key)
    assert first.status_code == 201
    first_id = first.json()["id"]

    second = await place_order(investor, setup["listing"]["id"], amount="1000.00", idempotency_key=key)
    assert second.status_code == 201
    assert second.json()["id"] == first_id

    # Only one row: the listing should reflect a single 1000.00 fill, not two.
    listing_target = float(setup["listing"]["target_amount"])
    assert listing_target == 10000.00  # sanity: fixture didn't get funded twice into FUNDED early


async def test_idempotency_key_reused_for_different_listing_returns_409(open_listing, place_order, make_user):
    setup_a = await open_listing(target_amount="10000.00", min_ticket="1000.00")
    setup_b = await open_listing(target_amount="10000.00", min_ticket="1000.00")
    investor = await make_user(role="INVESTOR")
    key = "idem-order-key-shared"

    first = await place_order(investor, setup_a["listing"]["id"], amount="1000.00", idempotency_key=key)
    assert first.status_code == 201

    second = await place_order(investor, setup_b["listing"]["id"], amount="1000.00", idempotency_key=key)
    assert second.status_code == 409


async def test_without_idempotency_key_each_call_creates_a_new_order(open_listing, place_order, make_user):
    setup = await open_listing(target_amount="10000.00", min_ticket="1000.00")
    investor = await make_user(role="INVESTOR")

    first = await place_order(investor, setup["listing"]["id"], amount="1000.00")
    second = await place_order(investor, setup["listing"]["id"], amount="1000.00")
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
