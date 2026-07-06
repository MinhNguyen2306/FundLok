# ADR-004: Vietnam Regulatory Compliance (Decree 94 + Circular 64)

| Field | Value |
|---|---|
| **Status** | Draft |
| **Date** | July 2026 |
| **Deciders** | Edward Wong (CTO) |
| **Related** | ADR-002 (omnibus/custodial), ADR-003 (omnibus-first, escrow seam) |

> **Not legal advice.** This ADR records engineering's working reading of the regulations so the codebase can be built to meet them. Every requirement below must be validated with qualified Vietnamese legal counsel before launch, and the sandbox application itself is a legal process, not an engineering one. Where this ADR and counsel disagree, counsel wins and this ADR is updated.

## Context

FundLok is a Vietnam-registered P2P lending marketplace. Two distinct Vietnamese instruments govern the platform, and they are frequently conflated — they are not the same regime:

1. **Decree 94/2025/ND-CP** — the fintech **regulatory sandbox** (effective 1 July 2025). It is *who may operate and under what conditions*: it defines the controlled-testing licence for P2P lending, Open API, and credit scoring.
2. **Circular 64/2024/TT-NHNN** — the banking **Open API technical standard** (effective 1 March 2025; full compliance by 1 March 2027). It is *how systems must talk to banks*.

FundLok must satisfy both: Decree 94 as the operating licence and conduct regime, Circular 64 as the technical bar for the custodial-bank/aggregator integration.

## Decision

Adopt both instruments as binding design constraints. Enforcement is distributed across modules per the mapping below; this ADR is the single reference that ties each requirement to where it lives.

### Decree 94/2025/ND-CP — P2P sandbox regime

| # | Requirement (as understood) | Where enforced |
|---|---|---|
| D1 | **Maximum loan exposure per borrower** must be managed and capped | `app/compliance/` (exposure-cap check at loan approval / listing; reads ledger balances) |
| D2 | Use **CIC** (National Credit Information Centre) data | `app/underwriting/` + `app/compliance/` (CIC integration feeds the grading engine) |
| D3 | Funds settle **only through bank accounts or licensed e-wallets** — FL never holds funds directly | ADR-002/003 custodial model; `app/banking/` + `app/ledger/` |
| D4 | **Loan term ≤ 2 years** | `app/loans/` validation + `app/compliance/` |
| D5 | **No loan guarantees**; no unrelated services (FL is a pure marketplace, takes no position) | Product/architecture invariant — already core to FL; no netting/position-taking in `app/ledger/` (ADR-003) |
| D6 | **Wholly Vietnamese-owned**; legal rep / CEO background checks | Corporate/legal — not an engineering control |
| D7 | **IT systems Vietnam-based**; security, privacy, continuity, pre-op testing | `app/core` config + deployment (Cloud Run region = Vietnam-eligible); infra/ops |
| D8 | **All testing within Vietnam** — no cross-border processing | Deployment/data-residency; no offshore data processing of sandbox activity |
| D9 | Activities limited to the **Certificate of Participation** scope; licence up to 2 yrs (+2×1-yr extensions) | Legal/operational; product scope discipline |
| D10 | **Full auditability** of platform activity | Immutable ledger + `audit_logs` (`app/ledger/`, ADR-003); append-only at DB layer |

### Circular 64/2024/TT-NHNN — Open API technical standard

| # | Requirement | Where enforced |
|---|---|---|
| C1 | **OAuth 2.0 (RFC 6749)** with API tokens and refresh flows | `app/banking/` client auth; consistent with existing JWT access+refresh + revocation (HANDOFF-02 Fix B) |
| C2 | **TLS 1.2+** for data in transit | Deployment/ingress config; outbound bank calls |
| C3 | **JSON over RESTful HTTP**, **ISO 20022 / ISO 8583** compatible payloads | `app/banking/` payload mapping to the custodial partner |
| C4 | **Consent management** — user-controlled, revocable, time-bound, fully auditable | `app/banking/` consent records + `audit_logs`; ties to ledger auditability (D10) |
| C5 | Phased Open API scope: info query → consent access → payment initiation | Sequencing of the `app/banking/` build (payment initiation is the phase FL needs) |

## Consequences

- A dedicated **compliance spec** (`docs/specs/compliance/`) will detail D1–D2 and D4 enforcement (exposure-cap algorithm, CIC integration contract, term validation) with testable acceptance criteria. This ADR is the constraint source it draws from.
- The **banking spec** must state Circular 64 conformance (C1–C5) as explicit acceptance criteria — OAuth2, TLS, ISO-format payloads, consent auditability — not as afterthoughts.
- The **ledger foundation** (ADR-003, spec in REVIEW) already advances D3, D5, and D10 (append-only immutable ledger, no cross-contract netting, balance primitives for exposure caps). It does not *enforce* the caps or reporting — that is the compliance module's job.
- **Data residency (D7/D8)** is a deployment decision: the Cloud Run region and any managed Postgres/R2 configuration must keep sandbox data processing inside Vietnam. Flag for the infra/ops review before launch.
- The exposure-cap check (D1) depends on the ledger's `get_account_balance` / per-borrower aggregation — a concrete dependency of the compliance module on the ledger foundation.

## Open Questions

| # | Question | Owner |
|---|---|---|
| 1 | Exact per-borrower exposure cap figure/formula under the current Certificate of Participation | Edward + counsel |
| 2 | CIC integration: direct membership vs. via the custodial bank vs. a third party | Edward + counsel |
| 3 | Cloud Run region / data-residency plan that satisfies D7/D8 (in-Vietnam processing) | Edward + infra |
| 4 | Does the chosen custodial partner already meet Circular 64, or does FL carry mapping burden (ISO 20022)? | Edward + partner |
