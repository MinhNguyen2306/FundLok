"""GVerify eKYC — acceptance tests for docs/specs/gverify/ekyc-kyc-verification.md.

Test names map 1:1 to the spec's acceptance criteria (§8). The GVerify HTTP
client is always mocked (HANDOFF-01 guardrail: no real provider calls).
"""
import base64
import uuid

import pytest

from app.gverify.client import GVerifyError

# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #

# Minimal bytes that pass the JPEG/PNG magic-byte check.
_JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"fundlok-test-image"
_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fundlok-test-image"


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def _body(**overrides) -> dict:
    body = {
        "id_front_b64": _b64(_JPEG_BYTES),
        "id_back_b64": _b64(_JPEG_BYTES),
        "portrait_b64": _b64(_PNG_BYTES),
    }
    body.update(overrides)
    return body


def _ocr_data(**overrides) -> dict:
    data = {
        "transaction_code": f"TX-OCR-{uuid.uuid4().hex[:8]}",
        "person_number": "079203001234",
        "full_name": "NGUYEN VAN A",
        "date_of_birth": "01/01/1990",
        "front_valid": "true",
        "back_valid": "true",
        "person_number_confidence": "0.99",
        "full_name_confidence": "0.98",
    }
    data.update(overrides)
    return data


def _face_data(**overrides) -> dict:
    data = {
        "transaction_code": f"TX-FACE-{uuid.uuid4().hex[:8]}",
        "is_matching": True,
        "match": "0.93",
    }
    data.update(overrides)
    return data


@pytest.fixture
def mock_gverify(monkeypatch):
    """Replace the GVerify client calls with configurable fakes.

    Returns a controller object: set `.ocr` / `.face` to a dict (returned) or
    an Exception (raised); `.ocr_calls` / `.face_calls` count invocations.
    """

    class _Controller:
        def __init__(self):
            self.ocr = _ocr_data()
            self.face = _face_data()
            self.ocr_calls = 0
            self.face_calls = 0

    ctl = _Controller()

    async def fake_ocr(*, img_front_b64, img_back_b64):
        ctl.ocr_calls += 1
        if isinstance(ctl.ocr, Exception):
            raise ctl.ocr
        return ctl.ocr

    async def fake_face(*, img1_b64, img2_b64):
        ctl.face_calls += 1
        if isinstance(ctl.face, Exception):
            raise ctl.face
        return ctl.face

    monkeypatch.setattr("app.gverify.client.verify_ocr_id", fake_ocr)
    monkeypatch.setattr("app.gverify.client.face_match", fake_face)
    return ctl


@pytest.fixture
def make_investor(make_user):
    async def _make():
        return await make_user(role="INVESTOR")

    return _make


# --------------------------------------------------------------------------- #
# POST /gverify/kyc/verify
# --------------------------------------------------------------------------- #


async def test_kyc_verify_happy_path_approves(client, make_investor, mock_gverify):
    investor = await make_investor()
    resp = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "APPROVED"
    assert data["is_approved"] is True
    assert data["rejection_reason"] is None
    assert data["person_number"] == "079203001234"
    assert data["full_name"] == "NGUYEN VAN A"
    assert data["date_of_birth"] == "01/01/1990"
    assert data["face_match_score"] == pytest.approx(0.93)
    assert mock_gverify.ocr_calls == 1
    assert mock_gverify.face_calls == 1


async def test_kyc_verify_rejects_invalid_id_card(client, make_investor, mock_gverify):
    investor = await make_investor()
    mock_gverify.ocr = _ocr_data(front_valid="false", front_invalid_message="blurry image")
    resp = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert data["is_approved"] is False
    assert "front not valid" in data["rejection_reason"]
    # Fail fast: the billable face-match call must be skipped.
    assert mock_gverify.face_calls == 0


async def test_kyc_verify_rejects_low_ocr_confidence(client, make_investor, mock_gverify):
    investor = await make_investor()
    mock_gverify.ocr = _ocr_data(person_number_confidence="0.42")
    resp = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert "confidence too low" in data["rejection_reason"]
    assert mock_gverify.face_calls == 0


async def test_kyc_verify_rejects_face_mismatch(client, make_investor, mock_gverify):
    investor = await make_investor()
    mock_gverify.face = _face_data(is_matching=False, match="0.12")
    resp = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert data["rejection_reason"] == "Portrait does not match the ID card photo"
    # OCR identity is still persisted on a face rejection.
    assert data["person_number"] == "079203001234"


async def test_kyc_verify_surfaces_biometric_invalid_message(client, make_investor, mock_gverify):
    """A provider-side face rejection (anti-spoofing etc.) must surface the
    provider's own message, not the generic mismatch text (seen live with
    invalid_code 4: screen-captured / AI-generated document image)."""
    investor = await make_investor()
    mock_gverify.face = _face_data(
        is_matching=False,
        match="-1",
        invalid_code=4,
        invalid_message="Identity document image is either generated by AI or captured on a screen",
    )
    resp = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert data["rejection_reason"] == (
        "Face check failed: Identity document image is either generated by AI "
        "or captured on a screen"
    )


async def test_kyc_verify_rejects_low_face_score(client, make_investor, mock_gverify):
    investor = await make_investor()
    mock_gverify.face = _face_data(is_matching=True, match="0.55")
    resp = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert data["rejection_reason"] == "Face match below threshold"


async def test_kyc_verify_conflict_when_already_approved(client, make_investor, mock_gverify):
    investor = await make_investor()
    first = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert first.status_code == 201 and first.json()["status"] == "APPROVED"

    second = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert second.status_code == 409
    # No new provider calls were made for the rejected duplicate.
    assert mock_gverify.ocr_calls == 1


async def test_kyc_verify_allows_retry_after_rejection(client, make_investor, mock_gverify):
    investor = await make_investor()
    mock_gverify.face = _face_data(is_matching=False)
    first = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert first.status_code == 201 and first.json()["status"] == "REJECTED"

    mock_gverify.face = _face_data()  # matching again
    second = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert second.status_code == 201, second.text
    assert second.json()["status"] == "APPROVED"
    assert second.json()["verification_id"] != first.json()["verification_id"]


async def test_kyc_verify_rejects_unauthorized_role(client, make_user, mock_gverify):
    sme = await make_user(role="SME")
    resp = await client.post("/gverify/kyc/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 403
    assert mock_gverify.ocr_calls == 0


async def test_kyc_verify_rejects_bad_image(client, make_investor, mock_gverify):
    investor = await make_investor()
    # Valid base64 but not a JPEG/PNG payload.
    resp = await client.post(
        "/gverify/kyc/verify",
        json=_body(id_front_b64=_b64(b"just some text, not an image")),
        headers=investor["headers"],
    )
    assert resp.status_code == 400
    assert "JPEG or PNG" in resp.json()["detail"]
    # Not valid base64 at all.
    resp = await client.post(
        "/gverify/kyc/verify",
        json=_body(portrait_b64="!!!not-base64!!!"),
        headers=investor["headers"],
    )
    assert resp.status_code == 400
    assert mock_gverify.ocr_calls == 0


async def test_kyc_verify_rejects_oversized_image(client, make_investor, mock_gverify):
    investor = await make_investor()
    oversized = _JPEG_BYTES + b"\x00" * (10 * 1024 * 1024)
    resp = await client.post(
        "/gverify/kyc/verify",
        json=_body(id_back_b64=_b64(oversized)),
        headers=investor["headers"],
    )
    assert resp.status_code == 400
    assert "10MB" in resp.json()["detail"]
    assert mock_gverify.ocr_calls == 0


async def test_kyc_verify_provider_error_returns_502_and_marks_failed(
    client, make_investor, mock_gverify
):
    investor = await make_investor()
    mock_gverify.ocr = GVerifyError("GVerify /ekyc/api/base64/verify-ocrid returned an error: unknown")
    resp = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert resp.status_code == 502

    # The FAILED attempt is recorded and visible via /status.
    status = await client.get("/gverify/kyc/status", headers=investor["headers"])
    assert status.status_code == 200
    assert status.json()["status"] == "FAILED"
    assert status.json()["is_terminal"] is True


# --------------------------------------------------------------------------- #
# Phone handoff: POST /gverify/kyc/handoff + /gverify/kyc/handoff/verify
# --------------------------------------------------------------------------- #


async def test_kyc_handoff_token_flow_verifies(client, make_investor, mock_gverify):
    investor = await make_investor()
    handoff = await client.post("/gverify/kyc/handoff", headers=investor["headers"])
    assert handoff.status_code == 201, handoff.text
    token = handoff.json()["token"]
    assert handoff.json()["expires_in_seconds"] == 600

    # The "phone": no session cookie, only the handoff token.
    resp = await client.post(
        "/gverify/kyc/handoff/verify",
        json=_body(),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "APPROVED"

    # The desktop session sees the verdict via its own status endpoint.
    status = await client.get("/gverify/kyc/status", headers=investor["headers"])
    assert status.status_code == 200
    assert status.json()["status"] == "APPROVED"


async def test_kyc_handoff_requires_investor_role(client, make_user):
    sme = await make_user(role="SME")
    resp = await client.post("/gverify/kyc/handoff", headers=sme["headers"])
    assert resp.status_code == 403


async def test_kyc_handoff_verify_rejects_bad_token(client, mock_gverify):
    resp = await client.post(
        "/gverify/kyc/handoff/verify",
        json=_body(),
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401
    assert mock_gverify.ocr_calls == 0

    # Missing header entirely.
    resp = await client.post("/gverify/kyc/handoff/verify", json=_body())
    assert resp.status_code == 401


async def test_kyc_handoff_verify_rejects_wrong_purpose_token(
    client, make_investor, mock_gverify
):
    from app.utils.jwt import create_verification_token

    investor = await make_investor()
    # A valid JWT for the same user but minted for email verification — the
    # purpose claim must not be interchangeable.
    wrong_purpose = create_verification_token(investor["id"])
    resp = await client.post(
        "/gverify/kyc/handoff/verify",
        json=_body(),
        headers={"Authorization": f"Bearer {wrong_purpose}"},
    )
    assert resp.status_code == 401
    assert mock_gverify.ocr_calls == 0


async def test_kyc_handoff_verify_conflict_when_already_approved(
    client, make_investor, mock_gverify
):
    investor = await make_investor()
    first = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    assert first.status_code == 201 and first.json()["status"] == "APPROVED"

    handoff = await client.post("/gverify/kyc/handoff", headers=investor["headers"])
    token = handoff.json()["token"]
    resp = await client.post(
        "/gverify/kyc/handoff/verify",
        json=_body(),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


# --------------------------------------------------------------------------- #
# GET /gverify/kyc/status
# --------------------------------------------------------------------------- #


async def test_kyc_status_returns_latest_attempt(client, make_investor, mock_gverify):
    investor = await make_investor()
    mock_gverify.face = _face_data(is_matching=False)
    await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])
    mock_gverify.face = _face_data()
    second = await client.post("/gverify/kyc/verify", json=_body(), headers=investor["headers"])

    resp = await client.get("/gverify/kyc/status", headers=investor["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["verification_id"] == second.json()["verification_id"]
    assert data["status"] == "APPROVED"
    assert data["is_approved"] is True


async def test_kyc_status_not_found_when_never_attempted(client, make_investor):
    investor = await make_investor()
    resp = await client.get("/gverify/kyc/status", headers=investor["headers"])
    assert resp.status_code == 404
