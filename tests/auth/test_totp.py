"""Two-factor authentication (TOTP).

The tests that matter most here are the ones proving 2FA is a GATE, not a badge:
a login with the right password but no code must hand out nothing usable, and
the challenge token issued in between must not work as a session. Everything
else — enrolment, recovery codes, disable — is guard rails around that.
"""

import pyotp
import pytest
from sqlalchemy import select

from app.auth import totp, totp_crypto
from app.core.config import settings
from app.users.models import TotpRecoveryCode, User

# The password make_user registers with. Imported rather than retyped so a
# change to the fixture cannot leave these tests failing on a stale literal.
from conftest import DEFAULT_PASSWORD as PASSWORD


def code_for(secret: str) -> str:
    return pyotp.TOTP(secret).now()


async def enrol(client, user) -> tuple[str, list[str]]:
    """Take an account all the way through enrolment. Returns (secret, codes)."""
    setup = await client.post("/auth/2fa/setup", headers=user["headers"])
    assert setup.status_code == 201, setup.text
    secret = setup.json()["secret"]

    enable = await client.post(
        "/auth/2fa/enable",
        json={"code": code_for(secret)},
        headers=user["headers"],
    )
    assert enable.status_code == 200, enable.text
    return secret, enable.json()["recovery_codes"]


# --------------------------------------------------------------------------- #
# The pure layer
# --------------------------------------------------------------------------- #


class TestCodeVerification:
    def test_accepts_the_current_code(self):
        secret = totp.generate_secret()
        assert totp.verify_code(secret, code_for(secret))

    def test_rejects_a_wrong_code(self):
        secret = totp.generate_secret()
        assert not totp.verify_code(secret, "000000")

    def test_tolerates_spaces_because_people_paste_them(self):
        secret = totp.generate_secret()
        current = code_for(secret)
        assert totp.verify_code(secret, f" {current[:3]} {current[3:]} ")

    @pytest.mark.parametrize("bad", ["", "12345", "1234567", "abcdef", "12 34", None])
    def test_rejects_anything_that_is_not_six_digits(self, bad):
        secret = totp.generate_secret()
        assert not totp.verify_code(secret, bad)

    def test_rejects_a_code_from_a_different_secret(self):
        assert not totp.verify_code(
            totp.generate_secret(), code_for(totp.generate_secret())
        )

    def test_rejects_everything_when_there_is_no_secret(self):
        assert not totp.verify_code("", "000000")
        assert not totp.verify_code(None, "000000")

    def test_provisioning_uri_carries_issuer_and_account(self):
        uri = totp.provisioning_uri(totp.generate_secret(), "sme@example.com")
        assert uri.startswith("otpauth://totp/")
        assert "FundLok" in uri
        assert "sme%40example.com" in uri


class TestRecoveryCodes:
    def test_generates_distinct_codes(self):
        codes = totp.generate_recovery_codes()
        assert len(codes) == totp.RECOVERY_CODE_COUNT
        assert len(set(codes)) == len(codes)

    def test_avoids_visually_ambiguous_characters(self):
        # I/L/O/U are excluded so a code read off paper cannot be mistyped.
        for code in totp.generate_recovery_codes():
            assert not (set(code) & set("ILOU"))

    def test_hash_round_trip_ignores_formatting(self):
        code = totp.generate_recovery_codes()[0]
        code_hash = totp.hash_recovery_code(code)
        # Lower case, spaces and dashes are what a human actually types.
        assert totp.recovery_code_matches(code.lower(), code_hash)
        assert totp.recovery_code_matches(f"{code[:5]}-{code[5:]}", code_hash)

    def test_is_hashed_not_stored_plainly(self):
        code = totp.generate_recovery_codes()[0]
        assert code not in totp.hash_recovery_code(code)


class TestChallengeToken:
    def test_round_trips_the_user_id(self):
        token = totp.create_challenge_token("11111111-1111-1111-1111-111111111111")
        assert (
            totp.verify_challenge_token(token)
            == "11111111-1111-1111-1111-111111111111"
        )

    def test_rejects_a_token_minted_for_another_purpose(self):
        from app.utils.jwt import create_password_reset_token

        with pytest.raises(Exception):
            totp.verify_challenge_token(create_password_reset_token("abc"))

    def test_rejects_garbage(self):
        with pytest.raises(Exception):
            totp.verify_challenge_token("not-a-jwt")


# --------------------------------------------------------------------------- #
# Enrolment
# --------------------------------------------------------------------------- #


async def test_setup_returns_a_secret_and_a_scannable_uri(client, make_user):
    user = await make_user(role="INVESTOR")

    resp = await client.post("/auth/2fa/setup", headers=user["headers"])

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["secret"]
    assert body["provisioning_uri"].startswith("otpauth://totp/")


async def test_setup_alone_does_not_enable_anything(client, make_user, db_session):
    # An abandoned setup must never lock anyone out of their account.
    user = await make_user(role="INVESTOR")
    await client.post("/auth/2fa/setup", headers=user["headers"])

    status_resp = await client.get("/auth/2fa", headers=user["headers"])
    assert status_resp.json()["enabled"] is False

    # ...and login still works with just a password.
    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    assert login.status_code == 200
    assert "totp_required" not in login.json()


async def test_enable_requires_a_valid_code(client, make_user):
    user = await make_user(role="INVESTOR")
    await client.post("/auth/2fa/setup", headers=user["headers"])

    resp = await client.post(
        "/auth/2fa/enable", json={"code": "000000"}, headers=user["headers"]
    )

    assert resp.status_code == 400
    assert "not valid" in resp.json()["detail"]


async def test_enable_without_setup_is_refused(client, make_user):
    user = await make_user(role="INVESTOR")

    resp = await client.post(
        "/auth/2fa/enable", json={"code": "123456"}, headers=user["headers"]
    )

    assert resp.status_code == 400


async def test_enable_turns_it_on_and_issues_recovery_codes(client, make_user):
    user = await make_user(role="INVESTOR")
    _, codes = await enrol(client, user)

    assert len(codes) == totp.RECOVERY_CODE_COUNT

    status_resp = await client.get("/auth/2fa", headers=user["headers"])
    body = status_resp.json()
    assert body["enabled"] is True
    assert body["confirmed_at"] is not None
    assert body["recovery_codes_remaining"] == totp.RECOVERY_CODE_COUNT


async def test_recovery_codes_are_stored_hashed(client, make_user, db_session):
    user = await make_user(role="INVESTOR")
    _, codes = await enrol(client, user)

    rows = (
        await db_session.execute(
            select(TotpRecoveryCode).where(TotpRecoveryCode.user_id == user["id"])
        )
    ).scalars().all()

    stored = {row.code_hash for row in rows}
    for code in codes:
        assert code not in stored


async def test_setup_is_refused_once_enabled(client, make_user):
    # Re-minting a live secret would silently break the authenticator the user
    # is currently relying on.
    user = await make_user(role="INVESTOR")
    await enrol(client, user)

    resp = await client.post("/auth/2fa/setup", headers=user["headers"])

    assert resp.status_code == 409


# --------------------------------------------------------------------------- #
# Login — the part that makes 2FA real
# --------------------------------------------------------------------------- #


async def test_password_alone_no_longer_signs_you_in(client, make_user):
    user = await make_user(role="INVESTOR")
    await enrol(client, user)

    resp = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["totp_required"] is True
    assert body["challenge_token"]
    # Nothing usable was issued.
    assert "access_token" not in resp.cookies
    assert "refresh_token" not in resp.cookies


async def test_the_challenge_token_is_not_a_session(client, make_user):
    """The single most important test in this file.

    Every purpose-scoped token in this codebase is signed with the same key as
    an access token. If get_current_user did not reject the `purpose` claim, this
    token would already be a full session and the code step would be optional —
    2FA would be theatre.
    """
    user = await make_user(role="INVESTOR")
    await enrol(client, user)

    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    challenge = login.json()["challenge_token"]

    resp = await client.get(
        "/users/me", headers={"Authorization": f"Bearer {challenge}"}
    )

    assert resp.status_code == 401, "the 2FA challenge token was accepted as a session"


async def test_a_valid_code_completes_the_login(client, make_user):
    user = await make_user(role="INVESTOR")
    secret, _ = await enrol(client, user)

    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    resp = await client.post(
        "/auth/login/2fa",
        json={
            "challenge_token": login.json()["challenge_token"],
            "code": code_for(secret),
        },
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == user["email"]
    assert resp.cookies.get("access_token")
    assert resp.cookies.get("refresh_token")


async def test_a_wrong_code_does_not_complete_the_login(client, make_user):
    user = await make_user(role="INVESTOR")
    await enrol(client, user)

    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    resp = await client.post(
        "/auth/login/2fa",
        json={"challenge_token": login.json()["challenge_token"], "code": "000000"},
    )

    assert resp.status_code == 401
    assert not resp.cookies.get("access_token")


async def test_a_recovery_code_completes_the_login_once(client, make_user):
    user = await make_user(role="INVESTOR")
    _, codes = await enrol(client, user)
    recovery = codes[0]

    first_login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    first = await client.post(
        "/auth/login/2fa",
        json={
            "challenge_token": first_login.json()["challenge_token"],
            "code": recovery,
        },
    )
    assert first.status_code == 200, first.text

    # Second use of the same code must fail — that is what "single-use" means.
    second_login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    second = await client.post(
        "/auth/login/2fa",
        json={
            "challenge_token": second_login.json()["challenge_token"],
            "code": recovery,
        },
    )
    assert second.status_code == 401


async def test_using_a_recovery_code_decrements_the_remaining_count(
    client, make_user
):
    user = await make_user(role="INVESTOR")
    _, codes = await enrol(client, user)

    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    await client.post(
        "/auth/login/2fa",
        json={"challenge_token": login.json()["challenge_token"], "code": codes[0]},
    )

    status_resp = await client.get("/auth/2fa", headers=user["headers"])
    assert (
        status_resp.json()["recovery_codes_remaining"]
        == totp.RECOVERY_CODE_COUNT - 1
    )


async def test_a_forged_challenge_token_is_refused(client, make_user):
    user = await make_user(role="INVESTOR")
    secret, _ = await enrol(client, user)

    resp = await client.post(
        "/auth/login/2fa",
        json={"challenge_token": "not-a-token", "code": code_for(secret)},
    )

    assert resp.status_code == 401


async def test_an_access_token_cannot_stand_in_for_a_challenge_token(
    client, make_user
):
    # The reverse of test_the_challenge_token_is_not_a_session: purpose checks
    # have to hold in both directions, or one token type can impersonate another.
    other = await make_user(role="INVESTOR")
    user = await make_user(role="INVESTOR")
    secret, _ = await enrol(client, user)

    resp = await client.post(
        "/auth/login/2fa",
        json={
            "challenge_token": other["access_token"],
            "code": code_for(secret),
        },
    )

    assert resp.status_code == 401


async def test_a_wrong_password_never_reaches_the_code_step(client, make_user):
    user = await make_user(role="INVESTOR")
    await enrol(client, user)

    resp = await client.post(
        "/auth/login", json={"email": user["email"], "password": "wrong-password"}
    )

    assert resp.status_code == 401
    assert "challenge_token" not in resp.text


async def test_the_sign_in_is_audited_only_after_the_second_factor(
    client, make_user
):
    # A sign-in abandoned at the code prompt must not appear in the security
    # history as a completed sign-in.
    user = await make_user(role="INVESTOR")
    secret, _ = await enrol(client, user)

    before = await client.get("/auth/security-events", headers=user["headers"])
    sign_ins_before = sum(
        1 for e in before.json() if e["action"] == "SIGN_IN"
    )

    # Stop at the challenge.
    await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    midway = await client.get("/auth/security-events", headers=user["headers"])
    assert (
        sum(1 for e in midway.json() if e["action"] == "SIGN_IN")
        == sign_ins_before
    )

    # Now finish it.
    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    await client.post(
        "/auth/login/2fa",
        json={
            "challenge_token": login.json()["challenge_token"],
            "code": code_for(secret),
        },
    )
    after = await client.get("/auth/security-events", headers=user["headers"])
    assert (
        sum(1 for e in after.json() if e["action"] == "SIGN_IN")
        == sign_ins_before + 1
    )


# --------------------------------------------------------------------------- #
# Disable
# --------------------------------------------------------------------------- #


async def test_disable_requires_the_password(client, make_user):
    user = await make_user(role="INVESTOR")
    secret, _ = await enrol(client, user)

    resp = await client.post(
        "/auth/2fa/disable",
        json={"password": "wrong-password", "code": code_for(secret)},
        headers=user["headers"],
    )

    assert resp.status_code == 400
    assert "Password" in resp.json()["detail"]


async def test_disable_requires_a_second_factor_too(client, make_user):
    # A borrowed session plus a leaked password must not be enough to strip the
    # factor that exists to defend against exactly that.
    user = await make_user(role="INVESTOR")
    await enrol(client, user)

    resp = await client.post(
        "/auth/2fa/disable",
        json={"password": PASSWORD, "code": "000000"},
        headers=user["headers"],
    )

    assert resp.status_code == 400


async def test_disable_clears_the_secret_and_the_recovery_codes(
    client, make_user, db_session
):
    user = await make_user(role="INVESTOR")
    secret, _ = await enrol(client, user)

    resp = await client.post(
        "/auth/2fa/disable",
        json={"password": PASSWORD, "code": code_for(secret)},
        headers=user["headers"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["enabled"] is False

    row = (
        await db_session.execute(select(User).where(User.id == user["id"]))
    ).scalar_one()
    await db_session.refresh(row)
    assert row.totp_enabled is False
    assert row.totp_secret is None

    remaining = (
        await db_session.execute(
            select(TotpRecoveryCode).where(TotpRecoveryCode.user_id == user["id"])
        )
    ).scalars().all()
    assert remaining == []

    # And a password-only login works again.
    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    assert login.status_code == 200
    assert "totp_required" not in login.json()


async def test_disable_accepts_a_recovery_code(client, make_user):
    # Losing the phone must not mean losing the account.
    user = await make_user(role="INVESTOR")
    _, codes = await enrol(client, user)

    resp = await client.post(
        "/auth/2fa/disable",
        json={"password": PASSWORD, "code": codes[0]},
        headers=user["headers"],
    )

    assert resp.status_code == 200, resp.text


async def test_disable_is_refused_when_2fa_is_off(client, make_user):
    user = await make_user(role="INVESTOR")

    resp = await client.post(
        "/auth/2fa/disable",
        json={"password": PASSWORD, "code": "000000"},
        headers=user["headers"],
    )

    assert resp.status_code == 400


async def test_every_2fa_endpoint_needs_a_session(client):
    for method, path, body in (
        ("get", "/auth/2fa", None),
        ("post", "/auth/2fa/setup", None),
        ("post", "/auth/2fa/enable", {"code": "123456"}),
        ("post", "/auth/2fa/disable", {"password": PASSWORD, "code": "123456"}),
    ):
        resp = await getattr(client, method)(path, json=body) if body else await getattr(
            client, method
        )(path)
        assert resp.status_code == 401, f"{method.upper()} {path} was reachable"


# --------------------------------------------------------------------------- #
# Encryption at rest
# --------------------------------------------------------------------------- #


class TestSecretEncryption:
    def test_round_trips(self):
        secret = totp.generate_secret()
        assert totp_crypto.decrypt_secret(totp_crypto.encrypt_secret(secret)) == secret

    def test_ciphertext_does_not_contain_the_secret(self):
        secret = totp.generate_secret()
        assert secret not in totp_crypto.encrypt_secret(secret)

    def test_is_versioned_so_a_future_scheme_can_be_told_apart(self):
        assert totp_crypto.encrypt_secret(totp.generate_secret()).startswith("v1:")

    def test_two_encryptions_of_the_same_secret_differ(self):
        # Fernet includes a random IV, so identical secrets do not produce
        # identical rows — otherwise the column would leak which users share a
        # secret (and, with a known plaintext, which secret).
        secret = totp.generate_secret()
        assert totp_crypto.encrypt_secret(secret) != totp_crypto.encrypt_secret(secret)

    def test_a_tampered_value_does_not_decrypt(self):
        stored = totp_crypto.encrypt_secret(totp.generate_secret())
        tampered = stored[:-4] + ("AAAA" if not stored.endswith("AAAA") else "BBBB")
        assert totp_crypto.decrypt_secret(tampered) is None

    def test_a_legacy_plaintext_value_is_not_honoured(self):
        # Accepting unprefixed values would keep the plaintext weakness alive
        # behind a compatibility branch. Such a row forces re-enrolment instead.
        assert totp_crypto.decrypt_secret("JBSWY3DPEHPK3PXP") is None

    def test_empty_values_are_handled(self):
        assert totp_crypto.decrypt_secret(None) is None
        assert totp_crypto.decrypt_secret("") is None

    def test_a_value_from_a_different_key_does_not_decrypt(self):
        # The realistic failure mode: a restored backup meeting a rotated key.
        from cryptography.fernet import Fernet

        other = Fernet(Fernet.generate_key())
        foreign = "v1:" + other.encrypt(b"JBSWY3DPEHPK3PXP").decode()
        assert totp_crypto.decrypt_secret(foreign) is None


async def test_the_stored_secret_is_encrypted_not_plaintext(
    client, make_user, db_session
):
    """The point of the whole module: a database dump must not yield secrets."""
    user = await make_user(role="INVESTOR")

    setup = await client.post("/auth/2fa/setup", headers=user["headers"])
    plaintext_secret = setup.json()["secret"]

    row = (
        await db_session.execute(select(User).where(User.id == user["id"]))
    ).scalar_one()
    await db_session.refresh(row)

    assert row.totp_secret != plaintext_secret
    assert plaintext_secret not in row.totp_secret
    assert row.totp_secret.startswith("v1:")
    # ...and it is still the right secret, decrypted.
    assert totp_crypto.decrypt_secret(row.totp_secret) == plaintext_secret


async def test_login_still_works_end_to_end_with_encryption(client, make_user):
    # Guards the wiring, not the crypto: a decrypt missed on any read path would
    # leave codes silently unverifiable.
    user = await make_user(role="INVESTOR")
    secret, _ = await enrol(client, user)

    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    resp = await client.post(
        "/auth/login/2fa",
        json={
            "challenge_token": login.json()["challenge_token"],
            "code": code_for(secret),
        },
    )

    assert resp.status_code == 200, resp.text


async def test_a_corrupt_secret_falls_back_to_recovery_codes(
    client, make_user, db_session
):
    """Fails closed, and leaves a way in.

    Simulates a key rotation without re-encryption, or a mangled row. The TOTP
    path cannot match, so the account is reachable only by recovery code — which
    is the correct outcome, and why recovery codes exist.
    """
    user = await make_user(role="INVESTOR")
    secret, codes = await enrol(client, user)

    row = (
        await db_session.execute(select(User).where(User.id == user["id"]))
    ).scalar_one()
    row.totp_secret = "v1:not-a-valid-fernet-token"
    db_session.add(row)
    await db_session.commit()

    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    challenge = login.json()["challenge_token"]

    # The app's own code no longer works...
    denied = await client.post(
        "/auth/login/2fa",
        json={"challenge_token": challenge, "code": code_for(secret)},
    )
    assert denied.status_code == 401

    # ...but a recovery code does.
    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    allowed = await client.post(
        "/auth/login/2fa",
        json={"challenge_token": login.json()["challenge_token"], "code": codes[0]},
    )
    assert allowed.status_code == 200, allowed.text


async def test_setup_is_refused_when_no_encryption_key_is_configured(
    client, make_user, monkeypatch
):
    """Fail closed: no key, no enrolment — never a plaintext fallback."""
    user = await make_user(role="INVESTOR")
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY", None)

    resp = await client.post("/auth/2fa/setup", headers=user["headers"])

    assert resp.status_code == 503
    # The response must NOT name the setting: that is server configuration, and
    # this endpoint is reachable by any signed-in user. The specific cause goes
    # to the log for whoever is running the server.
    assert "TOTP_ENCRYPTION_KEY" not in resp.text
    assert "temporarily unavailable" in resp.json()["detail"]


async def test_an_invalid_encryption_key_is_reported_not_ignored(
    client, make_user, monkeypatch
):
    user = await make_user(role="INVESTOR")
    monkeypatch.setattr(settings, "TOTP_ENCRYPTION_KEY", "not-a-fernet-key")

    resp = await client.post("/auth/2fa/setup", headers=user["headers"])

    assert resp.status_code == 503
