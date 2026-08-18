# 3.7 Integration and testing

*[CONTENT — Edward. English draft for internal review; Vietnamese version to follow.]*

---

This section sets out how the FundLok–VPBank integration is brought into service: the stages it passes through, the specific transactions used to test it, the method by which reconciliation is proved correct, and the criteria that must be met before live money moves at pilot volume.

The approach is conservative by design. Because Phase 1 uses a batch instruction channel and a daily statement rather than an API (Section 3.3), there is little software integration to test on VPBank's side — the testing effort goes into proving that the **controls** behave as specified, particularly the two that carry the most consequence: that funds cannot be released to a destination outside the permitted list, and that a repeated instruction cannot produce a second payment.

Testing deliberately includes **negative cases**. A test suite that only proves money moves when it should is not evidence of a working control; the tests that matter are the ones that prove money does *not* move when it should not.

---

## 3.7.1 Stages

| Stage | What happens | Money at risk | Exit condition |
|---|---|---|---|
| 0 — Confirmation | VPBank answers the questions in Section 3.3, and both parties agree which items are configuration and which are build. Field formats for the instruction channel and statement are exchanged | None | A signed-off requirement list, with each item of Section 3.3 marked confirmed, amended or not available |
| 1 — Provisioning & connectivity | One escrow account is opened for testing. FundLok's authorised users are entitled with separated prepare and approve rights. Statement retrieval is established and parsed by FundLok's reconciliation | None | FundLok can retrieve and parse a statement for the test account without manual intervention |
| 2 — Control tests | The negative and control test cases in 3.7.2 are executed on the test account with nominal amounts | Nominal only | All control test cases pass, with the permitted-destination and duplicate-instruction tests passing without exception |
| 3 — First live loan | One real loan runs end to end: real investors, real SME, real money, closely supervised, with every step manually verified against Section 3.1 | One loan | The loan completes and the escrow account reconciles to nil, with no unexplained entry |
| 4 — Supervised production | Loans run at pilot volume with daily reconciliation reviewed by a named individual rather than by exception only | Pilot volume | Thirty consecutive days with no unreconciled item older than one business day |
| 5 — Steady pilot | Normal running. Reconciliation is reviewed by exception; volumes are tracked against the Phase 2 trigger in Section 3.4 | Pilot volume | — |

Stages 0 to 2 involve no customer funds. Stage 3 deliberately restricts exposure to a single loan, so that any defect in the control set is discovered while the amount at risk is one loan rather than a portfolio.

---

## 3.7.2 Test transactions

All monetary test amounts are nominal: VND 10,000 per test transfer, chosen as the smallest value that exercises a real transfer rather than a zero-value validation. Where a test requires a second account, FundLok provides its own operating account as the counterparty so that no customer is involved in a failing case.

### Control and negative tests — Stage 2

| Ref | Test | Expected result |
|---|---|---|
| T1 | Account titling and segregation — inspect the opened account's registered title and confirm it is segregated from FundLok's operating accounts | Title matches the agreed format; account is not linked to FundLok's own accounts for set-off or sweeping |
| T2 | **Permitted-destination enforcement** — instruct a transfer to an account that is not on the permitted-destination list | **Instruction rejected by VPBank.** No funds move. Rejection reason returned and readable by FundLok |
| T3 | Permitted destination, valid — instruct a transfer to an account that is on the list | Executed. Appears on the statement with a stable identifier |
| T4 | **Dual control** — submit an instruction authorised by only one FundLok user | **Instruction not executed.** Rejected or held pending a second authorisation |
| T5 | Dual control, segregation of duty — attempt to have the same individual both prepare and approve | Not permitted by the channel entitlement |
| T6 | **Duplicate instruction** — submit the same instruction reference twice | **Exactly one payment results.** The second submission is rejected or returns the original outcome |
| T7 | Inbound attribution — pay into the escrow account via VietQR quoting a FundLok reference | Credit appears on the statement with the full reference intact and the remitter name and account present |
| T8 | Inbound attribution, reference length — pay quoting a reference at the maximum length FundLok intends to use | Reference preserved without truncation |
| T9 | Inbound attribution failure — pay with no reference, or a malformed one | Credit appears; FundLok's reconciliation flags it as unattributed and raises an exception rather than applying it to a loan |
| T10 | Batch with a failing line — submit a batch in which one destination is invalid and the others are valid | Valid lines execute; the invalid line is rejected at line level with a reason; **the failed amount remains in the escrow account** |
| T11 | Statement identifier stability — retrieve the same statement period twice on different days | Every transaction identifier is unchanged between retrievals |
| T12 | Statement date range — request a historical range rather than the latest day | Complete period returned |
| T13 | Balance agreement — compare VPBank's reported balance with FundLok's ledger position for the test account | Figures agree exactly |
| T14 | Entitlement revocation — FundLok notifies removal of an authorised user, then that user attempts to approve | Approval refused |
| T15 | Cut-off behaviour — submit an instruction immediately after the daily cut-off | Value date applied per VPBank's stated rule; behaviour matches what is recorded in Appendix C |
| T16 | Overdraft and set-off — attempt an instruction exceeding the escrow balance | Rejected. No overdraft created, no set-off against any other balance |
| T17 | Closure with nil balance — close the test account | Final statement issued; account closed; balance nil |

T2, T4, T6 and T10 are the tests that must pass without qualification. A workaround or a "yes, but" on any of the four means the control is not in place, and Stage 3 does not begin.

### End-to-end test — Stage 3

The first live loan exercises all nine steps of Section 3.1 in order, with each step verified before the next begins: party onboarding and bank account opening, appraisal and listing, escrow provisioning, loan agreement execution, funding from every participating investor, disbursement to the SME, at least two repayment collections, at least two distribution cycles to all investors, and closure with nil balance. Distribution is verified to have reached each investor's originating account and no other.

---

## 3.7.3 Reconciliation validation method

Reconciliation is proved by **three-way agreement** over a defined period, for each escrow account:

1. **FundLok's ledger** — every posting recorded against the loan.
2. **VPBank's statement** — every line booked to the account.
3. **FundLok's instruction log** — every instruction issued and its recorded outcome.

The validation runs as follows, and is repeated daily from Stage 2 onward.

Every statement line must match exactly one ledger entry, and every ledger entry representing an external movement must match exactly one statement line. Every debit on the statement must trace to exactly one instruction in the instruction log with a matching outcome. Closing balance per VPBank must equal FundLok's computed balance for the account. The count of unmatched items on both sides must be zero at the close of the validation period.

Two properties make the result meaningful rather than circular. FundLok's ledger is append-only and cannot be edited, so a discrepancy is resolved by posting a correcting entry with a recorded reason — the ledger is never adjusted quietly to agree with the bank. And the instruction log is independent of both the ledger and the statement, so a debit that appears on the statement without a matching authorised instruction is detectable, which is the case that matters most.

**Break-detection test.** Validation is not accepted on clean data alone. FundLok injects a deliberate discrepancy into its own reconciliation input during Stage 2 — a modified amount and an omitted line — and the validation must flag both. A reconciliation process that has never failed has not been shown to work.

---

## 3.7.4 Sign-off criteria

Stage 3 does not begin until every item below is satisfied.

| # | Criterion | Evidence |
|---|---|---|
| 1 | Every item in Section 3.3 is marked confirmed, amended by agreement, or explicitly not available with a recorded consequence | Signed-off requirement list from Stage 0 |
| 2 | Control tests T2, T4, T6 and T10 have passed without qualification or workaround | Test results with statement extracts |
| 3 | All remaining Stage 2 tests have passed, or have a recorded, accepted deviation | Test results |
| 4 | Statement retrieval and parsing run without manual intervention | Reconciliation output for the test account |
| 5 | Three-way reconciliation returns zero unmatched items over at least five consecutive business days | Reconciliation reports |
| 6 | The break-detection test has flagged both injected discrepancies | Reconciliation exception log |
| 7 | Cut-off times, value dating and non-business-day behaviour are documented and match observed behaviour | Appendix C, completed |
| 8 | FundLok's authorised users are entitled with separated prepare and approve rights, and revocation has been demonstrated | Entitlement record and T14 result |
| 9 | Exception handling is defined with a named owner and a response time per exception type | FundLok operations procedure |
| 10 | Both parties have a named individual accountable for the pilot, with an agreed escalation path | Recorded in the partnership documentation |

**Signatories.** FundLok: Edward Wong, Chief Technology Officer, for the technical and reconciliation criteria; Loc, Chief Executive Officer, for commencement of live operation. VPBank: the equivalent custody-operations and technical owners, to be named.

Progression from Stage 4 to Stage 5 requires criterion 5 sustained over thirty consecutive days rather than five, with no unreconciled item older than one business day.

---

## 3.7.5 Items to be confirmed

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 1 | Whether VPBank can provide a test or non-production environment, or whether Stage 2 must run on a live account with nominal amounts | Determines whether Stage 2 carries any real exposure. FundLok's plan assumes a live account with nominal amounts, which works either way | VPBank, requested by Edward | Pending VPBank confirmation |
| 2 | Named technical and custody-operations contacts at VPBank for Stages 0 to 2 | Criterion 10 cannot be met without them | VPBank, requested by Edward | Pending VPBank confirmation |
| 3 | Whether VPBank wishes to witness or countersign the Stage 2 control test results | FundLok's preference is that VPBank countersigns T2, T4, T6 and T10, since these are the controls VPBank enforces | Edward, with VPBank | Pending VPBank confirmation |
| 4 | Elapsed duration to allow for Stages 0 to 2 | Depends on VPBank's internal change process, which FundLok cannot estimate | VPBank, requested by Edward | Pending VPBank confirmation |
| 5 | Repayment cadence | Determines how long Stage 3 takes, since the stage requires at least two collection and distribution cycles | Loc + Edward | 2026-08-07 |

---

*Dependencies: Section 3.3 (Phase 1 requirements). Consistent with Section 3.1 (process), Section 3.5 (FundLok's build) and Appendix C (SLA and cut-offs). Effort for the FundLok side of this work is in Section 3.6.*
