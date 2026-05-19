#!/usr/bin/env python3
"""
Ordered HTTP smoke test for all FundLok API routes.

Dependency order (do not reorder lightly):
  1. Public: health, test-db
  2. Register SME, INVESTOR, then ADMIN (any order among the three, before login)
  3. Login each role → JWT access tokens
  4. Refresh (uses refresh_token from login)
  5. Authenticated reads: GET /users/me
  6. SME creates businesses (POST /sme/businesses then POST /projects for coverage)
  7. GET /projects (SME-only listing in this app)
  8. KYC files: presign → commit for each required purpose
  9. DB: mark KYC documents APPROVED (no public API for this; required for listings)
 10. Loan: create application → submit
 11. Admin underwriting: score run → approve (locks score run)
 12. Admin: create contract
 13. Admin: create listing | Investor: place order (full amount to fund listing)
 14. Admin: disbursement | repayment
 15. Admin: audit log query

Usage (from repo root, API running, .env with DATABASE_URL for KYC approval step):

  python scripts/test_all_endpoints.py

Env:
  FUNDL_API_BASE_URL   default http://127.0.0.1:8000
  FUNDL_API_PASSWORD   default TestPassw0rd!
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def _die(msg: str, resp: httpx.Response | None = None) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    if resp is not None:
        print(resp.status_code, resp.text[:2000], file=sys.stderr)
    raise SystemExit(1)


def approve_kyc_documents(project_id: uuid.UUID) -> None:
    """Set KYC_ID / KYC_ADDRESS / KYC_BUSINESS_REG docs to APPROVED for listing."""
    import app.models  # noqa: F401 — register ORM mappers

    from app.core.database import SessionLocal
    from app.lending.kyc import KYC_PURPOSES
    from app.lending.models import Document

    db = SessionLocal()
    try:
        for purpose in KYC_PURPOSES:
            doc = (
                db.query(Document)
                .filter(
                    Document.entity_type == "PROJECT",
                    Document.entity_id == project_id,
                    Document.purpose == purpose,
                )
                .first()
            )
            if doc is None:
                raise RuntimeError(f"Missing document for purpose {purpose} on project {project_id}")
            doc.status = "APPROVED"
            db.add(doc)
        db.commit()
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ordered FundLok API smoke test")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override FUNDL_API_BASE_URL (default http://127.0.0.1:8000)",
    )
    args = parser.parse_args()

    import os

    base = (args.base_url or os.environ.get("FUNDL_API_BASE_URL") or "http://127.0.0.1:8000").rstrip("/")
    password = os.environ.get("FUNDL_API_PASSWORD", "TestPassw0rd!")
    run_id = uuid.uuid4().hex[:10]

    sme_email = f"sme_{run_id}@example.com"
    investor_email = f"investor_{run_id}@example.com"
    admin_email = f"admin_{run_id}@example.com"

    print("Using base URL:", base)
    print("SME email:", sme_email)
    print("Investor email:", investor_email)
    print("Admin email:", admin_email)

    def j(resp: httpx.Response) -> dict:
        if resp.status_code >= 400:
            _die(f"HTTP {resp.status_code} on {resp.request.method} {resp.request.url}", resp)
        if not resp.content:
            return {}
        return resp.json()

    with httpx.Client(base_url=base, timeout=60.0) as client:
        # --- Public ---
        print("\n1. GET /health")
        j(client.get("/health"))

        print("\n2. GET /test-db")
        j(client.get("/test-db"))

        # --- Register (before any login) ---
        print("\n3. POST /auth/register (SME)")
        j(
            client.post(
                "/auth/register",
                json={
                    "email": sme_email,
                    "password": password,
                    "full_name": "Test SME Owner",
                    "role": "SME",
                },
            )
        )

        print("\n4. POST /auth/register (INVESTOR)")
        j(
            client.post(
                "/auth/register",
                json={
                    "email": investor_email,
                    "password": password,
                    "full_name": "Test Investor",
                    "role": "INVESTOR",
                },
            )
        )

        print("\n5. POST /auth/register (ADMIN)")
        j(
            client.post(
                "/auth/register",
                json={
                    "email": admin_email,
                    "password": password,
                    "full_name": "Test Admin",
                    "role": "ADMIN",
                },
            )
        )

        # --- Login ---
        print("\n6. POST /auth/login (SME)")
        sme_tokens = j(
            client.post("/auth/login", json={"email": sme_email, "password": password})
        )
        sme_auth = {"Authorization": f"Bearer {sme_tokens['access_token']}"}

        print("\n7. POST /auth/login (INVESTOR)")
        investor_tokens = j(
            client.post("/auth/login", json={"email": investor_email, "password": password})
        )
        investor_auth = {"Authorization": f"Bearer {investor_tokens['access_token']}"}

        print("\n8. POST /auth/login (ADMIN)")
        admin_tokens = j(
            client.post("/auth/login", json={"email": admin_email, "password": password})
        )
        admin_auth = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

        print("\n9. POST /auth/refresh")
        refreshed = j(
            client.post("/auth/refresh", json={"refresh_token": sme_tokens["refresh_token"]})
        )
        if not refreshed.get("access_token"):
            _die("Refresh did not return access_token")

        # --- Current user ---
        print("\n10. GET /users/me (SME)")
        j(client.get("/users/me", headers=sme_auth))
        print("\n11. GET /users/me (INVESTOR)")
        j(client.get("/users/me", headers=investor_auth))
        print("\n12. GET /users/me (ADMIN)")
        j(client.get("/users/me", headers=admin_auth))

        # --- SME projects ---
        print("\n13. POST /sme/businesses")
        biz_body = {
            "legal_name": f"Test Biz SME route {run_id}",
            "tax_id": f"TAX-SME-{run_id}",
            "industry": "Software",
        }
        main_project = j(client.post("/sme/businesses", json=biz_body, headers=sme_auth))
        main_project_id = uuid.UUID(main_project["id"])

        print("\n14. POST /projects/")
        extra_project = j(
            client.post(
                "/projects/",
                json={
                    "legal_name": f"Test Biz projects route {run_id}",
                    "tax_id": f"TAX-PRJ-{run_id}",
                },
                headers=sme_auth,
            )
        )
        uuid.UUID(extra_project["id"])  # validate shape

        print("\n15. GET /projects/")
        j(client.get("/projects/", headers=sme_auth))

        # --- Files: KYC triple ---
        kyc_meta = [
            ("KYC_ID", "id.pdf", "application/pdf"),
            ("KYC_ADDRESS", "addr.pdf", "application/pdf"),
            ("KYC_BUSINESS_REG", "reg.pdf", "application/pdf"),
        ]
        fake_checksum = "0" * 64
        file_step = 16
        for purpose, fname, mime in kyc_meta:
            print(f"\n{file_step}. POST /files/presign ({purpose})")
            file_step += 1
            pres = j(
                client.post(
                    "/files/presign",
                    headers=sme_auth,
                    json={
                        "business_id": str(main_project_id),
                        "purpose": purpose,
                        "filename": fname,
                        "mime_type": mime,
                    },
                )
            )
            fid = uuid.UUID(pres["file_id"])
            print(f"\n{file_step}. POST /files/{fid}/commit ({purpose})")
            file_step += 1
            j(
                client.post(
                    f"/files/{fid}/commit",
                    headers=sme_auth,
                    json={"checksum": fake_checksum, "size": 1024},
                )
            )

        kyc_end_step = 16 + len(kyc_meta) * 2
        print(f"\n{kyc_end_step}. DB: approve KYC documents for listing gate")
        approve_kyc_documents(main_project_id)

        # --- Loan flow (SME) ---
        loan_amount = "10000.00"
        step = kyc_end_step + 1
        print(f"\n{step}. POST /loans/applications")
        application = j(
            client.post(
                "/loans/applications",
                headers=sme_auth,
                json={
                    "business_id": str(main_project_id),
                    "requested_amount": loan_amount,
                    "purpose": "Working capital",
                },
            )
        )
        application_id = uuid.UUID(application["id"])

        step += 1
        print(f"\n{step}. POST /loans/applications/{{id}}/submit")
        j(client.post(f"/loans/applications/{application_id}/submit", headers=sme_auth))

        # --- Underwriting (ADMIN) ---
        step += 1
        print(f"\n{step}. POST /underwriting/score-runs")
        score_run = j(
            client.post(
                "/underwriting/score-runs",
                headers=admin_auth,
                json={"application_id": str(application_id), "mode": "script"},
            )
        )
        score_run_id = uuid.UUID(score_run["id"])

        step += 1
        print(f"\n{step}. POST /underwriting/score-runs/{{id}}/approve")
        j(client.post(f"/underwriting/score-runs/{score_run_id}/approve", headers=admin_auth))

        # --- Contract (ADMIN) ---
        step += 1
        print(f"\n{step}. POST /contracts/")
        contract = j(
            client.post(
                "/contracts/",
                headers=admin_auth,
                json={
                    "application_id": str(application_id),
                    "score_run_id": str(score_run_id),
                    "template_version": "test-1",
                },
            )
        )
        contract_id = uuid.UUID(contract["id"])

        # --- Market ---
        step += 1
        print(f"\n{step}. POST /market/listings")
        listing = j(
            client.post(
                "/market/listings",
                headers=admin_auth,
                json={
                    "contract_id": str(contract_id),
                    "target_amount": loan_amount,
                    "min_ticket": "1000.00",
                },
            )
        )
        listing_id = uuid.UUID(listing["id"])

        step += 1
        print(f"\n{step}. POST /market/listings/{{id}}/orders (full fill)")
        idem_order = f"order-{run_id}"
        j(
            client.post(
                f"/market/listings/{listing_id}/orders",
                headers={**investor_auth, "Idempotency-Key": idem_order},
                json={"amount": loan_amount, "ackRiskDisclosure": True},
            )
        )

        # --- Payments (ADMIN) ---
        step += 1
        print(f"\n{step}. POST /payments/disbursements")
        j(
            client.post(
                "/payments/disbursements",
                headers={**admin_auth, "Idempotency-Key": f"disb-{run_id}"},
                json={
                    "contract_id": str(contract_id),
                    "bank_account": "TEST-IBAN-001",
                    "amount": loan_amount,
                },
            )
        )

        step += 1
        print(f"\n{step}. POST /payments/repayments")
        j(
            client.post(
                "/payments/repayments",
                headers={**admin_auth, "Idempotency-Key": f"repay-{run_id}"},
                json={
                    "contract_id": str(contract_id),
                    "amount": "500.00",
                    "paid_at": datetime.now(timezone.utc).isoformat(),
                    "reference": "script-test",
                },
            )
        )

        step += 1
        print(f"\n{step}. GET /admin/audit-logs")
        logs = j(client.get("/admin/audit-logs", headers=admin_auth, params={"limit": 50}))
        print(f"    ({len(logs)} log rows)")

    print("\nAll steps completed OK.")


if __name__ == "__main__":
    main()
