"""GVerify eKYB — acceptance tests for docs/specs/gverify/ekyb-kyb-verification.md.

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

_JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"fundlok-kyb-test-certificate"
_PDF_BYTES = b"%PDF-1.7\n" + b"fundlok-kyb-test-certificate"


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def _body(**overrides) -> dict:
    body = {"document_b64": _b64(_JPEG_BYTES), "document_type": "COMPANY"}
    body.update(overrides)
    return body


def _ocr_data(**overrides) -> dict:
    data = {
        "transaction_code": f"TX-OCRX-{uuid.uuid4().hex[:8]}",
        "name": "CÔNG TY TNHH FUNDLOK TEST",
        "name_confidence": 0.98,
        "tax_code": "0312345678",
        "tax_code_confidence": 0.99,
        "business_type": "Công ty TNHH",
        "company_address": "123 Lê Lợi, Quận 1, TP.HCM",
        "date_of_establishment": "01/01/2020",
        "charter_capital": "2.000.000.000 đồng",
        # Live payload shape (2026-07-15): identity_number/position, not the
        # documented id_number/title.
        "representatives": [
            {"name": "NGUYEN VAN A", "identity_number": "079203001234", "position": "Giám đốc"},
        ],
    }
    data.update(overrides)
    return data


def _tax_data(**overrides) -> dict:
    data = {
        "transaction_code": f"TX-TAX-{uuid.uuid4().hex[:8]}",
        "is_valid": True,
        "company": {
            "tax_code": "0312345678",
            "name": "CÔNG TY TNHH FUNDLOK TEST",
            "business_status": "Đang hoạt động",
            "business_status_en": "Active",
            "representative": "NGUYEN VAN A",
        },
    }
    data.update(overrides)
    return data


@pytest.fixture
def mock_gverify_kyb(monkeypatch):
    """Replace the eKYB client calls with configurable fakes.

    Set `.ocr` / `.tax` to a dict (returned) or an Exception (raised);
    `.ocr_calls` / `.tax_calls` count invocations.
    """

    class _Controller:
        def __init__(self):
            self.ocr = _ocr_data()
            self.tax = _tax_data()
            self.ocr_calls = 0
            self.tax_calls = 0
            self.last_ocr_kwargs = None
            self.last_tax_kwargs = None

    ctl = _Controller()

    async def fake_ocr(**kwargs):
        ctl.ocr_calls += 1
        ctl.last_ocr_kwargs = kwargs
        if isinstance(ctl.ocr, Exception):
            raise ctl.ocr
        return ctl.ocr

    async def fake_tax(**kwargs):
        ctl.tax_calls += 1
        ctl.last_tax_kwargs = kwargs
        if isinstance(ctl.tax, Exception):
            raise ctl.tax
        return ctl.tax

    monkeypatch.setattr("app.gverify.client.ocrx_decode", fake_ocr)
    monkeypatch.setattr("app.gverify.client.taxcode_verify", fake_tax)
    return ctl


@pytest.fixture
def make_sme(make_user):
    async def _make():
        return await make_user(role="SME")

    return _make


# --------------------------------------------------------------------------- #
# POST /gverify/kyb/verify
# --------------------------------------------------------------------------- #


async def test_kyb_verify_happy_path_approves(client, make_sme, mock_gverify_kyb):
    sme = await make_sme()
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "APPROVED"
    assert data["is_approved"] is True
    assert data["rejection_reason"] is None
    assert data["tax_code"] == "0312345678"
    assert data["business_name"] == "CÔNG TY TNHH FUNDLOK TEST"
    assert data["business_status"] == "Active"
    assert data["representatives"][0]["id_number"] == "079203001234"
    assert mock_gverify_kyb.ocr_calls == 1
    assert mock_gverify_kyb.tax_calls == 1


async def test_kyb_verify_accepts_pdf_document(client, make_sme, mock_gverify_kyb):
    sme = await make_sme()
    resp = await client.post(
        "/gverify/kyb/verify",
        json=_body(document_b64=_b64(_PDF_BYTES)),
        headers=sme["headers"],
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "APPROVED"
    # The client must have been handed the PDF content type.
    assert mock_gverify_kyb.last_ocr_kwargs["content_type"] == "application/pdf"


async def test_kyb_verify_low_ocr_confidence_goes_to_manual_review(
    client, make_sme, mock_gverify_kyb
):
    """Low confidence is a borderline case — parked for ops, not rejected
    (provider integration guide outcomes)."""
    sme = await make_sme()
    mock_gverify_kyb.ocr = _ocr_data(tax_code_confidence=0.41)
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "MANUAL_REVIEW"
    assert "confidence too low" in data["rejection_reason"]
    # Fail fast: the billable registry call must be skipped.
    assert mock_gverify_kyb.tax_calls == 0


async def test_kyb_verify_rejects_missing_tax_code(client, make_sme, mock_gverify_kyb):
    sme = await make_sme()
    mock_gverify_kyb.ocr = _ocr_data(tax_code="")
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "REJECTED"
    assert "tax code" in resp.json()["rejection_reason"]
    assert mock_gverify_kyb.tax_calls == 0


async def test_kyb_verify_declared_tax_code_covers_ocr_extraction_gap(
    client, make_sme, mock_gverify_kyb
):
    """Live gap (2026-07-15): OCR returned tax_code:"" for a legible MST. An
    SME-declared MST stands in — still bound by the registry name cross-check."""
    sme = await make_sme()
    mock_gverify_kyb.ocr = _ocr_data(tax_code="")
    resp = await client.post(
        "/gverify/kyb/verify",
        json=_body(tax_code="0312345678"),
        headers=sme["headers"],
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "APPROVED"
    assert data["tax_code"] == "0312345678"
    assert mock_gverify_kyb.tax_calls == 1


async def test_kyb_verify_ocr_tax_code_wins_over_declared(client, make_sme, mock_gverify_kyb):
    sme = await make_sme()
    resp = await client.post(
        "/gverify/kyb/verify",
        json=_body(tax_code="9999999999"),  # OCR extracted 0312345678 — that wins
        headers=sme["headers"],
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "APPROVED"
    assert resp.json()["tax_code"] == "0312345678"


async def test_kyb_verify_rejects_malformed_declared_tax_code(
    client, make_sme, mock_gverify_kyb
):
    sme = await make_sme()
    resp = await client.post(
        "/gverify/kyb/verify",
        json=_body(tax_code="not-a-tax-code"),
        headers=sme["headers"],
    )
    assert resp.status_code == 400
    assert "MST" in resp.json()["detail"]
    assert mock_gverify_kyb.ocr_calls == 0


async def test_kyb_verify_rejects_invalid_tax_code(client, make_sme, mock_gverify_kyb):
    sme = await make_sme()
    mock_gverify_kyb.tax = _tax_data(is_valid=False)
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert data["rejection_reason"] == "Tax code is not valid in the state registry"


async def test_kyb_verify_rejects_inactive_business(client, make_sme, mock_gverify_kyb):
    sme = await make_sme()
    mock_gverify_kyb.tax = _tax_data(
        company={
            "name": "CÔNG TY TNHH FUNDLOK TEST",
            "business_status": "Đã giải thể",
            "business_status_en": "Dissolved",
        }
    )
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert "not active" in data["rejection_reason"]
    assert "Dissolved" in data["rejection_reason"]


async def test_kyb_verify_name_mismatch_goes_to_manual_review(client, make_sme, mock_gverify_kyb):
    """A registry/certificate name divergence is adjudicated by a human —
    normalization can't distinguish OCR noise from a genuinely different
    company (guide: minor differences → manual review)."""
    sme = await make_sme()
    mock_gverify_kyb.tax = _tax_data(
        company={
            "tax_code": "0312345678",
            "name": "CÔNG TY CỔ PHẦN KHÁC HOÀN TOÀN",
            "business_status_en": "Active",
            "representative": "NGUYEN VAN A",
        }
    )
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "MANUAL_REVIEW"
    assert "Business name differs" in data["rejection_reason"]


async def test_kyb_verify_tax_code_echo_mismatch_goes_to_manual_review(
    client, make_sme, mock_gverify_kyb
):
    sme = await make_sme()
    mock_gverify_kyb.tax = _tax_data(
        company={
            "tax_code": "9999999999",
            "name": "CÔNG TY TNHH FUNDLOK TEST",
            "business_status_en": "Active",
            "representative": "NGUYEN VAN A",
        }
    )
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "MANUAL_REVIEW"
    assert "Tax code differs" in data["rejection_reason"]


async def test_kyb_verify_representative_mismatch_goes_to_manual_review(
    client, make_sme, mock_gverify_kyb
):
    sme = await make_sme()
    mock_gverify_kyb.tax = _tax_data(
        company={
            "tax_code": "0312345678",
            "name": "CÔNG TY TNHH FUNDLOK TEST",
            "business_status_en": "Active",
            "representative": "TRAN THI B",
        }
    )
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "MANUAL_REVIEW"
    assert "Legal representative differs" in data["rejection_reason"]


async def test_kyb_verify_incomplete_representative_goes_to_manual_review(
    client, make_sme, mock_gverify_kyb
):
    """Registry returned no representative — incomplete data is a review
    case per the guide, not an auto-approve."""
    sme = await make_sme()
    mock_gverify_kyb.tax = _tax_data(
        company={
            "tax_code": "0312345678",
            "name": "CÔNG TY TNHH FUNDLOK TEST",
            "business_status_en": "Active",
        }
    )
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "MANUAL_REVIEW"
    assert "incomplete" in data["rejection_reason"]


async def test_kyb_verify_rep_match_rule(client, make_sme, mock_gverify_kyb, monkeypatch):
    from app.core.config import settings as app_settings

    # Flag ON, no approved KYC for this user -> rejected before the tax call.
    monkeypatch.setattr(app_settings, "GVERIFY_KYB_REQUIRE_REP_MATCH", True)
    sme = await make_sme()
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "REJECTED"
    assert "identity verification" in resp.json()["rejection_reason"]
    assert mock_gverify_kyb.tax_calls == 0

    # Flag OFF -> same certificate approves (fresh user, no KYC needed).
    monkeypatch.setattr(app_settings, "GVERIFY_KYB_REQUIRE_REP_MATCH", False)
    sme2 = await make_sme()
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme2["headers"])
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "APPROVED"


async def test_kyb_verify_conflict_when_already_approved(client, make_sme, mock_gverify_kyb):
    sme = await make_sme()
    first = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert first.status_code == 201 and first.json()["status"] == "APPROVED"

    second = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert second.status_code == 409
    assert mock_gverify_kyb.ocr_calls == 1  # no provider call for the duplicate


async def test_kyb_verify_allows_retry_after_rejection(client, make_sme, mock_gverify_kyb):
    sme = await make_sme()
    mock_gverify_kyb.tax = _tax_data(is_valid=False)
    first = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert first.status_code == 201 and first.json()["status"] == "REJECTED"

    mock_gverify_kyb.tax = _tax_data()
    second = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert second.status_code == 201, second.text
    assert second.json()["status"] == "APPROVED"
    assert second.json()["verification_id"] != first.json()["verification_id"]


async def test_kyb_verify_rejects_unauthorized_role(client, make_user, mock_gverify_kyb):
    investor = await make_user(role="INVESTOR")
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=investor["headers"])
    assert resp.status_code == 403
    assert mock_gverify_kyb.ocr_calls == 0


async def test_kyb_verify_rejects_bad_document(client, make_sme, mock_gverify_kyb):
    sme = await make_sme()
    # Valid base64 but neither image nor PDF.
    resp = await client.post(
        "/gverify/kyb/verify",
        json=_body(document_b64=_b64(b"plain text, not a certificate")),
        headers=sme["headers"],
    )
    assert resp.status_code == 400
    assert "JPEG, PNG or PDF" in resp.json()["detail"]
    # Unknown document_type — including HOUSEHOLD, dropped per the provider
    # integration guide (2026-07-15).
    for bad_type in ("SOLE_TRADER", "HOUSEHOLD"):
        resp = await client.post(
            "/gverify/kyb/verify",
            json=_body(document_type=bad_type),
            headers=sme["headers"],
        )
        assert resp.status_code == 400, bad_type
        assert "document_type" in resp.json()["detail"]
    assert mock_gverify_kyb.ocr_calls == 0


async def test_kyb_verify_provider_error_returns_502_and_marks_failed(
    client, make_sme, mock_gverify_kyb
):
    sme = await make_sme()
    mock_gverify_kyb.ocr = GVerifyError("GVerify /ekyb/api/ocrx/decode returned an error: unknown")
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 502

    status = await client.get("/gverify/kyb/status", headers=sme["headers"])
    assert status.status_code == 200
    assert status.json()["status"] == "FAILED"
    assert status.json()["is_terminal"] is True


# --------------------------------------------------------------------------- #
# GET /gverify/kyb/status
# --------------------------------------------------------------------------- #


async def test_kyb_status_returns_latest_attempt(client, make_sme, mock_gverify_kyb):
    sme = await make_sme()
    mock_gverify_kyb.tax = _tax_data(is_valid=False)
    await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    mock_gverify_kyb.tax = _tax_data()
    second = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])

    resp = await client.get("/gverify/kyb/status", headers=sme["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["verification_id"] == second.json()["verification_id"]
    assert data["status"] == "APPROVED"
    assert data["business_name"] == "CÔNG TY TNHH FUNDLOK TEST"


async def test_kyb_status_not_found_when_never_attempted(client, make_sme):
    sme = await make_sme()
    resp = await client.get("/gverify/kyb/status", headers=sme["headers"])
    assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# Provider contract test (KYB plan §7.3 / §13.1) — guards the verified tax
# request shape so a refactor can't silently revert to the (broken) doc schema.
# --------------------------------------------------------------------------- #


async def test_taxcode_verify_uses_lowercase_id_and_license_code(monkeypatch):
    """The outgoing tax-verify body MUST use lowercase `id` and include
    `license_code` (the working contract). Uppercase `ID` yields the live
    ERROR_01 "Id is null or empty" — this test fails if that regresses."""
    from app.gverify import client as gclient

    captured: dict = {}

    class _Resp:
        status_code = 200

        @staticmethod
        def json():
            return {"success": True, "data": {}}

    class _FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None, headers=None):
            captured["url"] = url
            captured["body"] = json
            return _Resp()

    monkeypatch.setattr(gclient.settings, "GVERIFY_BASE_URL", "https://provider.test")
    monkeypatch.setattr(gclient.settings, "GVERIFY_PARTNER_CODE", "TPVDEMO")
    monkeypatch.setattr(gclient.settings, "GVERIFY_API_KEY", "test-key")
    monkeypatch.setattr(gclient.httpx, "AsyncClient", _FakeAsyncClient)

    await gclient.taxcode_verify(tax_code="1501167629", license_code="41M8041297")

    body = captured["body"]
    assert "id" in body and body["id"] == "1501167629"  # lowercase, per working contract
    assert "ID" not in body  # the doc's uppercase key must NOT be sent
    assert body["license_code"] == "41M8041297"  # required by the working contract
    assert body["tax_type"] == "COMPANY"
    assert body["code"] == "TPVDEMO"  # partner code travels in the body


async def test_kyb_verify_forwards_declared_license_code(client, make_sme, mock_gverify_kyb):
    """A declared license_code reaches the provider call verbatim."""
    sme = await make_sme()
    resp = await client.post(
        "/gverify/kyb/verify",
        json=_body(tax_code="0312345678", license_code="41M8041297"),
        headers=sme["headers"],
    )
    assert resp.status_code == 201, resp.text
    assert mock_gverify_kyb.last_tax_kwargs["license_code"] == "41M8041297"
    assert resp.json()["license_code"] == "41M8041297"


async def test_kyb_verify_invalid_tax_code_error_rejects_not_502(client, make_sme, mock_gverify_kyb):
    """ERROR_23 from the registry is a business rejection, not a transport
    failure — it must be 201 REJECTED, never 502 (KYB plan §10.1)."""
    sme = await make_sme()
    mock_gverify_kyb.tax = GVerifyError("invalid tax code", code="ERROR_23")
    resp = await client.post("/gverify/kyb/verify", json=_body(), headers=sme["headers"])
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "REJECTED"
    assert "not valid in the state registry" in resp.json()["rejection_reason"]
