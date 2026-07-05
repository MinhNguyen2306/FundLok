"""HANDOFF-01 §5: app/utils/rbac.py::require_roles enforcement.

POST /market/listings is gated by require_roles(Role.ADMIN). We send a
syntactically valid body (a real UUID, valid decimals) so the 403 can only be
coming from the role check, not from request body validation (422).
"""
import uuid

import pytest


@pytest.mark.parametrize("role", ["SME", "INVESTOR"])
async def test_role_protected_route_rejects_wrong_role_403(client, make_user, role):
    user = await make_user(role=role)
    resp = await client.post(
        "/market/listings",
        json={"contract_id": str(uuid.uuid4()), "target_amount": "1000.00", "min_ticket": "100.00"},
        headers=user["headers"],
    )
    assert resp.status_code == 403
    assert resp.json() == {"detail": "Not authorized for this action"}


async def test_role_protected_route_rejects_unauthenticated(client):
    resp = await client.post(
        "/market/listings",
        json={"contract_id": str(uuid.uuid4()), "target_amount": "1000.00", "min_ticket": "100.00"},
    )
    assert resp.status_code == 401
