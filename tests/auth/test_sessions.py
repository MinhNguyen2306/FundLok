"""Signed-in devices and security history — /dashboard/security's backend.

A refresh token row is one live sign-in, but it ROTATES: refreshing revokes the
old row and inserts a new one. The property that matters here is that a device
keeps its identity across that rotation, otherwise the security screen would
show a new "device" every 30 minutes.
"""
from conftest import auth_headers

CHROME_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)
SAFARI_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


async def _login(client, user, user_agent: str):
    return await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"]},
        headers={"user-agent": user_agent},
    )


async def test_sessions_lists_the_signed_in_device(client, make_user):
    user = await make_user()
    await _login(client, user, CHROME_MAC)

    resp = await client.get("/auth/sessions", headers=auth_headers(user))
    assert resp.status_code == 200, resp.text
    sessions = resp.json()
    assert len(sessions) >= 1

    mine = [s for s in sessions if s["device"] == "Mac"]
    assert mine, sessions
    assert mine[0]["browser"] == "Chrome 141"


async def test_user_agent_is_parsed_into_device_and_browser(client, make_user):
    user = await make_user()
    await _login(client, user, SAFARI_IPHONE)

    sessions = (await client.get("/auth/sessions", headers=auth_headers(user))).json()
    iphone = [s for s in sessions if s["device"] == "iPhone"]
    assert iphone, sessions
    assert iphone[0]["browser"] == "Safari 17"


async def test_session_survives_a_token_refresh(client, make_user):
    """The regression this feature would otherwise ship with: rotation must not
    make the same device look like a new one."""
    user = await make_user()
    await _login(client, user, CHROME_MAC)
    before = (await client.get("/auth/sessions", headers=auth_headers(user))).json()
    ids_before = {s["session_id"] for s in before}

    refreshed = await client.post("/auth/refresh")
    assert refreshed.status_code == 200, refreshed.text

    after = (await client.get("/auth/sessions", headers=auth_headers(user))).json()
    ids_after = {s["session_id"] for s in after}
    assert ids_before == ids_after, "rotation changed the session identity"
    assert len(after) == len(before), "rotation created a duplicate device row"


async def test_revoking_a_session_removes_it_from_the_list(client, make_user):
    user = await make_user()
    # Two sign-ins for the same account = two devices.
    await _login(client, user, CHROME_MAC)
    await _login(client, user, SAFARI_IPHONE)

    sessions = (await client.get("/auth/sessions", headers=auth_headers(user))).json()
    assert len(sessions) >= 2
    target = next(s for s in sessions if not s["current"])

    revoked = await client.post(
        f"/auth/sessions/{target['session_id']}/revoke",
        headers=auth_headers(user),
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["revoked"] >= 1

    remaining = (await client.get("/auth/sessions", headers=auth_headers(user))).json()
    assert target["session_id"] not in {s["session_id"] for s in remaining}


async def test_cannot_revoke_another_users_session(client, make_user):
    victim = await make_user()
    await _login(client, victim, CHROME_MAC)
    victim_sessions = (
        await client.get("/auth/sessions", headers=auth_headers(victim))
    ).json()
    assert victim_sessions

    attacker = await make_user()
    resp = await client.post(
        f"/auth/sessions/{victim_sessions[0]['session_id']}/revoke",
        headers=auth_headers(attacker),
    )
    # Scoped by user_id, so the row is simply not found for this caller.
    assert resp.status_code == 404, resp.text


async def test_revoke_others_spares_the_calling_session(client, make_user):
    user = await make_user()
    await _login(client, user, SAFARI_IPHONE)
    current = await _login(client, user, CHROME_MAC)
    assert current.status_code == 200

    resp = await client.post("/auth/sessions/revoke-others", headers=auth_headers(user))
    assert resp.status_code == 200, resp.text
    assert resp.json()["revoked"] >= 1

    remaining = (await client.get("/auth/sessions", headers=auth_headers(user))).json()
    # The cookie jar holds the most recent login, so exactly that one survives.
    assert len(remaining) == 1
    assert remaining[0]["current"] is True


async def test_sign_in_is_recorded_as_a_security_event(client, make_user):
    user = await make_user()
    await _login(client, user, CHROME_MAC)

    resp = await client.get("/auth/security-events", headers=auth_headers(user))
    assert resp.status_code == 200, resp.text
    events = resp.json()
    assert any(e["action"] == "SIGN_IN" for e in events), events
    assert all(e["severity"] in {"info", "warning", "critical"} for e in events)


async def test_revoking_a_session_is_recorded(client, make_user):
    user = await make_user()
    await _login(client, user, SAFARI_IPHONE)
    await _login(client, user, CHROME_MAC)
    sessions = (await client.get("/auth/sessions", headers=auth_headers(user))).json()
    target = next(s for s in sessions if not s["current"])
    await client.post(
        f"/auth/sessions/{target['session_id']}/revoke", headers=auth_headers(user)
    )

    events = (
        await client.get("/auth/security-events", headers=auth_headers(user))
    ).json()
    revoked = [e for e in events if e["action"] == "SESSION_REVOKED"]
    assert revoked, events
    assert revoked[0]["severity"] == "warning"


async def test_sessions_require_authentication(client):
    assert (await client.get("/auth/sessions")).status_code == 401
    assert (await client.get("/auth/security-events")).status_code == 401
