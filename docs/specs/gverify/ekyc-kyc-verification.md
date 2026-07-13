# Spec: GVerify (Datatrust) eKYC — direct-API KYC verification

| Field | Value |
|---|---|
| **Status** | DRAFT |
| **Owner** | Phat |
| **Implementer(s)** | Phat (backend module + frontend) — Edward to review (verification domain) |
| **Module** | `app/gverify/` |
| **Version** | 1.0 |
| **Date** | 2026-07-13 |
| **Related ADR** | — (candidate ADR: KYC provider selection, Didit vs GVerify) |
| **Depends on** | GVerify/GHub API v2.5.1 (PATK, Confidential, 21/10/2025) |

---

## 1. Context & Goal

FundLok's current KYC (`app/verification/`) is built on Didit's hosted Sessions API:
the user is redirected to Didit's UI and the result arrives via webhook. GVerify
(Datatrust / PATK GHub) is a Vietnamese eKYC provider offering **direct APIs** —
we submit CCCD/CMND images and a portrait ourselves and get a synchronous verdict
(OCR + face match). A domestic provider reads Vietnamese ID cards natively and
aligns better with the Decree 94 sandbox posture.

This spec introduces a **new, parallel module** `app/gverify/`. It does NOT
modify `app/verification/` — both providers coexist until one is chosen; the
Didit module stays the default until this module is accepted and flipped on.

**Goal:** An investor can complete KYC in one round-trip — submit ID front/back
+ portrait, FundLok orchestrates GVerify OCR + face match, and stores an
APPROVED/REJECTED verdict with the extracted identity.

---

## 2. Out of Scope

- KYB (business verification) via GVerify's eKYB APIs (`/ekyb/api/*`) — future spec.
- Liveness checks (active / passive / emotion) — the client leaves room for them;
  the decision flow in v1 is OCR + face match only. See Open Question 2.
- eID chip verification (`/eid/api/*`) and CA digital signing (`/ca/api/*`).
- Address-decoding variants (63→34 province mapping) — we store OCR addresses verbatim.
- Removing or rerouting the existing Didit `/kyc/*` endpoints.
- Any change to how downstream modules consume KYC state (they keep using whatever
  they use today; wiring loan/market gating to this table is a follow-up).

---

## 3. Data Model

### New Table: `gverify_verifications`

One row per verification **attempt** (a user may retry after rejection; the
newest row is the current state — same pattern as `verifications`).

```
gverify_verifications
├── id                     UUID          PK, default gen_random_uuid()
├── user_id                UUID          NOT NULL → users(id) ON DELETE CASCADE, indexed
├── verification_type      TEXT          NOT NULL, server default 'KYC'   -- 'KYB' reserved for the future
├── status                 TEXT          NOT NULL, server default 'PENDING'
│                                        CHECK-like set (app-enforced): PENDING | APPROVED | REJECTED | FAILED
├── ocr_transaction_code   TEXT          nullable  -- GVerify {data}.transaction_code from OCR call
├── face_transaction_code  TEXT          nullable  -- GVerify {data}.transaction_code from face-match call
├── person_number          TEXT          nullable, indexed  -- CCCD/CMND number from OCR
├── full_name              TEXT          nullable
├── date_of_birth          TEXT          nullable  -- stored verbatim as GVerify returns it
├── ocr_data               JSONB         nullable  -- full OCR {data} payload
├── face_data              JSONB         nullable  -- full face-match {data} payload
├── rejection_reason       TEXT          nullable  -- human-readable reason when REJECTED/FAILED
├── created_at             TIMESTAMPTZ   DEFAULT NOW()
└── updated_at             TIMESTAMPTZ   DEFAULT NOW() (onupdate NOW())
```

### Alembic Migration

New revision chained off current head `6f3a29bbd701` (hash-based id assigned at
implementation time).

### Settings (env)

```
GVERIFY_BASE_URL              str        no default in prod; partner-provided {api-base-url}
GVERIFY_API_KEY               str|None   x-api-key header value
GVERIFY_PARTNER_CODE          str|None   partner/subpartner "code" sent per request
GVERIFY_OS_TYPE               str        default "fundlok-backend" (os-type header)
GVERIFY_FACE_MATCH_THRESHOLD  float      default 0.80 — min {data}.match to approve
GVERIFY_MIN_OCR_CONFIDENCE    float      default 0.85 — min person_number/full_name confidence
```

---

## 4. API Contract

### `POST /gverify/kyc/verify`

**Auth:** Bearer JWT — role: `INVESTOR`

One-shot KYC: OCR both card faces, then face-match the portrait against the ID
front. Synchronous — the response carries the final verdict. Images are base64
strings (JSON body, mirroring GVerify's own base64 endpoints; the codebase is
JSON-only, no multipart).

**Request**
```json
{
  "id_front_b64": "string",   // required — JPEG|PNG, decoded size ≤ 10MB
  "id_back_b64": "string",    // required — JPEG|PNG, decoded size ≤ 10MB
  "portrait_b64": "string"    // required — JPEG|PNG, decoded size ≤ 10MB
}
```

**Response 201**
```json
{
  "verification_id": "uuid",
  "status": "APPROVED",             // APPROVED | REJECTED
  "is_approved": true,
  "rejection_reason": null,          // string when REJECTED
  "person_number": "0790XXXXXXXX",   // null when REJECTED before extraction
  "full_name": "NGUYEN VAN A",
  "date_of_birth": "01/01/1990",
  "face_match_score": 0.93,          // null if face step not reached
  "created_at": "2026-07-13T00:00:00Z"
}
```

**Error Responses**

| Status | Condition |
|---|---|
| 400 | image not valid base64, not JPEG/PNG, or decoded size > 10MB |
| 401 | missing/invalid JWT |
| 403 | role is not INVESTOR |
| 409 | latest attempt is already APPROVED |
| 422 | Pydantic validation failure (missing field) |
| 502 | GVerify unreachable / returned success=false envelope — attempt persisted as FAILED |

### `GET /gverify/kyc/status`

**Auth:** Bearer JWT — role: `INVESTOR`

Returns the caller's **latest** attempt.

**Response 200**
```json
{
  "verification_id": "uuid",
  "status": "REJECTED",
  "is_terminal": true,
  "is_approved": false,
  "rejection_reason": "Face match below threshold",
  "person_number": null,
  "full_name": null,
  "updated_at": "2026-07-13T00:00:00Z"
}
```

**Error:** 404 when the user has never attempted GVerify KYC.

### Upstream calls (GVerify API v2.5.1, for reference)

- `POST {base}/ekyc/api/base64/verify-ocrid` — body `{code, img_front, img_back}`;
  headers `x-api-key`, `os-type`, `Content-type: application/json`.
- `POST {base}/ekyc/api/base64/face-match` — body `{code, img1, img2}` where
  `img1` = portrait, `img2` = ID front.
- Both return the `{success, error{code,message}, data{...}}` envelope;
  `success=false` or HTTP ≠ 200 ⇒ provider error (our 502). GVerify error codes
  seen in the doc: `401` (bad APIKey), `ERROR_99` (unknown).

---

## 5. State Machine

Per-attempt; every attempt ends terminal within the request that created it.

```
PENDING ──[OCR + face match pass]──────────────► APPROVED
PENDING ──[OCR invalid / low confidence]───────► REJECTED
PENDING ──[face mismatch / below threshold]────► REJECTED
PENDING ──[GVerify HTTP error / success=false]─► FAILED
```

- No transitions out of APPROVED / REJECTED / FAILED — a retry is a **new row**.
- A user with a REJECTED or FAILED latest attempt may retry; a user whose latest
  attempt is APPROVED gets 409.

---

## 6. Business Rules

1. Only `INVESTOR` may call the KYC endpoints (mirrors Didit `/kyc/*`).
2. Each image must be valid base64, decode to JPEG or PNG (magic-byte check),
   and be ≤ 10MB decoded (GVerify's documented limit).
3. OCR passes iff: envelope `success=true`, AND `front_valid` and `back_valid`
   are truthy ("true"/"1"/"yes"/"valid", case-insensitive, or boolean true),
   AND `person_number` is non-empty, AND — where the confidence values parse as
   floats — `person_number_confidence` ≥ `GVERIFY_MIN_OCR_CONFIDENCE` and
   `full_name_confidence` ≥ `GVERIFY_MIN_OCR_CONFIDENCE`. Unparseable confidence
   values are ignored (the field set varies by card type).
4. Face match passes iff `is_matching` is true AND — when `match` parses as a
   float — `match` ≥ `GVERIFY_FACE_MATCH_THRESHOLD`.
5. Both provider payloads (`{data}`) are persisted verbatim (JSONB) on the
   attempt row for audit. The submitted images are retained in R2 under
   `verification/KYC/{verification_id}/` (bucket `R2_VERIFICATION_BUCKET`,
   falling back to `R2_BUCKET`) — v1.1 decision, reversing v1.0's
   no-retention stance. Retention is best-effort: a storage outage never
   blocks the verification (logged, provider payloads remain the primary
   audit record). Keys are deterministic from the attempt id — no DB column.
6. Every attempt writes an audit-log entry (entity `GVERIFY_KYC_VERIFICATION`,
   action `VERIFY`, actor = the user).
7. The face-match call is skipped when OCR already failed (fail fast, one less
   billable provider call).
8. Provider identifiers (`transaction_code`) are stored for reconciliation with
   GVerify's billing/console.

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| Image > 10MB / not JPEG-PNG / bad base64 | No row created, no provider call | 400 `{"detail": "..."}` |
| Latest attempt already APPROVED | No row created, no provider call | 409 |
| GVerify unreachable / timeout on either call | Attempt row saved as FAILED with reason | 502 |
| GVerify envelope `success=false` (e.g. ERROR_99) | Attempt row saved as FAILED, error code+message in reason | 502 |
| OCR says card invalid (`front_valid`/`back_valid` falsy) | Attempt REJECTED, reason recorded, face call skipped | 201 with `status: REJECTED` |
| OCR confidence below threshold | Attempt REJECTED, reason recorded, face call skipped | 201 with `status: REJECTED` |
| Face `is_matching=false` or score < threshold | Attempt REJECTED, OCR fields still persisted | 201 with `status: REJECTED` |
| SME/ADMIN calls the endpoint | — | 403 |
| `GET /status` with no attempts | — | 404 |

Note: a *rejection* is a successful API call (201) — the verification business
outcome is in the body. Only provider failures surface as 5xx.

---

## 8. Acceptance Criteria

- [ ] `test_kyc_verify_happy_path_approves` — valid images, OCR + face pass ⇒ 201 APPROVED, identity fields persisted
- [ ] `test_kyc_verify_rejects_invalid_id_card` — `front_valid` falsy ⇒ 201 REJECTED, face-match not called
- [ ] `test_kyc_verify_rejects_low_ocr_confidence` — confidence below threshold ⇒ 201 REJECTED
- [ ] `test_kyc_verify_rejects_face_mismatch` — `is_matching=false` ⇒ 201 REJECTED with reason
- [ ] `test_kyc_verify_rejects_low_face_score` — `match` below threshold ⇒ 201 REJECTED
- [ ] `test_kyc_verify_conflict_when_already_approved` — second call after APPROVED ⇒ 409, no new row
- [ ] `test_kyc_verify_allows_retry_after_rejection` — new attempt after REJECTED ⇒ 201, new row
- [ ] `test_kyc_verify_rejects_unauthorized_role` — SME ⇒ 403
- [ ] `test_kyc_verify_rejects_bad_image` — non-image bytes ⇒ 400, no provider call
- [ ] `test_kyc_verify_rejects_oversized_image` — > 10MB decoded ⇒ 400
- [ ] `test_kyc_verify_provider_error_returns_502_and_marks_failed` — client raises ⇒ 502, attempt FAILED
- [ ] `test_kyc_status_returns_latest_attempt` — returns newest row
- [ ] `test_kyc_status_not_found_when_never_attempted` — 404

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | Which provider wins long-term — does GVerify replace Didit for KYC, and does the cut-over rewire `/kyc/*` or keep `/gverify/kyc/*`? Needs an ADR. | Edward | — |
| 2 | Do we require a liveness step (passive liveness = 2 portraits) before APPROVED, or is OCR + face match enough for the sandbox? | Edward | — |
| 3 | Real `GVERIFY_BASE_URL` + credentials and sandbox access from Datatrust/PATK. | Phat | — |
| 4 | Should `person_number` be unique-per-approved-user (block one CCCD across accounts)? | Edward | — |
| 5 | KYB via `/ekyb/api/*` (business registration OCR + tax code verify) — separate spec. | Edward | — |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-13 | Phat | Initial draft |
| 1.1 | 2026-07-14 | Phat | Retain submitted images in R2 (`verification/KYC/<id>/`); surface biometric invalid_message verbatim; phone QR handoff endpoints |
