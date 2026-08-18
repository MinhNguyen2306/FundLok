# 3.5 What FundLok builds — and pays for

*[CONTENT — Edward. English draft for internal review; Vietnamese version to follow.]*

---

Everything on the FundLok side of this partnership is built, operated and paid for by FundLok. VPBank is asked to provide custody and settlement (specified in Section 3.3) and nothing else: no platform development, no integration development on FundLok's behalf, and no contribution to FundLok's build or running costs.

This section lists the components FundLok is responsible for, separated into **what already exists and is running today** and **what FundLok will build for this partnership**. The distinction matters because it shows how much of the platform is already operational: the parts of the system that carry the most correctness risk — the appraisal engine, the identity verification flow and the double-entry ledger — are built, tested and merged, not planned. What remains to be built is largely the connective work between FundLok's existing ledger and VPBank's custody account.

---

## 3.5.1 Already built and operating

| # | Component | What it does | Status |
|---|---|---|---|
| 1 | Platform API & investor / SME portal | Registration, authentication, role-based access control, user and enterprise profile management, administrative back office | In production. Token-based authentication with refresh and revocation, Argon2 password hashing, role-based authorisation across all endpoints |
| 2 | Identity verification — KYC and KYB | Investor identity verification, enterprise verification including business registration, licence code and legal-representative checks, document capture and face match, via an integrated third-party verification provider | In production. Largest single subsystem in the platform; written to its own specification |
| 3 | Credit appraisal & grading engine | Deterministic multi-factor scoring of each SME application producing a grade, a rate tier and pricing, with sector-level reference data, calibration parameters and a locked score run so terms cannot drift after approval | In production. Backed by a fixed golden-set test fixture and a sector reference table of 105 values |
| 4 | Double-entry ledger | Append-only record of every movement, balances computed by summation rather than stored, immutability enforced at the database layer as well as in application code, funds segregated per loan with cross-loan netting rejected by the code itself | In production. Corrections are made by posting a reversing entry; no record can be edited or deleted |
| 5 | Marketplace, order book & loan contracts | Publication of appraised opportunities, investor commitment capture, contract generation and loan lifecycle state management | In production |
| 6 | Document management | Secure document upload, storage and retrieval for verification and loan documentation, using pre-signed access to object storage | In production |
| 7 | Audit logging | Recorded trail of administrative and financial actions, retained for inspection | In production |
| 8 | Automated test suite & deployment pipeline | Regression tests run on every change, with automated build and deployment to managed cloud infrastructure and secrets held in a managed secret store | In production |

---

## 3.5.2 To be built for this partnership

Each component below is tied to the step of the end-to-end process (Section 3.1) that it serves, so the list can be checked against the process rather than taken on trust.

| # | Component | What it does | Serves step |
|---|---|---|---|
| 1 | Payment instruction engine with dual control | Composes and transmits payment instructions to VPBank, enforcing two-person authorisation so no single individual can cause a transfer, with an idempotency key on every instruction so a repeated instruction can never produce a second payment | 6, 8 |
| 2 | Escrow account provisioning & lifecycle | Requests the restricted escrow account for each loan, records the account against the loan, manages the permitted-destination list, and closes the account at loan closure — with an internal approval gate before an account goes live | 3, 9 |
| 3 | Bank settlement records & automated reconciliation | Links every ledger entry to the corresponding bank settlement, reconciles VPBank's statement against FundLok's ledger on a defined cycle, and raises any difference as an exception rather than adjusting the ledger to match | 5, 7, 9 |
| 4 | Collection matching | Matches each incoming receipt to the correct loan and day, reconciles it against the amount requested, and routes unattributable receipts to an exception queue instead of applying them on assumption | 7 |
| 5 | Distribution engine | Computes each investor's pro-rata entitlement, composes the corresponding batch of instructions, tracks each transfer individually, and leaves a failed amount in the escrow account for retry rather than redirecting it | 8 |
| 6 | Settlement account registration & verification | Registers each party's own bank account or licensed e-wallet, records the originating account that makes the closed loop enforceable, and confirms the account belongs to the verified party before it becomes a permitted destination | 2, 5, 8 |
| 7 | Operations & reconciliation dashboards | Gives FundLok's operations staff live visibility of escrow balances, instruction status, reconciliation state and open exceptions, so a break is visible on the day it occurs | All |
| 8 | Exposure & reporting module | Tracks each borrower's outstanding exposure across loans and produces the operational and portfolio reporting FundLok requires | 2, 9 |
| 9 | Data protection controls | Consent capture and withdrawal records, retention enforcement, and the access-control and logging evidence required under Section 4.4 | 1, 2 |
| 10 | T-VAN integration | Pulls each borrower's invoice-level sales data daily from a licensed T-VAN provider, which is the source of the revenue figure the daily repayment is calculated from | 7 |
| 11 | Daily revenue-share engine | Computes each borrower's amount due from the prior day's revenue, issues the payment request through the platform and its notification channel, and tracks the outstanding obligation against the gross principal | 7 |

FundLok's existing ledger is the foundation all eleven sit on. Components 1 to 5 are connective work between that ledger and VPBank's custody account; components 6 to 9 are FundLok-internal; components 10 and 11 implement the daily revenue-share mechanism specified in Section 1.4 and are the largest single addition to FundLok's build.

Components 10 and 11 deserve a note. The repayment mechanism is a **daily revenue share, not an instalment schedule** — the amount owed each day is derived from the borrower's actual prior-day sales rather than fixed at origination. That makes the T-VAN integration a dependency of the money flow itself rather than a reporting convenience: without it there is no figure to collect against. Neither component is started.

---

## 3.5.3 Cost

**FundLok bears the full cost of every component in both tables above** — build, testing, deployment, hosting, third-party verification fees, and ongoing operation and support. FundLok seeks no contribution, cost-sharing or development resource from VPBank for any of it.

VPBank's own build is specified separately in Sections 3.3 and 3.4, and VPBank prices that work itself. Effort estimates for the components above are in Section 3.6.

---

## 3.5.4 Basis of the statements in this section

Per the general rule that every figure carries a source: the counts and status descriptions in 3.5.1 are taken from a direct inspection of the FundLok source repository on 4 August 2026. The platform comprises 23 application modules and approximately 8,200 lines of application code, covered by 160 automated tests, with 14 database migrations applied. "In production" means merged to the main branch, covered by the automated test suite, and deployed through the automated pipeline — not prototyped.

---

## 3.5.5 Items to be confirmed

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 0 | Confirmation from Phat of the T-VAN integration's actual status. Nothing relating to it appears in the FundLok repository or on any branch as at 5 August 2026, so it is recorded above as not started | Determines whether component 10 is greenfield or partly complete, and its estimate in Section 3.6 | Edward, with Phat | 2026-08-12 |
| 1 | Whether the operations dashboards (component 7) are required for the pilot or can follow it | At pilot volume, exception handling could be run from existing administrative screens, which would remove one component from the pilot scope | Edward | 2026-08-07 |
| 2 | Whether exposure and reporting (component 8) is in pilot scope or deferred | Depends on the reporting VPBank expects to receive during the pilot | Edward, with VPBank | Pending VPBank confirmation |
| 3 | Hosting region for personal data, and the position on in-country processing | Stated in Section 4.4; affects the infrastructure line of this section. Current deployment is in a regional cloud location outside Vietnam, so an in-country commitment is a migration rather than a description of today | Edward | 2026-08-07 |

---

*Dependencies: none. Consistent with Section 3.1 (process), Section 3.3 and 3.4 (VPBank's build), Section 3.6 (effort) and Section 4.4 (data protection).*
