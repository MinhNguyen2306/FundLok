# Known Gaps & Backlog

Gaps surfaced by the **HANDOFF-01** behavioral (characterization) test suite. The tests
document *current* behavior on `main`; the items below are recorded, not yet fixed. Each
feeds into planned V2 work. Source: the HANDOFF-01 PR write-up.

## GAP-1 — No endpoint approves KYC documents → no listing can go live
- **What:** nothing in `app/` ever sets `Document.status = "APPROVED"`. `project_has_verified_kyc()`
  (`app/lending/kyc.py`) gates `POST /market/listings`, so with no approval path in the real API,
  **no listing can legally go live.**
- **Impact:** blocks the borrower journey end-to-end in production. **High priority.**
- **Feeds into:** compliance/KYC flow; must be resolved before go-live.

## GAP-2 — Orders auto-fill; no PENDING_PAYMENT / payment-confirmation step
- **What:** `app/market/service.py::place_order` writes `status="FILLED"` immediately on placement.
  `PENDING_PAYMENT` is never used, and there is no cancel/expire path (`CANCELLED`/`EXPIRED`
  unreachable). The documented Order state machine is currently aspirational.
- **Impact:** a funding order fills with no real payment step. The banking funding flow must
  introduce the real gap: order stays `PENDING_PAYMENT` until the lender's inbound payment
  confirms via bank webhook, then → `FILLED`.
- **Feeds into:** banking Open API integration (ADR-002/ADR-003) + the funding-flow spec.

## Deferred (by design — not bugs)
- No admin-provisioning endpoint — ADMIN is provisioned out-of-band (per CLAUDE.md).
- ARQ worker scaffold — deferred (Phase 0).
