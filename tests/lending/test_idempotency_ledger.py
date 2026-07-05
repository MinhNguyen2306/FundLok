"""HANDOFF-01 §5 + §3.5: LedgerEntry idempotency (highest-value coverage).

This is the mechanism that will make Brankas at-least-once webhooks safe in
V2 (per HANDOFF-01 §3.5), so it's locked down here against the current sync
implementation.
"""


def test_duplicate_idempotency_key_on_ledger_entry_returns_existing_row(funded_contract, client):
    setup = funded_contract(target_amount="10000.00", min_ticket="1000.00")
    key = "idem-ledger-key-1"
    body = {"contract_id": setup["contract"]["id"], "bank_account": "VN-TEST-0001", "amount": "10000.00"}

    first = client.post(
        "/payments/disbursements", json=body,
        headers={**setup["admin"]["headers"], "Idempotency-Key": key},
    )
    assert first.status_code == 201
    first_id = first.json()["disbursement_id"]

    second = client.post(
        "/payments/disbursements", json=body,
        headers={**setup["admin"]["headers"], "Idempotency-Key": key},
    )
    assert second.status_code == 201
    assert second.json()["disbursement_id"] == first_id


def test_idempotency_key_reused_for_different_contract_returns_409(funded_contract, client):
    setup_a = funded_contract(target_amount="10000.00", min_ticket="1000.00")
    setup_b = funded_contract(target_amount="10000.00", min_ticket="1000.00")
    key = "idem-ledger-key-shared"

    first = client.post(
        "/payments/disbursements",
        json={"contract_id": setup_a["contract"]["id"], "bank_account": "VN-TEST-0001", "amount": "10000.00"},
        headers={**setup_a["admin"]["headers"], "Idempotency-Key": key},
    )
    assert first.status_code == 201

    second = client.post(
        "/payments/disbursements",
        json={"contract_id": setup_b["contract"]["id"], "bank_account": "VN-TEST-0002", "amount": "10000.00"},
        headers={**setup_b["admin"]["headers"], "Idempotency-Key": key},
    )
    assert second.status_code == 409


def test_duplicate_idempotency_key_on_repayment_returns_existing_row(funded_contract, client):
    setup = funded_contract(target_amount="10000.00", min_ticket="1000.00")
    key = "idem-repayment-key-1"
    body = {
        "contract_id": setup["contract"]["id"],
        "amount": "500.00",
        "paid_at": "2026-07-04T00:00:00Z",
        "reference": "test-repayment",
    }

    first = client.post(
        "/payments/repayments", json=body,
        headers={**setup["admin"]["headers"], "Idempotency-Key": key},
    )
    assert first.status_code == 201
    first_id = first.json()["repayment_id"]

    second = client.post(
        "/payments/repayments", json=body,
        headers={**setup["admin"]["headers"], "Idempotency-Key": key},
    )
    assert second.status_code == 201
    assert second.json()["repayment_id"] == first_id
