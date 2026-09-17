# Spec: KYC Document Approval Endpoint

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/lending/` |
| **Version** | 1.0 |
| **Date** | 2026-09-17 |
| **Related ADR** | — |
| **Depends on** | — |

---

## 1. Context & Goal

HANDOFF-03 GAP-1 / Issue 12: `project_has_verified_kyc()` (`app/lending/kyc.py`)
gates `POST /market/listings`, but nothing anywhere in the app ever sets
`Document.status = "APPROVED"` -- verified by grepping the whole `app/`
tree. No listing can go live through any real code path; the only way to
reach that state before this spec was `conftest.py`'s `approve_kyc_documents`
test fixture, which writes the ORM row directly because there was no
service to call.

**Goal:** one admin-only endpoint that approves a `Document`, with actor,
timestamp and rationale captured in the audit log, so the KYC gate is
reachable from outside the test suite.

---

## 2. Out of Scope

- Document upload / creation (`app/uploads/`, Phat's UI-integrated module) --
  this spec only approves an existing `Document` row.
- Rejection, re-submission, or any other status transition besides
  `PENDING -> APPROVED`.
- A "list documents pending review" endpoint -- not required by GAP-1's
  acceptance criterion and not built here.
- KYB/business verification flows (`app/verification/`, `app/gverify/`) --
  those are a separate identity-verification pipeline with their own
  session/webhook state, not the generic `Document` entity this endpoint
  approves.

---

## 3. Data Model

No new tables, no migration. Uses the existing `documents` table
(`app/lending/models.py::Document`) and `audit_logs`
(`app/lending/models.py::AuditLog`) as-is: `status` and `verified_at` are
already columns on `Document`; actor/timestamp/rationale are captured via
`append_audit` (`app/utils/audit.py`), not new columns.

---

## 4. API Contract

### `POST /lending/documents/{document_id}/approve`

**Auth:** Bearer JWT — role: `ADMIN`

**Request**
```json
{
  "rationale": "string"   // required, min length 1 -- goes into the audit log
}
```

**Response 200**
```json
{
  "id": "uuid",
  "entity_type": "PROJECT",
  "entity_id": "uuid",
  "purpose": "KYC_ID",
  "filename": "string",
  "status": "APPROVED",
  "verified_at": "2026-09-17T00:00:00Z",
  "created_at": "2026-09-17T00:00:00Z"
}
```

**Error Responses**

| Status | Condition |
|---|---|
| 400 | Document is already `APPROVED` |
| 403 | Caller is not `ADMIN` |
| 404 | Document does not exist |
| 422 | `rationale` missing or empty |

---

## 5. State Machine

```
PENDING  ──[trigger: POST .../approve, by ADMIN]──►  APPROVED
```

`APPROVED -> APPROVED` (re-approval) is rejected with 400 rather than
silently succeeding a second time -- approval is a one-way, audited event,
not an idempotent status set.

---

## 6. Business Rules

1. Only `ADMIN` may approve a document (RBAC `require_roles(Role.ADMIN)`).
2. Approving sets `status = "APPROVED"` and `verified_at = now()` (UTC)
   in the same write.
3. Every approval writes one `AuditLog` row: `entity_type="DOCUMENT"`,
   `entity_id=<document id>`, `action="APPROVE"`, `actor_id=<caller>`,
   `before_state={"status": <previous status>}`,
   `after_state={"status": "APPROVED", "verified_at": ..., "rationale": ...}`.
4. `project_has_verified_kyc()` requires all of `KYC_PURPOSES` (`KYC_ID`,
   `KYC_ADDRESS`, `KYC_BUSINESS_REG`) to be `APPROVED` for the same
   `entity_id` — this endpoint approves one document at a time; the caller
   (ops) is responsible for approving all three before a project can list.

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| Document does not exist | No row found | 404 |
| Document already `APPROVED` | Rejected before any write | 400 |
| Caller is SME/INVESTOR | RBAC dependency raises before the handler runs | 403 |
| `rationale` empty or missing | Pydantic validation failure | 422 |

---

## 8. Acceptance Criteria

- [x] `test_approve_document_sets_status_and_verified_at`
- [x] `test_approve_document_writes_audit_log_with_actor_and_rationale`
- [x] `test_approve_document_requires_admin_role`
- [x] `test_approve_document_not_found_returns_404`
- [x] `test_approve_document_already_approved_rejected`
- [x] `test_project_passes_kyc_check_and_can_be_listed_after_real_approval` — the GAP-1 criterion verbatim, end to end through the real endpoint (not the `conftest.py` ORM shortcut)

---

## 9. Open Questions

None.

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-17 | Edward | Initial approval endpoint (T15, HANDOFF-03 GAP-1). |
