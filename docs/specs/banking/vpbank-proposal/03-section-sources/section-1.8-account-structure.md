# 1.8 Account structure — Option A and Option B

*[CONTENT — Loc and Edward. English draft for internal review; Vietnamese version to follow.]*

---

Two account structures can carry the arrangement described in Sections 1.3, 1.4 and 3.1. Both keep investor funds segregated from FundLok's own money, both permit the same eight money movements, and both support the closed-loop rule. They differ in one respect: **whose name the accounts are held in**, and therefore where an investor's un-withdrawn balance physically rests.

- **Option A — FBO.** A restricted escrow account per loan, held in FundLok's name *for the benefit of* the SME and that loan's investors. Repayment receipts accumulate in that account and each investor's entitlement is tracked in FundLok's ledger. On a withdrawal request, the balance transfers to the investor's own bank account.
- **Option B — Escrow.** Each investor holds their own escrow account at VPBank, opened in the investor's own name, alongside a project escrow account that acts as the collection point for each loan. Repayment receipts are allocated daily into each investor's escrow account. On a withdrawal request, the balance transfers from there to the investor's own bank account.

Both are set out below against the same four elements, followed by a recommendation and a migration trigger.

**Assumptions.** FundLok internal estimates dated 5 August 2026: 5–10 loans funded per month during the pilot; investors are family offices deploying approximately USD 200,000 each across ten to fifteen borrowers, implying five to eight investors on a loan of VND 2.5 billion; 22 business days per month; daily revenue-share collection per Section 1.4.

---

## 1.8.1 Option A — FBO

### Description

One restricted escrow account per loan, titled in FundLok's name for the benefit of the loan's beneficiaries. Investors fund it, it disburses to the SME, and it receives the daily revenue-share repayments. Each investor's share of what has been collected is recorded in FundLok's double-entry ledger rather than as a separate bank balance. When an investor asks to withdraw, FundLok instructs a transfer from the escrow account to that investor's own registered bank account. An un-withdrawn balance stays in the escrow account and may be directed into a new loan.

### Build requirement

| Element | Requirement |
|---|---|
| Accounts to open | One per loan — 5–10 per month at pilot volume |
| VPBank capability needed | Restricted account with a bank-enforced permitted-destination list, dual-control instruction channel, daily machine-readable statement. All within Phase 1 as specified in Section 3.3 |
| Account opening | Operational process is sufficient at this volume; no automation required |
| FundLok build | As already specified in Section 3.5. The ledger that tracks each investor's entitlement is built and in production |
| Daily movements per loan | Two — one inbound receipt and one fee movement. Allocation is a ledger posting, not a transfer |

### Pros

Simple to operate and cheap to run: roughly 336 movements a month at 10 active loans and 1,568 at 60, because allocation is a ledger posting and generates no bank transfer. Account opening stays within an operational process for the whole pilot and well beyond. Reinvestment is frictionless, since an un-withdrawn balance is already in an account that can fund a new loan. Fewer accounts means a shorter permitted-destination list and less reconciliation surface. It also imposes the lighter Phase 1 ask on VPBank, which makes it the faster structure to get live.

### Cons

The decisive weakness is legal rather than operational. Because the account is titled in FundLok's name, the protection of investor funds in a FundLok insolvency depends on the *for the benefit of* designation being recognised — that the funds are not FundLok's property and so form no part of its estate. That is a question of Vietnamese law and of how the designation is documented, not a matter FundLok can assert. The same titling raises an accounting question: an auditor may require the balance to be recognised on FundLok's balance sheet with an offsetting liability rather than treated as fully off-balance-sheet.

Consequently, VPBank has to take some comfort from FundLok's ledger for the proposition that each investor's share is what FundLok says it is. The ledger is append-only, immutable at the database layer and reconciled daily against VPBank's own statement — but it is still FundLok's record of a division that has no independent expression in the banking system. An investor's claim is an entitlement, not a bank balance in their own name.

---

## 1.8.2 Option B — Escrow

### Description

Each investor holds an escrow account at VPBank in their own name, opened once and reused across every loan they participate in. A project escrow account per loan acts as the collection point: investors fund it, it disburses to the SME, and it receives the daily revenue-share repayments. Each cleared receipt is allocated the same day into each investor's own escrow account. A withdrawal transfers from the investor's escrow account to their own registered bank account. Reinvestment moves the balance from the investor's escrow account into a new project escrow account.

### Build requirement

| Element | Requirement |
|---|---|
| Accounts to open | One per loan, plus one per investor held permanently. At pilot volume roughly 1–10 new investor accounts per month, because family offices are large tickets and each account is reused across ten to fifteen loans |
| VPBank capability needed | Everything in Option A, plus capacity to execute daily internal allocation across investor accounts, and a permitted-destination list large enough for n+2 entries per project |
| Account opening | Operational process is sufficient at pilot volume; automation needed once new investor accounts exceed roughly 25 per month, which is the trigger already set for Section 3.4 item P6 |
| FundLok build | As Section 3.5, plus the allocation instruction becoming a daily batch rather than a ledger posting |
| Daily movements per loan | Ten on the working case — one inbound receipt, eight allocations and one fee. Movement counts in 1.8.3 also include investor funding, disbursement and withdrawals, so they exceed the daily-cycle figures in Section 1.4.7 |

### Pros

The investor's money is in an account in the investor's own name. In a FundLok insolvency the funds are not in FundLok's estate at all, so the question of whether a designation holds up does not arise. VPBank can prove segregation from its own records without relying on FundLok's ledger, and the accounting question disappears with it. Each investor's balance is a bank balance, evidenced by a statement in their own name — which is both a stronger legal position and a better thing to be able to tell an investor. It is also the structure VPBank is understood to prefer, for exactly these reasons.

### Cons

More accounts and considerably more movement: roughly 13,400 movements a month at 60 active loans against 1,570 under Option A, almost all of the difference internal to VPBank. That costs FundLok little in staff time — around 0.28 against 0.21 of a full-time role at month 12 — but it is real processing on VPBank's side, and whether they can absorb it, and how they price it, is not yet established. Automated account opening becomes necessary earlier than under Option A. Reinvestment requires a transfer back rather than being a book entry. And the permitted-destination list has to hold ten entries per project on the working case, roughly 600 live entries at 60 active loans, which is a scale requirement no one has yet confirmed VPBank's product supports.

---

## 1.8.3 The two options side by side

| | Option A — FBO | Option B — Escrow |
|---|---|---|
| Account holder | FundLok, for the benefit of the beneficiaries | Each investor, in their own name |
| Accounts at pilot volume | 5–10 per month, one per loan | 5–10 per loan per month, plus 1–10 new investor accounts per month |
| Investor's balance is | An entitlement in FundLok's ledger | A bank balance in the investor's own name |
| Movements per month at 60 active loans | ~1,570 | ~13,400 |
| FundLok operating load at month 12 | 0.14–0.21 FTE | 0.18–0.28 FTE |
| Insolvency protection | Depends on the FBO designation being recognised | Structural — funds are not in FundLok's estate |
| Accounting question | Auditor may require on-balance-sheet with offsetting liability | Does not arise |
| VPBank must rely on FundLok's ledger for the split | Yes, to a degree | No |
| Automated account opening needed | Not for the foreseeable pilot | Once new investor accounts exceed ~25 per month |
| Phase 1 ask of VPBank | Lighter | Adds internal allocation capacity and a larger destination list |

---

## 1.8.4 Recommendation

**FundLok recommends Option B.**

The reasoning is that the operational penalty is small and the legal benefit is not. Option A is simpler and cheaper to run, but the difference is roughly 0.07 of a full-time role at month 12 and some additional internal processing at VPBank — while the difference in the investor's protection is the difference between a claim that depends on a designation surviving legal scrutiny and one that never enters FundLok's estate in the first place. On a platform whose entire proposition is that it takes no position and never holds customer money, the structure that makes that literally true is worth the operating cost.

Three supporting reasons. It removes the accounting question rather than answering it. It removes VPBank's need to take comfort from FundLok's ledger for the division of funds, which is the thing hardest for a custodian to accept. And it is the direction VPBank is understood to favour, so it is not a point on which FundLok would be spending credibility to save very little.

The recommendation is conditional on two confirmations from VPBank, neither of which FundLok can answer: that VPBank can execute the daily internal allocation volumes in 1.8.3, and that the permitted-destination list can hold at least ten entries per project account with controlled amendment during the account's life. If either is not available, Option A is the fallback and the pilot should not be delayed for it — the structures are not so different that starting on A forecloses moving to B.

---

## 1.8.5 Migration

Migration is relevant in two distinct cases and they should not be conflated.

**Case 1 — a lower-commitment pilot, then a target structure.** FundLok may begin with the lightest arrangement VPBank can support quickly — manual instructions, a single project escrow account per loan, no per-investor accounts — in order to prove the flow on the first few loans before either structure is committed to. This is Option A in practice, whether or not it is described that way.

**Case 2 — Option A to Option B.** Where A is adopted as the launch structure and B is the target, the migration provisions an escrow account for each existing investor, transfers each investor's tracked entitlement from the project escrow account into their new account, and switches allocation from a ledger posting to a daily transfer. Existing loans continue without interruption; the loan agreements are unaffected, because the structure sits beneath them.

**Trigger, expressed as a volume number.** Migration from Option A to Option B is initiated when **new investor accounts would exceed 25 per month**, sustained across two consecutive months.

The number is chosen because 25 accounts a month is approximately where a manual account-opening process stops absorbing the load — at 15 minutes per account that is about 6 staff-hours a month, and beyond it the cost grows faster than the benefit of deferring. It is deliberately the same threshold already set for automated account opening in Section 3.4 item P6, so the two do not drift apart: the point at which B becomes worth migrating to is the point at which VPBank needs to automate account opening anyway.

Two secondary triggers, either of which would bring migration forward regardless of volume: an investor or counsel requiring that balances be held in the investor's own name, or a change in the accounting treatment of the Option A balance that FundLok's auditor is unwilling to support.

**Not a date.** Migration is not scheduled. If the volume trigger is never reached, Option A remains in place indefinitely, and that is an acceptable outcome rather than a deferred obligation.

---

## 1.8.6 Items to be confirmed

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 1 | Whether VPBank can execute daily internal allocation at the volumes in 1.8.3, and how it prices them | The recommendation of Option B is conditional on this | VPBank, requested by Edward | Pending VPBank confirmation |
| 2 | Maximum number of entries on a permitted-destination list per account, and whether entries can be added during the account's life | Option B needs at least n+2 entries per project, roughly 600 live at 60 active loans | VPBank, requested by Edward | Pending VPBank confirmation |
| 3 | Whether the FBO designation under Option A is recognised such that funds fall outside FundLok's estate | The central weakness of Option A. If counsel confirms it robustly, A becomes materially more attractive | Edward, with counsel | 2026-08-14 |
| 4 | Accounting treatment of the Option A balance — on-balance-sheet with offsetting liability, or off-balance-sheet with disclosure | Determines what FundLok can state to VPBank in writing | Loc, with FundLok's accountant | 2026-08-14 |
| 5 | Confirmation that VPBank does in fact prefer Option B, and on what grounds | Stated here as FundLok's understanding rather than as established fact | Loc, with VPBank | Pending VPBank confirmation |
| 6 | Whether an investor may hold one escrow account across all loans, or whether VPBank requires one per loan per investor | If the latter, Option B's account count rises by an order of magnitude and the recommendation changes | VPBank, requested by Edward | Pending VPBank confirmation |
| 7 | Expected new-investor onboarding rate, once sales targets are set | The migration trigger in 1.8.5 is expressed against it | Loc | 2026-08-12 |

---

*Dependencies: Section 3.3 (Phase 1 requirements). Consistent with Section 1.3 (four-sided structure), Section 1.4 (money flow), Section 1.7 (role boundaries), Section 3.1 (process) and Section 3.4 (Phase 2, whose P6 trigger shares the 25-per-month threshold). Insolvency and accounting treatment are documented in Section 4.5.*
