"""Password change and sign-in alerts — the two protections on
/dashboard/security that now have a backend.

The password-change endpoint is deliberately separate from /users/me/password:
that one only ever sets a FIRST password (overwriting an existing one from a
borrowed session would be account takeover), so changing an existing password
requires the current one as proof the session is not borrowed.
"""
import pytest
from sqlalchemy import select

from app.users.models import RefreshToken, User
from conftest import auth_headers

CHROME = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)
EDGE_WINDOWS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
)


# --- change password -------------------------------------------------------


async def test_change_password_requires_the_current_one(client, make_user):
    user = await make_user()
    resp = await client.post(
        "/users/me/password/change",
        json={"current_password": "not-the-password", "new_password": "NewPassw0rd!"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"] == "Current password is incorrect"


async def test_change_password_succeeds_and_the_new_one_works(client, make_user):
    user = await make_user()
    resp = await client.post(
        "/users/me/password/change",
        json={"current_password": user["password"], "new_password": "NewPassw0rd!"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 200, resp.text

    old = await client.post(
        "/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    assert old.status_code == 401, "the old password must stop working"

    new = await client.post(
        "/auth/login", json={"email": user["email"], "password": "NewPassw0rd!"}
    )
    assert new.status_code == 200, new.text


async def test_change_password_revokes_every_other_session(
    client, make_user, db_session
):
    """Changing a password because someone else is in the account achieves
    nothing if their session keeps working — refresh tokens are independent of
    the password."""
    user = await make_user()
    # A second sign-in = a second live session.
    await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"]},
        headers={"user-agent": EDGE_WINDOWS},
    )

    live_before = (
        await db_session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user["id"],
                RefreshToken.revoked_at.is_(None),
            )
        )
    ).scalars().all()
    assert len(live_before) >= 2

    resp = await client.post(
        "/users/me/password/change",
        json={"current_password": user["password"], "new_password": "NewPassw0rd!"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["sessions_revoked"] >= 2

    live_after = (
        await db_session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user["id"],
                RefreshToken.revoked_at.is_(None),
            )
        )
    ).scalars().all()
    assert live_after == []


async def test_change_password_rejects_reusing_the_same_password(client, make_user):
    user = await make_user()
    resp = await client.post(
        "/users/me/password/change",
        json={"current_password": user["password"], "new_password": user["password"]},
        headers=auth_headers(user),
    )
    assert resp.status_code == 400, resp.text
    assert "different" in resp.json()["detail"]


async def test_change_password_rejects_a_short_new_password(client, make_user):
    user = await make_user()
    resp = await client.post(
        "/users/me/password/change",
        json={"current_password": user["password"], "new_password": "short"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 422, resp.text


async def test_change_password_requires_authentication(client):
    resp = await client.post(
        "/users/me/password/change",
        json={"current_password": "x", "new_password": "NewPassw0rd!"},
    )
    assert resp.status_code == 401


async def test_password_change_is_audited(client, make_user):
    user = await make_user()
    await client.post(
        "/users/me/password/change",
        json={"current_password": user["password"], "new_password": "NewPassw0rd!"},
        headers=auth_headers(user),
    )
    # The session cookies were revoked with everything else, so re-authenticate.
    await client.post(
        "/auth/login", json={"email": user["email"], "password": "NewPassw0rd!"}
    )
    events = (
        await client.get("/auth/security-events", headers=auth_headers(user))
    ).json()
    assert any(e["action"] == "PASSWORD_CHANGED" for e in events), events


# --- sign-in alerts --------------------------------------------------------


async def test_signin_alerts_default_to_off(client, make_user):
    user = await make_user()
    resp = await client.get(
        "/users/me/security-preferences", headers=auth_headers(user)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["signin_alerts_enabled"] is False


async def test_signin_alerts_can_be_toggled(client, make_user):
    user = await make_user()
    on = await client.patch(
        "/users/me/security-preferences",
        json={"signin_alerts_enabled": True},
        headers=auth_headers(user),
    )
    assert on.status_code == 200, on.text
    assert on.json()["signin_alerts_enabled"] is True

    read_back = await client.get(
        "/users/me/security-preferences", headers=auth_headers(user)
    )
    assert read_back.json()["signin_alerts_enabled"] is True


async def test_toggling_alerts_is_audited(client, make_user):
    """Switching alerts OFF is what an account takeover would do, so the change
    itself has to appear in the security history."""
    user = await make_user()
    await client.patch(
        "/users/me/security-preferences",
        json={"signin_alerts_enabled": True},
        headers=auth_headers(user),
    )
    events = (
        await client.get("/auth/security-events", headers=auth_headers(user))
    ).json()
    assert any(e["action"] == "SIGNIN_ALERTS_CHANGED" for e in events), events


async def test_alert_is_sent_only_for_an_unseen_device(
    client, make_user, db_session, monkeypatch
):
    sent: list[dict] = []

    def _capture(to_email, *, device, browser, ip_address):
        sent.append({"to": to_email, "device": device, "browser": browser})

    # Patch where it is used, not where it is defined.
    monkeypatch.setattr("app.auth.service.send_new_device_signin_alert", _capture)

    user = await make_user()
    await client.patch(
        "/users/me/security-preferences",
        json={"signin_alerts_enabled": True},
        headers=auth_headers(user),
    )

    # First sign-in from this UA -> unseen -> alert.
    await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"]},
        headers={"user-agent": EDGE_WINDOWS},
    )
    assert len(sent) == 1, sent
    assert sent[0]["device"] == "Windows PC"
    assert sent[0]["browser"] == "Edge 139"

    # Same UA again -> already seen -> no second alert.
    await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"]},
        headers={"user-agent": EDGE_WINDOWS},
    )
    assert len(sent) == 1, "a familiar device must not alert"


async def test_no_alert_when_the_preference_is_off(client, make_user, monkeypatch):
    sent: list[dict] = []
    monkeypatch.setattr(
        "app.auth.service.send_new_device_signin_alert",
        lambda *a, **k: sent.append(k),
    )

    user = await make_user()
    await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"]},
        headers={"user-agent": EDGE_WINDOWS},
    )
    assert sent == [], "alerts are opt-in"
