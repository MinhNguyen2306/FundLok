"""docs/specs/banking/account-linking-mock.md section 10 acceptance criteria."""


async def test_place_order_requires_active_linked_account(open_listing, place_order, make_user):
    setup = await open_listing(target_amount="10000.00", min_ticket="1000.00")
    investor = await make_user(role="INVESTOR")

    resp = await place_order(investor, setup["listing"]["id"], amount="1000.00", link_account=False)
    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"] == "No active linked account. Link a bank/e-wallet account before funding."


async def test_place_order_rejects_revoked_only_accounts(open_listing, place_order, make_user, client):
    setup = await open_listing(target_amount="10000.00", min_ticket="1000.00")
    investor = await make_user(role="INVESTOR")

    link_resp = await client.post(
        "/banking/accounts/link",
        json={"account_type": "BANK", "account_number": "0000000000"},
        headers=investor["headers"],
    )
    account_id = link_resp.json()["id"]
    await client.post(f"/banking/accounts/{account_id}/unlink", headers=investor["headers"])

    resp = await place_order(investor, setup["listing"]["id"], amount="1000.00", link_account=False)
    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"] == "No active linked account. Link a bank/e-wallet account before funding."


async def test_place_order_succeeds_with_active_linked_account(open_listing, place_order, make_user):
    setup = await open_listing(target_amount="10000.00", min_ticket="1000.00")
    investor = await make_user(role="INVESTOR")

    resp = await place_order(investor, setup["listing"]["id"], amount="1000.00")
    assert resp.status_code == 201, resp.text
