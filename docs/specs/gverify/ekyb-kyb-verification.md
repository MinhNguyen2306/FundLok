# Spec: GVerify (Datatrust) eKYB — business verification for SMEs

| Field | Value |
|---|---|
| **Status** | DRAFT |
| **Owner** | Phat |
| **Implementer(s)** | Phat (backend module + frontend) — Edward to review (verification domain) |
| **Module** | `app/gverify/` (extends the existing module) |
| **Version** | 1.0 |
| **Date** | 2026-07-14 |
| **Related ADR** | — (same provider decision as ekyc-kyc-verification.md) |
| **Depends on** | `docs/specs/gverify/ekyc-kyc-verification.md` (client, config, patterns) · GVerify/GHub API v2.5.1 §eKYB |

---

## 1. Context & Goal

SMEs currently verify their business through Didit's hosted KYB flow. GVerify's
eKYB APIs let us replace it with a stronger, Vietnam-native check in one
round-trip:

1. **OCR X** (`POST {base}/ekyb/api/ocrx/decode`) — reads the business
   registration certificate (Giấy đăng ký kinh doanh; JPEG/PNG/PDF) and
   extracts the business name, tax code, address, owner, charter capital and
   the legal representatives (each with CCCD number), all with confidences.
2. **Tax Code Verify** (`POST {base}/ekyb/api/taxcode/verify`) — validates the
   extracted tax code against the government registry (Tổng Cục Thuế) and
   returns the registered name, address, status and representative.

The combination is materially better than document-OCR alone: we prove the
certificate is real **and currently active** in the state registry, and we can
cross-match the registry/certificate against what the SME declared in FundLok
and against the owner's personal KYC identity.

**Goal:** An SME can verify their business in one request — upload the
registration certificate, FundLok orchestrates OCR X + Tax Code Verify +
cross-checks, and stores an APPROVED/REJECTED verdict with the extracted
company profile.

---

## 2. Out of Scope

- GTIN product lookup (`/ekyb/api/gtin/lookup`) — product verification, not KYB.
- `OCR X Decode Address` (63→34 province conversion) — addresses stored verbatim.
- Invoice registration/lookup APIs.
- Replacing the *document upload* trail in `app/uploads` / `app/lending/kyc.py`
  (`KYC_BUSINESS_REG` purpose docs) — see Open Question 4 for how they relate.
- Retiring the Didit KYB flow — both run in parallel until this spec is
  accepted and the cut-over is decided (mirrors the KYC provider strategy).
- The phone QR handoff for KYB (the certificate is usually a PDF/scan on the
  desktop; handoff can be added later reusing the KYC token pattern).

---

## 3. Data Model

### New Table: `gverify_kyb_verifications`

Separate from `gverify_verifications` — the payload shape is business-, not
person-shaped. Same append-per-attempt pattern: newest row per user = current
state; retries are new rows.

```
gverify_kyb_verifications
├── id                      UUID          PK, default gen_random_uuid()
├── user_id                 UUID          NOT NULL → users(id) ON DELETE CASCADE, indexed
├── status                  TEXT          NOT NULL, server default 'PENDING'
│                                         (app-enforced: PENDING | APPROVED | REJECTED | MANUAL_REVIEW | FAILED)
├── document_type           TEXT          NOT NULL  -- COMPANY | COMPANY_BRANCH (as sent to OCR X; HOUSEHOLD dropped in v1.2)
├── ocr_transaction_code    TEXT          nullable
├── tax_transaction_code    TEXT          nullable
├── tax_code                TEXT          nullable, indexed  -- from OCR, confirmed by registry
├── business_name           TEXT          nullable
├── business_type           TEXT          nullable
├── company_address         TEXT          nullable
├── date_of_establishment   TEXT          nullable  -- verbatim
├── charter_capital         TEXT          nullable  -- verbatim (COMPANY) / business_capital (HOUSEHOLD)
├── representatives         JSONB         nullable  -- OCR X representatives array verbatim
├── ocr_data                JSONB         nullable  -- full OCR X {data}
├── tax_data                JSONB         nullable  -- full Tax Verify {data}
├── rejection_reason        TEXT          nullable
├── created_at              TIMESTAMPTZ   DEFAULT NOW()
└── updated_at              TIMESTAMPTZ   DEFAULT NOW() (onupdate NOW())
```

### Alembic Migration

New revision chained off current head (hash id assigned at implementation).

### Settings (reuses all `GVERIFY_*` from the KYC spec, plus)

```
GVERIFY_MIN_KYB_OCR_CONFIDENCE   float   default 0.85 — min name/tax_code confidence
GVERIFY_KYB_REQUIRE_REP_MATCH    bool    default false — require the SME's KYC person_number
                                          to appear among the certificate's representatives
                                          (see Business Rule 7 / Open Question 2)
```

---

## 4. API Contract

### `POST /gverify/kyb/verify`

**Auth:** Bearer JWT — role: `SME`

One-shot KYB: OCR the certificate, verify the tax code against the registry,
cross-check, return the verdict synchronously.

**Request**
```json
{
  "document_b64": "string",       // required — JPEG | PNG | PDF, decoded ≤ 10MB
  "document_type": "COMPANY"      // required — COMPANY | COMPANY_BRANCH
}
```

**Response 201**
```json
{
  "verification_id": "uuid",
  "status": "APPROVED",              // APPROVED | REJECTED
  "is_approved": true,
  "rejection_reason": null,
  "tax_code": "0312345678",
  "business_name": "CÔNG TY TNHH ...",
  "business_type": "Công ty TNHH",
  "business_status": "Đang hoạt động",   // from the registry (tax_data)
  "representatives": [ { "name": "...", "id_number": "..." } ],
  "created_at": "2026-07-14T00:00:00Z"
}
```

**Error Responses**

| Status | Condition |
|---|---|
| 400 | document not valid base64, not JPEG/PNG/PDF, > 10MB, or unknown document_type |
| 401 | missing/invalid JWT |
| 403 | role is not SME |
| 409 | latest attempt already APPROVED |
| 422 | Pydantic validation failure |
| 502 | GVerify unreachable / success=false — attempt persisted FAILED |

### `GET /gverify/kyb/status`

**Auth:** Bearer JWT — role: `SME`. Returns the latest attempt (404 = never
attempted). Same shape as the KYC status plus `tax_code`, `business_name`.

### Upstream calls (GVerify API v2.5.1, for reference)

- `POST {base}/ekyb/api/ocrx/decode` — **multipart/form-data** (`file`,
  `type`); `code` travels as a **header** on this endpoint (unlike the base64
  eKYC endpoints where it is a JSON field). No base64 variant is documented —
  the backend client must send multipart (httpx `files=`; sending multipart
  does not require `python-multipart`, which is only for *receiving* it).
- `POST {base}/ekyb/api/taxcode/verify` — JSON `{ID, tax_type: "COMPANY", code}`.
- Both return the `{success, error, data}` envelope; same error handling as KYC.

---

## 5. State Machine

Per-attempt, terminal within the creating request (same as KYC):

```
PENDING ──[OCR + registry + cross-checks pass]───────────► APPROVED
PENDING ──[hard failure: unreadable doc, invalid tax
           code, inactive business, rep-flag violation]──► REJECTED
PENDING ──[borderline: low OCR confidence, registry
           cross-check mismatch or incomplete data]──────► MANUAL_REVIEW
PENDING ──[provider HTTP error / success=false]──────────► FAILED
```

`MANUAL_REVIEW` (added v1.2 per the provider integration guide) is terminal
for the attempt: an ops decision resolves it out-of-band. The FE shows the
"under review" screen; retries are not blocked (only APPROVED 409s).

Retry = new row; latest APPROVED ⇒ 409 on further attempts.

---

## 6. Business Rules

1. Only `SME` may call the KYB endpoints (mirrors Didit `/kyb/*`).
2. The document must be valid base64 decoding to JPEG, PNG (magic bytes) or
   PDF (`%PDF`), ≤ 10MB. `document_type` must be one of the three OCR X types.
3. **OCR pass:** envelope success, `name` and `tax_code` non-empty, and — where
   parseable — `name_confidence` and `tax_code_confidence` ≥
   `GVERIFY_MIN_KYB_OCR_CONFIDENCE`.
4. **Registry pass:** Tax Code Verify `is_valid` is true AND
   `business_status_en` (fallback `business_status`) indicates an active
   business. Inactive/suspended/dissolved ⇒ REJECTED with the registry status
   in the reason.
5. **Name cross-check:** normalised OCR `name` must equal the registry
   `company.name` (case-, diacritic- and whitespace-insensitive). Mismatch ⇒
   REJECTED ("certificate does not match the tax registry").
6. The Tax Code Verify call is skipped when OCR already failed (fail fast,
   one less billable call — same pattern as KYC's face-match skip).
7. **Representative link (flag-gated):** when `GVERIFY_KYB_REQUIRE_REP_MATCH`
   is true, the SME user's latest APPROVED GVerify **KYC** `person_number`
   must appear among the certificate's `representatives[].id_number`. This
   binds "verified person" ⇔ "legal representative of the verified business".
   Default off until Edward decides (Open Question 2).
8. Both provider payloads persisted verbatim (JSONB). The certificate is
   retained in R2 under `verification/KYB/{verification_id}/certificate.*`
   (bucket `R2_VERIFICATION_BUCKET`, falling back to `R2_BUCKET`) — v1.1
   decision. Best-effort: a storage outage never blocks the verification.
   Every attempt writes an audit-log entry
   (`GVERIFY_KYB_VERIFICATION` / `VERIFY`).
9. Provider `transaction_code`s stored for reconciliation.
10. Provider-side invalid messages (anti-spoofing etc.) surface verbatim in
    `rejection_reason` — never masked by a generic message (lesson from the
    KYC face-check bug, live incident 2026-07-13).

---

## 7. Error Cases

| Scenario | System behaviour | Response |
|---|---|---|
| Bad base64 / wrong type / oversized / bad document_type | No row, no provider call | 400 |
| Latest attempt already APPROVED | No row, no provider call | 409 |
| OCR X unreachable / success=false | Row FAILED + reason | 502 |
| OCR confidences low / fields missing | Row REJECTED, tax call skipped | 201 REJECTED |
| Registry `is_valid=false` or business inactive | Row REJECTED with registry status | 201 REJECTED |
| OCR name ≠ registry name | Row REJECTED | 201 REJECTED |
| Rep-match enabled and no KYC-verified representative | Row REJECTED | 201 REJECTED |
| Tax Verify unreachable after OCR succeeded | Row FAILED (OCR fields still stored) | 502 |
| Non-SME caller | — | 403 |

---

## 8. Acceptance Criteria

- [ ] `test_kyb_verify_happy_path_approves` — valid cert, registry active, names match ⇒ 201 APPROVED, company fields persisted
- [ ] `test_kyb_verify_accepts_pdf_document` — `%PDF` magic passes validation
- [ ] `test_kyb_verify_rejects_low_ocr_confidence` — tax call skipped
- [ ] `test_kyb_verify_rejects_missing_tax_code` — OCR without tax_code ⇒ REJECTED
- [ ] `test_kyb_verify_rejects_invalid_tax_code` — registry `is_valid=false` ⇒ REJECTED
- [ ] `test_kyb_verify_rejects_inactive_business` — status not active ⇒ REJECTED with registry status in reason
- [ ] `test_kyb_verify_rejects_name_mismatch` — OCR/registry name divergence ⇒ REJECTED
- [ ] `test_kyb_verify_rep_match_rule` — flag on + no matching representative ⇒ REJECTED; flag off ⇒ APPROVED
- [ ] `test_kyb_verify_conflict_when_already_approved` — 409, no new row
- [ ] `test_kyb_verify_allows_retry_after_rejection`
- [ ] `test_kyb_verify_rejects_unauthorized_role` — INVESTOR ⇒ 403
- [ ] `test_kyb_verify_rejects_bad_document` — 400, no provider call
- [ ] `test_kyb_verify_provider_error_returns_502_and_marks_failed`
- [ ] `test_kyb_status_returns_latest_attempt`
- [ ] `test_kyb_status_not_found_when_never_attempted`

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | Which `business_status` values count as "active"? Need the enumeration from Datatrust (likely "Đang hoạt động" / "Active"); until then match case-insensitively on those two. | Phat → Datatrust | — |
| 2 | Enable the representative-match rule (Rule 7) at launch, or run it in shadow mode (log, don't reject) first? Binds KYC↔KYB but may reject legitimate cases (rep ≠ account owner). | Edward | — |
| 3 | ~~`HOUSEHOLD` in scope?~~ Resolved v1.2: dropped per the provider integration guide (OCR X business verification covers COMPANY / COMPANY_BRANCH). | Edward | Dropped 2026-07-15 |
| 4 | The loan flow gates on uploaded `KYC_BUSINESS_REG` documents (`app/lending/kyc.py`). Should a GVerify-approved KYB satisfy/auto-approve that document requirement? (The "should we store the cert" half is resolved: v1.1 retains it at `verification/KYB/<id>/`.) | Edward | — |
| 5 | Fuzzy name matching (Rule 5): exact-normalised may reject legitimate OCR noise. Threshold-based similarity instead? Start exact, collect rejections, revisit. | Phat | — |
| 6 | Cross-check against the FundLok project's declared `legal_name`/`tax_id` (projects table) — verify-at-KYB or verify-at-project-creation? | Edward | — |
| 7 | Does the demo tenancy (`ehubapi.tpv.vn` / TPVDEMO) include eKYB access, and is Tax Code Verify billed per call (affects fail-fast ordering)? | Phat → Datatrust | — |

---

## 10. Implementation Plan (phases)

1. **Spec review** — Edward reviews this document; resolve Open Questions 2–4
   before build (1–3 block nothing structurally).
2. **Backend** (`app/gverify/`, extends existing module):
   `client.py` + `ocrx_decode()` (multipart) and `taxcode_verify()`;
   `kyb_service.py` (validation, rules, cross-checks); `models.py` +
   `GVerifyKybVerification`; router `POST /gverify/kyb/verify`,
   `GET /gverify/kyb/status`; migration; `tests/gverify/test_kyb_verify.py`
   per §8 (provider mocked).
3. **Frontend** (Phat): `GVerifyKybClient` on `/kyc` for SMEs (document picker
   incl. PDF + type selector + verdict screens — mirrors the KYC capture
   component structure); services/hooks layers; i18n en+vi.
4. **Cut-over**: switch the SME branch of the `/kyc` role switcher from
   `DiditKycClient` to the new client; middleware gate `/kyb/status` →
   `/gverify/kyb/status`; Didit KYB stays reachable until removal is decided.

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-14 | Phat | Initial draft |
| 1.1 | 2026-07-14 | Phat | Retain the certificate in R2 (`verification/KYB/<id>/`) |
| 1.2 | 2026-07-15 | Phat | Aligned to the provider integration guide: dropped HOUSEHOLD; added MANUAL_REVIEW outcome (low OCR confidence, registry cross-check mismatches/incomplete data); added tax-code echo and legal-representative cross-checks |
