# 3.1 End-to-end process — nine steps from onboarding to loan closure

*[CONTENT — Edward and Loc. English draft for internal review; Vietnamese version to follow.]*

---

This section sets out the complete operating process for one loan, from the onboarding of the parties through to closure and release of the escrow account. It names the accountable owner for each of the nine steps and shows the process as a swim-lane diagram.

Four parties take part, each in one role only. The **investor** is the lender of record and owner of the loan. The **SME** is the borrower. **FundLok** is the arranger and servicer: it appraises, connects, issues payment instructions and reconciles, and it is not a party to the loan agreement. **VPBank** is the neutral custodian: it holds funds in a restricted-purpose escrow account and executes transfers to pre-agreed destinations on instruction.

Two principles govern the whole process and are visible in every step below. First, **FundLok moves instructions and data, never funds** — no step gives FundLok possession of, or a withdrawal right over, capital in the escrow account. Second, **the loop is closed**: money leaves the escrow account only to a verified borrower account, to the account an investor's money originally came from, or to FundLok's fee account — and in that last case only as a fixed proportion of an instruction that pays a beneficiary in the same movement. FundLok can never draw on a balance sitting idle. Section 1.4 sets this out in full.

A single loan has one borrower and one or more investors. Where a step below refers to "the investor", it applies to each participating investor individually, and each investor's entitlement is tracked and returned separately.

---

## 3.1.1 The nine steps at a glance

| # | Step | What happens | Accountable owner |
|---|---|---|---|
| 1 | Investor onboarding & account opening | Investor is onboarded to the platform; VPBank independently completes its own customer due diligence and opens the investor's account | VPBank — Onboarding (account opening) · FundLok — Onboarding Operations (platform registration) |
| 2 | SME onboarding, appraisal & listing | SME is onboarded and appraised by FundLok; rate tier assigned; the opportunity is published | FundLok — Credit & Underwriting |
| 3 | Escrow account provisioning | The restricted-purpose escrow account for the loan is opened and configured with its permitted-destination list and dual-control instruction channel | VPBank — Custody Operations |
| 4 | Loan agreement execution | Loan agreement signed directly between investor and SME; management authorisation and platform terms executed | FundLok — Platform & Legal Operations |
| 5 | Funding into escrow | Each investor funds the escrow account, from their own registered account or from a balance already held; the originating account is recorded | Investor (transfer) · VPBank — Custody Operations (credit and notification) |
| 6 | Disbursement to the SME | Disbursement conditions verified; FundLok issues a dual-control instruction; VPBank disburses to the SME's verified account | FundLok — Treasury Operations (instruction) · VPBank — Custody Operations (execution) |
| 7 | Daily revenue-share collection | Each business day FundLok computes the amount due from the SME's prior-day revenue and requests it; the SME pays into the escrow account | SME (payment) · VPBank — Collections (credit and notification) |
| 8 | Allocation and return to investors | FundLok computes each investor's entitlement and its own fee in one instruction; VPBank allocates to investors and pays the fee | FundLok — Treasury Operations (instruction) · VPBank — Custody Operations (execution) |
| 9 | Closure & release of the escrow account | Final amounts returned, balance reconciled to zero, statements issued, escrow account released | FundLok — Reconciliation & Reporting · VPBank — Custody Operations (release) |

No step is without an owner. Where two owners are named, the first is accountable for initiating the step and the second for executing it; accountability does not transfer.

---

## 3.1.2 The steps in detail

### Step 1 — Investor onboarding and account opening

The investor registers on the FundLok platform, where FundLok records the information it needs to operate the relationship and to act under the management authorisation contract. Separately and independently, VPBank performs its own customer due diligence on the investor and opens the investor's account in accordance with the structure adopted in Section 1.8.

**These two processes are distinct and neither substitutes for the other.** FundLok's onboarding serves the platform relationship. VPBank's due diligence is the bank's own, conducted to the bank's own standards and on the bank's own judgement, and FundLok makes no request that VPBank place reliance on FundLok's process or records.

*Owner: VPBank — Onboarding (account opening) · FundLok — Onboarding Operations (platform registration).*

### Step 2 — SME onboarding, appraisal and listing

The SME registers, submits financial and corporate documentation, and provides the personal guarantee of the business owner. FundLok conducts the credit appraisal, assigns the interest rate tier, and publishes the opportunity to investors.

VPBank conducts no appraisal, makes no credit assessment and takes no part in the lending decision. The decision to lend rests with the investor alone. Credit risk sits with the investor and never reaches VPBank.

*Owner: FundLok — Credit & Underwriting.*

### Step 3 — Escrow account provisioning

Before any money moves, the restricted-purpose escrow account for the loan is opened at VPBank. It is configured with two controls that are not optional: a **permitted-destination list**, so funds can only be released to a verified borrower account or to a registered investor originating account; and a **dual-control instruction channel**, so no single individual at FundLok can cause a transfer. Requirements for both are specified in Section 3.3.

FundLok requests the account and supplies the destination list. VPBank opens and configures it.

*Owner: VPBank — Custody Operations, on FundLok's request.*

### Step 4 — Loan agreement execution

The loan agreement is executed directly between the investor and the SME; the investor becomes the lender of record and the owner of the loan. In parallel, the investor executes the management authorisation contract with FundLok, and the SME accepts the platform terms of use. VPBank is not a party to the loan agreement.

FundLok generates the contract set and records the investor's commitment against the loan.

*Owner: FundLok — Platform & Legal Operations.*

### Step 5 — Funding into escrow

Each investor funds their commitment into the escrow account for that loan, either by transfer from **their own registered account** or from a balance already held from an earlier loan (Section 1.4, movement M8). VPBank credits the account and notifies FundLok; FundLok reconciles the credit against the commitment and records the originating account.

Recording the originating account at this step is what makes the closed loop enforceable later: the account that money came in from is the only account it can be returned to.

Funds credited to the escrow account but not attributable to a commitment are held unallocated and raised as an exception rather than applied on assumption.

*Owner: Investor (transfer) · VPBank — Custody Operations (credit and notification).*

### Step 6 — Disbursement to the SME

Disbursement proceeds only when all of the following are true: the loan agreement is signed, the full committed principal has been received into the escrow account, and the SME's receiving account has been verified and is on the permitted-destination list. FundLok verifies these conditions and issues a dual-control instruction. VPBank checks the conditions on its own terms and disburses to the SME's verified account.

The disbursement fee, approximately 1% of gross principal, travels inside this same instruction as a proportion VPBank can verify. It is funded by the SME, whose repayment obligation is calculated on the gross principal — so investors remain whole on their full capital.

Disbursement draws only on the escrow balance belonging to that loan. There is no pooled balance across loans, so one loan can never fund another.

*Owner: FundLok — Treasury Operations (instruction) · VPBank — Custody Operations (execution).*

### Step 7 — Daily revenue-share collection

Repayment is a **daily revenue share, not a fixed instalment schedule.** Each business day FundLok reads the SME's prior-day revenue from its e-invoice data through a licensed T-VAN provider, computes the agreed percentage, and issues the SME a payment request through the platform. The SME pays that amount into the escrow account by VietQR or bank transfer, quoting the reference FundLok supplies. VPBank credits the account and notifies FundLok, which attributes the receipt and reconciles it.

Because the amount tracks actual trading, a slow week produces smaller receipts and a strong week larger ones, with the total obligation unchanged. This is what makes the product workable for revenue-variable small businesses, and it is why the cycle is daily rather than monthly.

Receipts that cannot be attributed are held unallocated and raised as an exception rather than applied on assumption. Treatment of a surplus beyond the outstanding balance is an item to be confirmed in Section 1.4.

*Owner: SME (payment) · VPBank — Collections (credit and notification).*

### Step 8 — Allocation and return to investors

FundLok computes each investor's entitlement from the amounts collected and issues a dual-control instruction. VPBank transfers to **each investor's originating account, and only that account**. This is the closed-loop rule in operation. **Availability and transfer are different things**: an investor's share is available as soon as the day's allocation is posted, and is transferred to their external bank account when they request it. Daily availability does not require a daily outbound payment to every investor's bank.

Where a transfer to one investor fails, the other transfers still settle and the failed amount remains in the escrow account for retry. It is never redirected, never applied to another investor and never applied to another loan.

FundLok's loan management fee travels **inside this same instruction**, as a fixed proportion of the amount being allocated, so VPBank can verify it on the face of the instruction. It is funded by the investors and taken from return, never from principal. FundLok's other fee — the disbursement fee, funded by the SME — travels inside the disbursement instruction at Step 6. Neither fee can be issued as a movement on its own, and neither can draw on a balance sitting idle. Section 1.4.4 sets out the four constraints in full.

*Owner: FundLok — Treasury Operations (instruction) · VPBank — Custody Operations (execution).*

### Step 9 — Closure and release of the escrow account

When the final amounts have been collected and returned, FundLok performs the closing reconciliation. The escrow account must reconcile to a zero balance, agreed between FundLok's records and VPBank's statement, before it is released. VPBank issues the final statement and releases the account; FundLok closes the loan record and retains the statement, the reconciliation and the full instruction history for audit.

Where a dispute or default prevents normal closure, the account is held under the mechanism described in Section 4.1 rather than released.

*Owner: FundLok — Reconciliation & Reporting · VPBank — Custody Operations (release).*

---

## 3.1.3 Swim-lane diagram

The diagram accompanying this section shows the nine steps as rows and the four parties as columns, with the accountable owner named against each step. Cells drawn with a dashed outline state what a party deliberately does **not** do, so the boundaries of each role are legible from the diagram alone. The diagram is designed to remain readable at A4.

*[Insert: `section-3.1-swimlane` — nine-step swim-lane, four parties, owner per step.]*

---

## 3.1.4 Controls that hold at every step

| Control | How it operates | Where specified |
|---|---|---|
| Permitted destinations | Funds leave the escrow account only to a verified borrower account, a registered investor originating account, or FundLok's fee account. | Section 1.7, Section 1.4.4, Section 3.3 |
| Fee is never standalone | A fee line is permitted only inside an instruction that pays a beneficiary in the same movement, as a proportion VPBank can verify. It cannot draw on idle balance, and it is suspended while an account is frozen. | Section 1.4.4 |
| Closed loop | Each investor's return goes only to the account that investor funded from. | Section 1.4 |
| Dual control | No single FundLok individual can cause a transfer; every instruction requires two authorised parties. | Section 3.3 |
| Segregation by loan | Each loan's funds are held separately; no pooled balance and no netting between loans. | Section 1.8 |
| Instruction, not possession | FundLok issues instructions within conditions the bank enforces; it holds no withdrawal right. | Section 1.3 |
| Independent due diligence | VPBank performs its own customer due diligence and is not asked to rely on FundLok's. | Section 1.7 |
| Full audit trail | Every instruction, receipt and transfer is recorded and reconcilable against VPBank's statements. | Section 3.5, Appendix C |
| Exception handling | Unattributable receipts and failed transfers are held and escalated, never applied on assumption. | Section 3.7 |

---

## 3.1.5 Items to be confirmed

Per the general rule, nothing below is guessed. Each item carries a named owner and a date.

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 1 | The revenue-share percentage, and whether it varies by grade | Determines the size of each daily collection at Step 7 | Loc + Edward | 2026-08-12 |
| 2 | The loan management fee rate, and the registered ceiling for both fees | Steps 6 and 8 state the fees as verifiable proportions; the values must be stated for VPBank to enforce them | Loc, with Edward | 2026-08-12 |
| 3 | Account structure adopted — Option A or Option B of Section 1.8 | Determines whether Step 8's allocation is a bank transfer or a ledger posting | Loc + Edward (Section 1.8) | 2026-08-12 |
| 4 | Whether VPBank's existing blocked-account product can serve as the restricted-purpose escrow account, or a new configuration is required | Determines whether Step 3 is configuration or a new build | Edward, with VPBank (Section 3.3) | Pending VPBank confirmation |
| 5 | Form of the dual-control instruction channel for the pilot | Steps 6 and 8 depend on it | Edward (Section 3.3) | Pending VPBank confirmation |
| 6 | Cut-off times, value dating and non-business-day handling | Determines what FundLok can commit to investors and SMEs on timing in Steps 6, 7 and 8 | Edward (Appendix C) | Pending VPBank confirmation |
| 7 | Definition of "verified" for an SME receiving account and an investor originating account | The permitted-destination control in Step 3 depends on this definition | Edward, with VPBank | 2026-08-07 |

---

*Dependencies: this section depends on Section 1.4 (money flow) and Section 1.5 (data flow), and must remain consistent with Sections 1.3, 1.7, 1.8, 3.3 and 3.4.*
