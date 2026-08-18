> ## ⚠ INTERNAL ENGINEERING SPEC — DO NOT SEND TO VPBANK
>
> This document predates the VPBank proposal template and its universal rules, and it
> **conflicts with them** in ways that are not cosmetic:
>
> - It references Decree 94/2025 throughout. Rule 4 of the proposal forbids any mention of it.
> - It proposes that VPBank rely on FundLok's KYC/KYB with audit rights. Rule 5 forbids implying
>   any reliance on FundLok's AML process.
> - It frames FundLok as "account holder of record" holding the account FBO the parties. Section 1.3
>   of the proposal instead makes the **investor** the lender of record and FundLok a non-owner
>   arranger/servicer with no withdrawal right.
> - It posts FundLok's fee out of the escrow account. The permitted-destination rule in Section 1.7
>   allows funds to leave escrow **only** to a verified borrower account or the originating investor
>   account — never to a FundLok account.
>
> The VPBank-facing content lives in the proposal sections instead (3.1 is in this directory as
> `section-3.1-end-to-end-process.md`). Retained here because its internal engineering findings are
> still valid and useful: the ledger conventions, the `resolve_custodial_account()` strict-mode
> hazard, the pass-through netting constraint, and the `OMNIBUS_CASH` naming issue.

# Spec: VPBank Escrow Model — Nine-Step Lifecycle & Integration Points

| Field | Value |
|---|---|
| **Status** | DRAFT |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/banking/`, `app/ledger/` |
| **Version** | 0.1 |
| **Date** | 2026-08-04 |
| **Related ADR** | ADR-002 (omnibus/custodial), ADR-003 (omnibus-first, escrow seam), ADR-004 (Decree 94 + Circular 64) |
| **Depends on** | `docs/specs/ledger/ledger-foundation.md` (ACCEPTED, implemented) |
| **Partner** | VPBank — Vietnam Prosperity Joint Stock Commercial Bank (Ngân hàng TMCP Việt Nam Thịnh Vượng) |

> **Placeholders.** `[FL_LEGAL_ENTITY]` is FundLok's registered legal name as it will appear in the account title, and `[PROJECT_CODE]` is FundLok's per-project reference format. Both must be fixed before this document is sent externally.
>
> **Not legal advice.** Regulatory readings below are engineering's working interpretation, carried forward from ADR-004. They must be confirmed with Vietnamese counsel and with VPBank's own compliance team.

---

## 1. Context & Goal

FundLok (FL) is a Vietnam-registered peer-to-peer lending marketplace. FL matches SMB borrowers with retail and institutional lenders and **takes no position** in any loan — it is a marketplace, not a lender and not a counterparty to the credit. FL is not a licensed bank and, under Decree 94/2025/ND-CP, cannot hold customer funds directly. Every movement of money must therefore land in an account at a licensed institution.

This document specifies the **escrow model** for that account structure with VPBank as the escrow bank: one escrow account per loan project, held by FL **for the benefit of** the SME borrower and that project's lenders. It walks the full lifecycle in nine steps, from party onboarding to loan closure and escrow account closure, and marks every point where FL's systems must talk to VPBank's.

It has two audiences and two purposes:

1. **VPBank's partnership and compliance teams** — to establish what the account structure is, who the beneficiaries are, who performs due diligence on whom, and what regulatory obligations sit on each side. This is the material that supports signing.
2. **VPBank's Open API / IT team** — Section 4 is a prioritised list of the nine capabilities FL needs. Read as a build backlog, it is the integration surface that has to exist for the flow to run, with a manual operational fallback defined for each so that FL can go live before the full API is delivered.

**Goal:** a single reference that both organisations can implement against without further verbal context, and that resolves ADR-002's open question on the custodial partner.

---

## 2. Out of Scope

- **Commercial terms** — fee levels, revenue share, minimum balances, transaction pricing, exclusivity, SLA penalties. Referenced where they create a technical dependency; negotiated separately.
- **The Decree 94 sandbox application itself.** That is a legal process between FL and the State Bank of Vietnam (SBV). This document only describes the controls FL builds to satisfy it.
- **Credit decisioning.** FL's grading engine (`app/underwriting/`) sets the interest rate tier. VPBank has no input into, and no liability for, credit outcomes.
- **FL's internal UI.** Frontend flows are Phat's ownership per `CLAUDE.md`.
- **The share conversion instrument itself** — its legal form and registration. Step 9 records where it happens in the lifecycle only.
- **Migration of existing data.** FL has no live ledger rows; the escrow model is being provisioned from zero.

---

## 3. Account Structure: The FBO Escrow Model

### 3.1 One account per project

Each funded loan project gets **its own escrow account at VPBank**. There is no pooling across projects.

```
VPBank escrow account:  "[FL_LEGAL_ENTITY] FBO [PROJECT_CODE]"
                         └─ account holder of record:  FundLok
                         └─ beneficiaries:             1 SME borrower  +  N lenders
```

**FBO** means *for the benefit of*. FL is the **account holder of record**: FL opens the account, is named on it, operates it, and instructs payments out of it. FL does not own the money in it. The beneficial interest belongs to the SME borrower and that project's lenders, in proportions that FL's ledger records at all times.

### 3.2 Terminology, stated precisely

These terms are frequently conflated and they drive who VPBank must perform due diligence on. Using them loosely in a bank conversation causes real confusion, so this document fixes them:

| Term | Meaning here |
|---|---|
| **Account holder of record** | FundLok. The legal operator of the escrow account, and the entity VPBank contracts with and performs customer due diligence (CDD) on. |
| **Beneficiary / beneficial owner** | The SME borrower and each lender on that project. They hold the economic interest in the escrow balance. They are *not* VPBank account holders by virtue of the escrow account. |
| **Counterparty** | Describes the SME and the lenders **to each other**, under the loan contract. It is a credit-relationship term, not a banking-relationship term. |
| **Settlement account** | A beneficiary's own external bank account or licensed e-wallet, at VPBank or elsewhere, that money is received from and paid out to. |

So: the SME and the lenders are **counterparties to each other on the loan**, and **beneficiaries of the escrow account**. FL is the account holder. This distinction determines the scope of VPBank's CDD obligation (Section 8.1) and it is the single most important thing for both compliance teams to agree on early.

### 3.3 One-to-many, and why it is the natural fit

The relationship is **one SME to many lenders** on every project. A project has exactly one borrower and one-to-N lenders, each with a distinct pro-rata share.

This maps directly onto structure FL already has in production. The ledger foundation (`docs/specs/ledger/ledger-foundation.md`, ACCEPTED and merged) models a `custodial_account` that represents one physical bank account, with a `scope`:

- `PLATFORM` — a single pooled account (the omnibus model)
- `CONTRACT` — one account per loan contract, carrying `contract_id` (**the escrow model**)

ADR-003 anticipated exactly this outcome: FL built the ledger omnibus-first but escrow-compatible, on the expectation that a conservative Vietnamese institution might only offer per-project escrow. The escrow model is therefore **not an architecture change for FL.** `resolve_custodial_account()` already returns a contract's own `CONTRACT`-scoped account when one exists. What is missing is (a) provisioning real accounts against real VPBank account numbers, and (b) the VPBank integration surface in Section 4.

The invariant that makes this work, and that FL enforces in code today, is **no cross-contract netting**: a single ledger transaction may never move value between two projects' accounts, and FL never treats the total across projects as a spendable pool. `post_transaction()` raises `CrossContractTransactionError` if legs span two contracts. Under escrow this stops being merely good hygiene and becomes a structural requirement — each escrow account is legally ring-fenced, and one project's funds can never settle another project's obligation.

### 3.4 FL's internal chart of accounts, per escrow account

For each project escrow account, FL maintains internal ledger accounts. These are FL's books, not VPBank accounts; VPBank sees one account with one balance.

| FL ledger account | Represents |
|---|---|
| `OMNIBUS_CASH` | Cash actually sitting in the VPBank escrow account. Reconciled daily against VPBank's balance and statement. |
| `BORROWER` | The SME's position on this contract. |
| `LENDER` (one per lender) | Each lender's contributed capital and entitlement. Created on that lender's first funding. |
| `FL_REVENUE` | FL's fee income, posted as an explicit `FEE` leg — never a silent deduction. |
| `SUSPENSE` | Confirmed inbound funds that cannot yet be attributed to a lender or an instalment. Structural home for unmatched credits (Step 5). |

> **Naming note for FL, internal.** The `OMNIBUS_CASH` account type is a misnomer under escrow — it is the *escrow* cash account. The identifier is fixed by a `CHECK` constraint in migration `862160bce972`, so renaming it is a migration, not a rename. Recommend deferring until the compliance module lands and batching it with other enum work, but recording it here so the mismatch is documented rather than confusing.

Every balance is computed as `SUM(credits) − SUM(debits)` at read time. No balance is ever stored in a mutable column, and both ledger tables are append-only at the application layer *and* enforced by a PostgreSQL trigger. Corrections are made by posting a reversing transaction, never by editing a row. This is what gives FL — and VPBank, and the SBV — a tamper-evident audit trail (Decree 94, full auditability).

### 3.5 Control and authority matrix

| Action | FL | VPBank | Beneficiaries |
|---|---|---|---|
| Open / close escrow account | Requests | Executes, owns KYC on FL | — |
| Instruct payment out of escrow | Sole authority (ADMIN role, dual control) | Executes on valid instruction | Cannot instruct |
| Receive funds into escrow | Attributes in ledger | Credits account, notifies FL | Push funds in |
| See escrow balance | Yes, via API + own ledger | Yes, authoritative | Own share, via FL's UI |
| Withdraw funds directly | No — only per contract terms | No | No |
| Amend a ledger record | Impossible by design (append-only) | N/A | No |

FL's authority to instruct payments is **bounded by the loan contract**: disbursement only to the SME's verified settlement account after the funding target is met, and distribution only pro-rata to that project's lenders. FL cannot direct escrow funds to itself beyond the contractually agreed fee, and every fee movement is an explicit, auditable ledger posting.

---

## 4. Integration Surface: What FL Needs From VPBank

Nine capabilities. FL's understanding is that VPBank's Open API programme (built on WSO2 API management) today covers payments, wallet linking, balance sharing and payment authorisation, but does not include an escrow or custodial product, and there is no public developer portal or sandbox. This section is therefore written as a **build backlog**, with a manual operational fallback for each capability so the flow can run from day one while the API is delivered incrementally.

| ID | Capability | Priority | Manual fallback for day one | Circular 64 |
|---|---|---|---|---|
| **B1** | **Escrow account opening** — create an FBO escrow account for a project; return account number and status. | Should have | Ops opens accounts in batch with the relationship manager; account numbers keyed into FL's admin portal. Viable at low volume; becomes the binding constraint on growth. | C5 phase 1 |
| **B2** | **Account name verification** — confirm a given account number belongs to a given legal name (NAPAS name inquiry). | **Must have** | Manual name check against KYC records at first payout. Slow and error-prone; this is an AML control, not a convenience. | C1, C5 phase 1 |
| **B3** | **Inbound credit notification** — webhook on funds landing in an escrow account, carrying amount, value date, remitter, and the payment reference. | **Must have** | Poll B6 statements every 5–15 minutes. Adds latency to lender order confirmation and borrower repayment recognition. | C5 phase 2 |
| **B4** | **Payment initiation, single and batch** — credit transfer out of a named escrow account to a beneficiary account, with an FL-supplied idempotency key; per-leg status on batches. | **Must have** | Ops uploads a payment file / instructs by secure channel. Every distribution to N lenders becomes a manual batch. Not sustainable past pilot. | C1, C3, C5 phase 3 |
| **B5** | **Balance inquiry** — real-time balance per escrow account. | **Must have** | Read from B6 statement. Acceptable if statements are intraday. | C5 phase 1 |
| **B6** | **Statement retrieval** — transaction history per escrow account for a date range, paginated, with stable transaction identifiers. | **Must have** | Daily statement file by secure transfer. Workable, but T+1 reconciliation only. | C5 phase 1 |
| **B7** | **Payment status query** — status of a previously initiated payment by FL's reference. | Should have | Ops enquiry. Needed to resolve timeouts without double-paying; without it, FL must treat every timeout as manual investigation. | C5 phase 3 |
| **B8** | **Escrow account closure** — close a zero-balance escrow account and issue a final statement. | Nice to have | Ops request. Volume is low and closure is never time-critical. | C5 phase 1 |
| **B9** | **Consent and authorisation** — OAuth 2.0 client credentials for FL as account holder; consent records for beneficiaries linking their own settlement accounts, revocable and time-bound. | **Must have** for B2 | Signed mandate on paper, recorded in FL's audit log. | C1, C4 |

**Virtual accounts — the single highest-leverage ask.** If VPBank can issue **per-lender virtual account numbers underneath a project escrow account**, attribution of inbound funds becomes deterministic: each lender is given a unique account number to pay into, and no reference-string matching is needed. This removes the largest operational risk in the whole flow (Step 5, unattributable credits) and materially reduces suspense-account handling on both sides. FL's `custodial_account` model absorbs this without change. **FL would prioritise this above B1 automation.**

**Cross-cutting technical requirements**, per Circular 64/2024/TT-NHNN, which VPBank is itself subject to (effective 1 March 2025, full compliance by 1 March 2027):

- **C1** OAuth 2.0 (RFC 6749) with access and refresh tokens.
- **C2** TLS 1.2 or above for all data in transit.
- **C3** JSON over REST; payloads compatible with ISO 20022 / ISO 8583. **Open question for VPBank: does VPBank map to ISO 20022 on its side, or does FL carry the mapping burden?**
- **C4** Consent management — user-controlled, revocable, time-bound, fully auditable.
- **C5** Phased scope: information query → consent-based access → payment initiation. FL needs to reach phase 3.
- **Idempotency.** Every FL-initiated payment carries an FL-generated idempotency key. Replaying it must return the original result and must never create a second payment. FL's ledger is already built on this pattern end to end.
- **Currency.** VND only. Decree 94 requires sandbox transactions in Vietnamese Dong.
- **Data residency.** Decree 94 requires IT systems and all testing to be Vietnam-based, with no cross-border processing of sandbox activity. This constrains FL's deployment region and any VPBank-side processing of FL data.

---

## 5. The Nine Steps

> **The swimlane diagram on the final page** shows all nine steps against all five lanes at a glance, with every integration point and the direction of money movement. Read it alongside this section.

Each step below gives the actors, what happens, the FL↔VPBank integration point, the resulting FL ledger postings, and the state transitions. Ledger postings are written in the convention FL's ledger uses: `debit → credit`, where an amount moves *from* the debit account *to* the credit account, and an account's balance rises when credited.

---

### Step 1 — Party onboarding and identity verification

**Actors:** SME borrower, lender, FL, third-party verification provider (Didit), VPBank compliance.

The SME registers on FL and completes **KYB** (know your business) — legal entity verification, business registration, licence code, and legal representative identity. The lender registers and completes **KYC**. Both run through FL's existing `app/verification/` and `app/gverify/` modules against Didit, and neither party can transact until verified.

**Integration point.** No per-transaction API call. What *is* required at this step is a compliance agreement between FL and VPBank on two things: VPBank performs CDD on **FundLok** as the account holder of record, and FL supplies a **beneficiary register** for each escrow account — the verified identity of the SME and of each lender, in an agreed format and refresh cadence. Whether VPBank additionally requires its own CDD on each beneficiary, or is willing to rely on FL's verification with audit rights, is the **first question to settle**, because it determines whether onboarding a lender takes minutes or days, and therefore whether the marketplace works at all. FL's position is that FL performs KYC/KYB to VPBank's documented standard, VPBank retains audit and inspection rights over those records, and no separate VPBank onboarding is imposed on beneficiaries.

**Ledger:** none. **States:** `User.kyc_status → VERIFIED`; SME entity verified.

---

### Step 2 — Settlement account linking and name verification

**Actors:** SME, lender, FL, VPBank.

Each party links the external bank account or licensed e-wallet they will send money from and receive money to. FL stores only a masked reference — the raw account number is never persisted (`linked_accounts`, per `docs/specs/banking/account-linking-mock.md`, which is currently a mock standing in for exactly this integration).

**Integration point — B2, B9.** FL calls account name verification to confirm the account number belongs to the legal name FL verified in Step 1. A mismatch blocks the link. This is the control that stops FL disbursing to, or distributing to, a third party — the principal AML risk in the flow, and the reason B2 is a must-have rather than a nicety. A consent record is captured at the same time, revocable by the user.

Decree 94 requires that disbursement and repayment occur **only via bank accounts or licensed e-wallets**. This step is where FL enforces that: no party can transact without a verified settlement instrument of an accepted type.

**Ledger:** none. **States:** `linked_accounts.status → ACTIVE`.

---

### Step 3 — Project listing, loan application, grading and contract

**Actors:** SME, FL, FL ADMIN.

The SME describes its enterprise and project and applies for a loan. FL's ML grading engine scores the application across its factor set and assigns an interest rate tier; the score run is locked so that terms cannot drift after approval. An FL ADMIN reviews and approves, and a loan contract is generated with final terms and a funding target, then signed.

**Integration point.** None required — this is internal to FL, and VPBank has no role in and no liability for credit decisioning. One **open question** touches VPBank: Decree 94 requires P2P operators to manage each borrower's maximum debt balance, and CIC (National Credit Information Centre) data feeds that. FL must decide whether it accesses CIC through direct membership, through a third party, or **through VPBank as a member institution**. If VPBank can offer CIC lookup as part of the partnership, that resolves an open item in ADR-004 and adds real value to the credit process.

Note also that Decree 94 caps lending contract terms at **two years**, which bounds the maximum life of any escrow account VPBank opens.

**Ledger:** none. **States:** `LoanApplication: DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED`; `ScoreRun: RUNNING → READY → LOCKED`; `Contract: DRAFT → SIGNED`.

---

### Step 4 — Escrow account provisioning

**Actors:** FL, FL ADMIN, VPBank.

Once the contract is signed, the project's escrow account is opened at VPBank, titled `[FL_LEGAL_ENTITY] FBO [PROJECT_CODE]`. VPBank returns the account number and status; FL records it as a `custodial_accounts` row with `scope='CONTRACT'`, the `contract_id`, and the VPBank account number in `bank_account_ref`. FL then creates the internal chart of accounts from Section 3.4 for this contract. Provisioning is automated up to an **ADMIN approval gate** before the account goes live, which can be short-circuited later once the process is trusted.

**Integration point — B1.** Account opening, returning account number and status. If per-lender **virtual accounts** are available, they are allocated here too, or on demand at Step 5.

*Fallback:* ops opens accounts in batch with the relationship manager and keys the numbers into FL's admin portal. This works at pilot volume and is the honest constraint on scaling — every new project needs an account.

**Titling and structure to confirm with VPBank:** the exact permitted account title format for an FBO arrangement; whether the account is a current account with escrow terms in a tripartite or bipartite agreement, or a distinct escrow product; whether interest accrues on escrow balances and, if so, whose it is (FL's position: it belongs to the beneficiaries, and FL will need a documented allocation rule); and whether any minimum balance or dormancy rule applies to short-lived accounts.

> **Internal note for FL, not for VPBank.** `resolve_custodial_account()` currently falls back to the single `PLATFORM` account when a contract has no `CONTRACT`-scoped account. Under omnibus that fallback is correct. Under escrow it is a **latent hazard**: if provisioning silently failed, postings would land against the platform account instead of raising, co-mingling a project's funds in FL's books. Before escrow go-live this needs a strict mode that raises `CustodialAccountNotProvisioned` rather than falling back. Tracking as a follow-up.

**Ledger:** accounts created; no postings, zero balance. **States:** `Contract: SIGNED → ACTIVE_PENDING_FUNDING`; `Listing: DRAFT → OPEN`; `custodial_accounts.status = ACTIVE`.

---

### Step 5 — Lender funding into escrow (inbound, one-to-many)

**Actors:** lenders (N of them), FL, VPBank.

The listing is open on the marketplace. A lender chooses an amount and places an order, which FL creates in `PENDING_PAYMENT` with a unique payment reference. The lender pushes funds from their linked settlement account into the project escrow account, quoting that reference — or, with virtual accounts, simply pays their own dedicated account number. When VPBank confirms the credit, FL attributes it to the order, posts the funding to the ledger, and moves the order to `FILLED`. This repeats until the funding target is met.

**Integration point — B3, and B6 as fallback.** Inbound credit notification carrying amount, value date, remitter details and the payment reference. FL matches on reference; on success it posts `FUNDING` and fills the order. **Unmatched or ambiguous credits post to `SUSPENSE`** and raise an ops exception rather than being guessed at — that is exactly what the suspense account exists for. Handling is idempotent: the same credit notification delivered twice must produce one ledger transaction, which FL's event-level idempotency key guarantees.

*Fallback:* poll statements every 5–15 minutes. The cost is latency between a lender paying and seeing their order confirmed.

> **This step closes a known gap.** FL's current marketplace code fills orders immediately on placement, with no payment step — `PENDING_PAYMENT` is unreachable and there is no cancel or expire path (GAP-2 in `docs/backlog/known-gaps.md`). The escrow integration introduces the real gap between placing an order and money arriving. Orders will need an expiry, and `app/market/` is **Phat-owned**, so this requires joint agreement before either side edits it.

**Ledger:** per lender, `FUNDING`: debit that lender's `LENDER` account → credit `OMNIBUS_CASH`. **States:** `Order: PENDING_PAYMENT → FILLED` (or `EXPIRED`); and when the target is reached, `Listing: OPEN → FUNDED` and `Contract: ACTIVE_PENDING_FUNDING → ACTIVE_FUNDED`.

---

### Step 6 — Disbursement to the SME (outbound, net of fee)

**Actors:** FL ADMIN, VPBank, SME.

**Preconditions:** `Contract.status == ACTIVE_FUNDED` and `Listing.status == FUNDED` with `funded_amount >= target_amount`. An FL ADMIN triggers disbursement. FL verifies the escrow balance, then instructs VPBank to pay the SME's verified settlement account, and separately to move FL's fee to FL's own operating account. The disbursement amount is the funded amount **less FL's fee**, and the fee is posted as an explicit `FEE` leg in the same atomic ledger transaction — never a silent deduction.

**Integration point — B5, then B4, confirmed via B3 or B7.** Balance check, then payment initiation with FL's idempotency key. On a non-2xx from VPBank, FL writes **no** ledger entry and the ADMIN may retry with the same key. Settlement is asynchronous: FL's API returns `202 Accepted`, and the bank transaction record moves `PENDING → SETTLED` on confirmation. Contract row locking (`SELECT FOR UPDATE`) prevents concurrent disbursement of the same contract.

Because there is no cross-contract netting, the disbursement can only draw on **this project's** escrow balance. There is no platform pool to borrow against — a structural guarantee, not a policy.

**Ledger:** one transaction, two legs — `DISBURSEMENT`: debit `OMNIBUS_CASH` → credit `BORROWER`; `FEE`: debit `OMNIBUS_CASH` → credit `FL_REVENUE`. **States:** `Listing: FUNDED → CLOSED`; `bank_transaction: PENDING → SETTLED`. The contract stays `ACTIVE_FUNDED` — it reached that state when funding completed in Step 5, and only moves to `CLOSED` at Step 9.

---

### Step 7 — Repayment collection from the SME (inbound, scheduled)

**Actors:** SME, FL, VPBank.

FL's amortisation engine produces the repayment schedule at disbursement. On each due date the SME repays principal and interest into the **project escrow account**. FL recognises the repayment when VPBank confirms the credit. **Early repayment is encouraged as a platform value** — FL recalculates the remaining schedule and the outstanding balance rather than penalising it.

**Integration point — B3, reconciled via B6.** Same inbound notification path as Step 5, matched to the instalment. If the SME banks with VPBank, a **standing instruction or direct debit mandate** would materially improve collection rates and reduce missed instalments — an ask worth raising, and a reason for FL to encourage borrowers to hold VPBank accounts.

Underpayments, overpayments and off-schedule payments all land in escrow and are attributed by FL; anything unattributable goes to `SUSPENSE` with an ops exception. Late payment may attract a `PENALTY` posting per contract terms.

**Ledger:** `REPAYMENT`: debit `BORROWER` → credit `OMNIBUS_CASH`. **States:** instalment `DUE → PAID`; schedule recalculated on early repayment.

---

### Step 8 — Distribution to lenders (outbound, pro-rata, one-to-many)

**Actors:** FL, VPBank, lenders (N).

Once a repayment has cleared, FL computes each lender's pro-rata entitlement and FL's fee, then instructs VPBank to pay every lender's verified settlement account from the project escrow account. This is the one-to-many leg: one inbound repayment fans out to N outbound payments plus a fee.

**Integration point — B4 batch, with per-leg status, plus B7.** Batch payment initiation is what makes this step viable — instructing N payments individually, or by manual file upload, does not scale past a pilot. Per-leg status matters because **partial batch failure is normal**: if three of twelve legs fail, the other nine must settle and the three failed amounts **remain in the project escrow account** for retry. They are never re-purposed, and never netted against another project.

**Ledger:** one `REPAYMENT_SPLIT` transaction with N `DISTRIBUTION` legs (debit `OMNIBUS_CASH` → credit each `LENDER`) plus a `FEE` leg (debit `OMNIBUS_CASH` → credit `FL_REVENUE`). This is the multi-leg case the ledger was designed for, posted atomically.

> **Design note for FL, internal.** FL's `post_transaction()` requires that any account touched by more than one leg nets to zero within that transaction. `OMNIBUS_CASH` is a pass-through here, so a combined collect-and-distribute transaction is only valid when the **entire** repayment is distributed immediately. Any case where FL retains part of a repayment in escrow — a failed leg, a rounding residual, a distribution held pending investigation — must be posted as **separate transactions** (Step 7 inbound, Step 8 outbound) rather than one. Worth an explicit test.

**States:** distribution records `PENDING → SETTLED`; failed legs retried.

---

### Step 9 — Loan closure, share conversion and escrow account closure

**Actors:** FL, VPBank, SME, lenders.

When the final instalment is collected and distributed, the loan is complete. FL issues each lender their converted shares per the contract, closes the contract, and closes out the escrow account.

Closure has a hard precondition: **the escrow account must reconcile to zero.** FL's ledger balance for `OMNIBUS_CASH` on that contract and VPBank's balance must both be zero and must agree. Any residual — typically sub-unit rounding on a pro-rata split — is resolved to a documented destination before closure. *(Open question: rounding residual policy. FL's proposal is to allocate residuals to the lender with the largest holding, deterministically, rather than to `FL_REVENUE`, so that FL never benefits from rounding.)*

**Integration point — B6, then B8.** Final statement retrieval, reconciliation attestation, then account closure. FL retains the statement, the full ledger history and the reconciliation record for audit. Decree 94 licences run up to two years and may be extended twice by one year each; records must outlive the licence and be producible for SBV inspection on demand.

**Ledger:** final postings; balances net to zero on the contract. **States:** `Contract → CLOSED`; `Listing → CLOSED`; `custodial_accounts.status: ACTIVE → CLOSED`.

---

## 6. Cross-Cutting Operations

These run continuously alongside the nine steps rather than at a single point.

**Daily reconciliation.** FL retrieves each active escrow account's statement (B6) and reconciles it line by line against the ledger. Discrepancies raise an ops exception; FL never adjusts the ledger to match the bank, because the ledger is append-only — a genuine difference is resolved by posting a correcting transaction with a documented reason. FL also takes periodic balance snapshots per escrow account for reporting and dispute evidence. **FL requests stable, immutable transaction identifiers on statement lines**, so the same line is recognisable across retrievals.

**Exception handling.** Every unmatched credit, failed payment leg and reconciliation break becomes an ops queue item with an owner and an SLA. The suspense account is the ledger's structural home for money that has arrived but cannot yet be attributed; it must be swept to zero, and a persistent non-zero suspense balance is a reportable control failure.

**Incident reporting.** Decree 94 requires incident reporting to the SBV **within 24 hours**, alongside periodic operational reports. FL needs VPBank's incident notification path and timeline to meet that on the banking side — if a settlement failure or outage is material, FL's 24-hour clock starts when it happens, not when FL notices. *(This obligation is not yet recorded in ADR-004 and should be added.)*

**Cut-off times and value dating.** FL needs VPBank's payment cut-off times, value-dating rules and non-business-day behaviour, since they determine what FL can promise lenders and borrowers about when money moves.

**Dispute handling.** A beneficiary dispute is raised with FL, not VPBank — FL is the account holder and the record keeper. FL's immutable ledger plus VPBank's statements form the evidence set. An escalation path and evidence-request process between the two organisations needs defining.

---

## 7. Business Rules

1. **One escrow account per loan contract.** No pooling across projects, at any time, for any reason.
2. **No cross-contract netting.** A ledger transaction never spans two contracts; enforced in code and raised as an error.
3. **FL never holds customer funds.** All funds sit in VPBank escrow accounts. FL holds only its own earned fee revenue, in its own operating account.
4. **Settlement only to verified accounts.** Money leaves escrow only to a settlement account that passed name verification (Step 2) for a party verified in Step 1.
5. **Explicit fees.** FL's fee is always a `FEE` ledger leg, visible and auditable. Never a silent deduction.
6. **Idempotency everywhere.** Every payment instruction and every inbound notification carries a key; replays return the original result and write nothing new.
7. **Append-only ledger.** No UPDATE or DELETE, ever, at either the application or database layer. Corrections are reversing entries.
8. **Balances are computed, never stored.** `SUM(credits) − SUM(debits)` at read time.
9. **VND only**, per Decree 94.
10. **Loan term ≤ 2 years**, per Decree 94 — and therefore escrow account life ≤ 2 years plus closure.
11. **Escrow must reconcile to zero before closure.**
12. **FL takes no position and gives no guarantee.** FL does not lend, does not underwrite the credit risk, and does not guarantee any loan.

---

## 8. Regulatory Allocation

### 8.1 Who carries what

| Obligation | FL | VPBank |
|---|---|---|
| Decree 94 sandbox licence and conduct | Owns | — |
| CDD on FundLok as account holder | Provides records | **Owns** |
| KYC/KYB on beneficiaries | **Owns** (Didit) | Audit and inspection rights — *scope to be agreed, Step 1* |
| Settlement via bank accounts or e-wallets only | Enforces at linking | Provides the accounts |
| Borrower maximum debt balance | **Owns** (`app/compliance/`, to be built) | — |
| Loan term ≤ 2 years | **Owns** (validation) | — |
| Full auditability of platform activity | **Owns** (immutable ledger, audit logs) | Statements as corroborating evidence |
| Circular 64 conformance of the API | Conforms as consumer | **Owns** as provider |
| AML transaction monitoring | Monitors platform activity | Owns bank-side obligations |
| 24-hour incident reporting to SBV | **Owns** | Must notify FL of banking incidents in time to meet it |
| Vietnam data residency, no cross-border processing | **Owns** | Must not process FL sandbox data offshore |

### 8.2 What FL has already built toward this

Not aspirational — merged and tested:

- **Double-entry, append-only ledger** with the `custodial_account` escrow seam, database-level immutability trigger, and cross-contract netting prohibition (`app/ledger/`, migration `862160bce972`, PR #18).
- **KYC/KYB verification** live via Didit (`app/verification/`, `app/gverify/`).
- **Event-level idempotency** on financial postings — the mechanism that makes bank webhooks safe.
- **Async infrastructure** throughout: `AsyncSession`, typed Pydantic contracts, JWT with refresh-token revocation, Argon2, RBAC, audit logging.
- **Settlement account linking**, currently mocked and ready to be backed by B2.

Still to build, and dependent on this partnership: `bank_transactions` and reconciliation, the VPBank API client, the compliance module (exposure caps, CIC, reporting), and escrow provisioning.

---

## 9. Open Questions for VPBank

Ordered by how much they block progress.

| # | Question | Why it matters |
|---|---|---|
| 1 | Does VPBank require its own CDD on each beneficiary, or will it rely on FL's KYC/KYB with audit rights? | Determines whether lender onboarding takes minutes or days. Highest-impact question in this document. |
| 2 | Can VPBank issue **per-lender virtual account numbers** under a project escrow account? | Removes reference-matching risk entirely; the single highest-leverage technical capability. |
| 3 | What is the permitted account title format for an FBO escrow arrangement, and is it a current account with escrow terms or a distinct product? | Fixes the account structure and the contractual documents. |
| 4 | Which of B1–B9 exist today, and what is the delivery timeline for the rest? | Determines how much of the flow runs manually at launch and for how long. |
| 5 | Is there a sandbox or test environment, and what are the credentialing steps? | FL cannot write integration tests against production. Blocks the build. |
| 6 | Does VPBank map to ISO 20022 on its side, or does FL carry the mapping burden? | Circular 64 C3. Sizes FL's payload work. |
| 7 | Does interest accrue on escrow balances, and whose is it? | Beneficiary entitlement and FL's allocation rule. |
| 8 | Payment cut-off times, value dating, non-business-day behaviour, and per-transaction limits? | Determines what FL can promise users about timing. |
| 9 | Can VPBank provide **CIC lookup** as part of the partnership? | Resolves an open ADR-004 item and strengthens FL's credit process. |
| 10 | Can VPBank support **standing instructions or direct debit mandates** for borrower repayment? | Materially improves collection rates. |
| 11 | Account opening lead time and any per-account cost or minimum balance? | Per-project accounts mean volume; sizes the operational and cost model. |
| 12 | VPBank's incident notification path and timeline? | FL has a 24-hour SBV reporting obligation. |

## 10. Open Questions for FL, Internal

| # | Question | Owner |
|---|---|---|
| 1 | Strict mode for `resolve_custodial_account()` so escrow mode raises instead of falling back to `PLATFORM` (Step 4 note). | Edward |
| 2 | Rounding residual policy on pro-rata distribution (Step 9). | Edward |
| 3 | Order expiry semantics and the `PENDING_PAYMENT` gap — touches Phat-owned `app/market/` (Step 5, GAP-2). | Edward + Phat |
| 4 | Rename `OMNIBUS_CASH` to an escrow-neutral identifier; requires a migration. | Edward |
| 5 | Does ADR-002 get superseded by a new ADR recording VPBank as the signed partner and escrow as the launch topology? Recommend yes — ADR-008. | Edward |
| 6 | Add Decree 94's 24-hour incident reporting and VND-only requirements to ADR-004. | Edward |
| 7 | Per-lender virtual accounts: if VPBank supports them, does `linked_accounts` become the cache in front of them, or a separate table? | Edward |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-08-04 | Edward | Initial draft — FBO escrow structure, nine-step lifecycle with VPBank integration points, B1–B9 integration surface, regulatory allocation, open questions both directions. |
