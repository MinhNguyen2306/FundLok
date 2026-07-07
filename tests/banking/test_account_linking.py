"""docs/specs/banking/account-linking-mock.md acceptance criteria."""


async def test_link_account_happy_path(make_user, client):
    investor = await make_user(role="INVESTOR")
    resp = await client.post(
        "/banking/accounts/link",
        json={"account_type": "BANK", "account_number": "0123456789", "provider": "Vietcombank"},
        headers=investor["headers"],
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["account_ref_masked"] == "**** 6789"
    assert body["status"] == "ACTIVE"
    assert body["provider"] == "Vietcombank"
    assert "0123456789" not in resp.text


async def test_link_account_rejects_blank_account_number(make_user, client):
    sme = await make_user(role="SME")
    resp = await client.post(
        "/banking/accounts/link",
        json={"account_type": "BANK", "account_number": "   "},
        headers=sme["headers"],
    )
    assert resp.status_code == 400, resp.text


async def test_link_account_rejects_invalid_account_type(make_user, client):
    sme = await make_user(role="SME")
    resp = await client.post(
        "/banking/accounts/link",
        json={"account_type": "CRYPTO", "account_number": "0123456789"},
        headers=sme["headers"],
    )
    assert resp.status_code == 400, resp.text


async def test_list_accounts_returns_only_callers_own(make_user, client):
    investor_a = await make_user(role="INVESTOR")
    investor_b = await make_user(role="INVESTOR")
    await client.post(
        "/banking/accounts/link",
        json={"account_type": "EWALLET", "account_number": "9998887776"},
        headers=investor_a["headers"],
    )

    resp_a = await client.get("/banking/accounts", headers=investor_a["headers"])
    resp_b = await client.get("/banking/accounts", headers=investor_b["headers"])
    assert resp_a.status_code == 200
    assert len(resp_a.json()) == 1
    assert resp_b.status_code == 200
    assert resp_b.json() == []


async def test_unlink_account_sets_revoked(make_user, client):
    sme = await make_user(role="SME")
    link_resp = await client.post(
        "/banking/accounts/link",
        json={"account_type": "BANK", "account_number": "1112223334"},
        headers=sme["headers"],
    )
    account_id = link_resp.json()["id"]

    resp = await client.post(f"/banking/accounts/{account_id}/unlink", headers=sme["headers"])
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "REVOKED"


async def test_unlink_is_idempotent(make_user, client):
    sme = await make_user(role="SME")
    link_resp = await client.post(
        "/banking/accounts/link",
        json={"account_type": "BANK", "account_number": "1112223334"},
        headers=sme["headers"],
    )
    account_id = link_resp.json()["id"]

    first = await client.post(f"/banking/accounts/{account_id}/unlink", headers=sme["headers"])
    second = await client.post(f"/banking/accounts/{account_id}/unlink", headers=sme["headers"])
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "REVOKED"


async def test_unlink_other_users_account_returns_404(make_user, client):
    owner = await make_user(role="INVESTOR")
    other = await make_user(role="INVESTOR")
    link_resp = await client.post(
        "/banking/accounts/link",
        json={"account_type": "BANK", "account_number": "1112223334"},
        headers=owner["headers"],
    )
    account_id = link_resp.json()["id"]

    resp = await client.post(f"/banking/accounts/{account_id}/unlink", headers=other["headers"])
    assert resp.status_code == 404, resp.text


async def test_banking_endpoints_reject_admin_role(make_admin, client):
    admin = await make_admin()
    resp = await client.post(
        "/banking/accounts/link",
        json={"account_type": "BANK", "account_number": "0123456789"},
        headers=admin["headers"],
    )
    assert resp.status_code == 403, resp.text
