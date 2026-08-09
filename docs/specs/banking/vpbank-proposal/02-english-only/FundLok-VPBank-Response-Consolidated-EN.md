# FundLok — phản hồi đề xuất hợp tác VPBank
# FundLok — response to the VPBank collaboration proposal

**Bản tiếng Anh để rà soát nội bộ · English version for internal review**
**Ngày / Date: 5 August 2026 · Phần của Edward Wong / Edward Wong's assignments**

---

## Cách dùng tài liệu này · How to use this document

Tài liệu này chứa nội dung cho **mười mục** của đề xuất VPBank. Mỗi mục bắt đầu bằng một dải phân
cách nêu rõ mục đó dán vào đâu trong tài liệu gốc, thay cho dòng `[CONTENT — …]`.

This document holds the content for **ten sections** of the VPBank proposal. Each section begins with
a banner naming where it pastes in the original document, replacing the `[CONTENT — …]` line.

Ba mục có kèm sơ đồ — bốn sơ đồ tổng cộng — được cung cấp thành tệp riêng và cần chèn vào vị trí đã ghi trong mục đó:
Three sections carry diagrams — four in total — supplied as separate files and inserted at the point marked in the text:

- **1.4** — sơ đồ dòng tiền bốn giai đoạn / four-phase money flow
- **1.4** — sơ đồ phân luồng trách nhiệm vòng kín kèm cơ chế kiểm soát phí / closed-loop swim-lane with the fee control
- **1.5** — sơ đồ dòng dữ liệu ba vùng / three-zone data flow
- **3.1** — sơ đồ swim-lane chín bước / nine-step swim-lane

Các mục còn thiếu (Phụ lục C và E) đang chờ quyết định về phạm vi.
The remaining items (Appendices C and E) await a scope decision.

---


<!-- ══════════════════ PASTE INTO SECTION 1.4 ══════════════════ -->

> ## ▼ Mục 1.4 — Dòng tiền
> ## Section 1.4 — Money flow
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 1.4.
> Paste the block below in place of `[CONTENT — …]` at section 1.4.
> **Sơ đồ kèm theo / Diagram:** `section-1.4-moneyflow (four-phase money-flow diagram) · section-1.4-closedloop (closed-loop swim-lane with VPBank's fee control)`


# 1.4 Money flow

Money in this arrangement moves only between the parties' own bank accounts and the restricted escrow account held at VPBank. There is no point in the flow at which funds pass into an account that FundLok can spend from. FundLok issues the instruction for every movement described below and holds none of the money.

Eight movements make up the whole lifecycle, in four phases: the investors fund the escrow account, the escrow account disburses to the borrower, the borrower repays daily and those receipts are allocated, and the investor withdraws or reinvests. Each is set out individually in 1.4.2, and the two diagrams in 1.4.5 show all eight together.

Two properties of the design should be read before the detail, because everything else follows from them.

**The loop is closed.** Whatever an investor receives can be paid out only to the bank account that investor originally funded from. That account is recorded at the moment the investor's money arrives, and it becomes the only external destination available to them for the life of the loan. This is stated in full in 1.4.3.

**FundLok's fee is never an independent movement.** It travels inside an instruction that pays a beneficiary in the same breath, as a fixed proportion of that instruction, so VPBank can verify it on the face of the instruction without knowing anything about the loan. FundLok cannot draw on money that is sitting idle in the escrow account. This is set out in 1.4.4.

**Working case used for illustration.** A loan of VND 2.5 billion with eight participating investors and a disbursement fee of 1%. Investor scale is derived from FundLok's target investor profile — family offices deploying approximately USD 200,000 each across ten to fifteen borrowers — which implies roughly five to eight investors on a loan of this size. All figures are FundLok internal estimates dated 5 August 2026 and are illustrative of the mechanics, not a commitment on pricing.

---

## 1.4.1 The eight movements

| Ref | Movement | From | To | When | Currency |
|---|---|---|---|---|---|
| M1 | Principal | Each investor's own registered bank account | Project escrow account | Once, as each investor commits | VND |
| M2 | Principal less fee | Project escrow account | SME's verified account | Once, when the funding target is met | VND |
| M3 | Disbursement fee | Project escrow account | FundLok fee account | Same instruction as M2 | VND |
| M4 | Daily revenue share | SME | Project escrow account | Every business day | VND |
| M5 | Allocation | Project escrow account | Each investor's holding | Every business day | VND |
| M6 | Loan management fee | Project escrow account | FundLok fee account | Same instruction as M5 | VND |
| M7 | Withdrawal | Investor's holding | Investor's own registered bank account | On the investor's request | VND |
| M8 | Reinvestment | Investor's holding | A new project escrow account | On the investor's request | VND |

M3 and M6 are the only two movements that reach FundLok, and neither can be issued on its own.

---

## 1.4.2 Each movement in turn

### Phase 1 — Funding

**M1 — Principal into escrow.** Each investor transfers their committed amount from their own registered bank account into the project escrow account. VPBank credits the account and notifies FundLok; FundLok matches the credit to that investor's commitment and **records the originating account**. Recording it here is what makes the closed loop enforceable later. On the working case, eight investors contribute roughly VND 312.5 million each to reach VND 2.5 billion. A credit that cannot be matched to a commitment is held unallocated and raised as an exception rather than applied on assumption.

### Phase 2 — Disbursement

**M2 — Principal less fee to the SME.** Once the full committed principal has been received and the loan agreement is signed, FundLok issues a dual-authorised instruction and VPBank pays the SME's verified account. On the working case the SME receives VND 2.475 billion.

**M3 — Disbursement fee to FundLok.** In the same instruction, 1% of the gross principal goes to FundLok's fee account — VND 25 million on the working case. **This fee is funded by the SME**, whose repayment obligation is calculated on the gross VND 2.5 billion rather than the net amount received. The investors are therefore whole on their full capital; none of their principal has been used to pay FundLok. This is the point on which the fee's fairness turns, and it belongs in the loan agreement rather than being left to inference.

### Phase 3 — Daily collection and allocation

**M4 — Daily revenue share from the SME.** Repayment is not a fixed instalment schedule. Each business day FundLok reads the SME's previous day's revenue from its e-invoice data through a licensed T-VAN provider, computes the agreed percentage, and issues the SME a payment request through the FundLok platform and its notification channel. The SME pays that amount into the project escrow account, by VietQR or bank transfer, quoting the reference FundLok supplies.

Repayment therefore tracks the SME's actual trading. A slow week produces smaller receipts and a strong week larger ones, with the total obligation unchanged. This is the mechanism that makes the product suitable for revenue-variable small businesses, and it is why the flow is daily rather than monthly.

**M5 — Allocation to each investor.** Once a receipt has cleared, FundLok computes each investor's pro-rata share and issues a dual-authorised instruction; VPBank credits each investor's holding. Each investor's entitlement is tracked separately at all times; there is no pooling of one investor's position with another's.

**M6 — Loan management fee to FundLok.** In the same instruction as M5, FundLok's management fee is paid to its fee account as a fixed proportion of the amount being allocated. **This fee is funded by the investors** and is taken from return, never from principal.

Where a single allocation fails — an unreachable destination, for instance — the other allocations in that instruction still settle and the failed amount stays in the project escrow account for retry. It is never redirected, never applied to another investor and never applied to another loan.

### Phase 4 — Withdrawal or reinvestment

**M7 — Withdrawal.** The investor requests a transfer through the FundLok platform, and VPBank pays it to that investor's own registered bank account — the account they funded from in M1, and no other. This is the closed loop in operation.

**M8 — Reinvestment.** Alternatively the investor directs their available balance into a new loan, in which case the balance funds a new project escrow account and the cycle begins again at M1. A held balance is therefore a funding source in its own right, alongside an inbound transfer from the investor's bank account.

---

## 1.4.3 The closed-loop rule

**Money that has been received on an investor's behalf can leave the arrangement only to the bank account that investor originally funded from.**

The rule operates as follows. At M1, the originating bank account of each inbound payment is recorded against that investor. That account, and only that account, is registered as the permitted external destination for that investor. At M7, VPBank pays to the registered account; no other destination is available to that investor, and a request naming a different account is not executed. Changing the registered account is a controlled event requiring re-verification that the new account belongs to the same verified party, not a self-service change.

Two consequences are worth stating plainly. FundLok cannot direct an investor's money to a third party, because no third party is ever a permitted destination. And an investor cannot use the platform to move money to an account that has not been verified as theirs, which closes the most obvious route by which a marketplace of this kind could be misused.

The rule applies equally on the borrower side: the SME receives funds only at its own verified account, recorded and verified before disbursement.

---

## 1.4.4 How FundLok is paid without holding funds

There are two fees, and both are constrained the same way.

| | Disbursement fee | Loan management fee |
|---|---|---|
| Reference | M3 | M6 |
| Approximately | 1% of gross principal | To be confirmed — see 1.4.7 |
| Funded by | The SME | The investors |
| Taken from | Gross principal, with the SME's obligation calculated on the gross amount | Return, never principal |
| When | Inside the disbursement instruction (M2) | Inside each allocation instruction (M5) |
| Verifiable by VPBank as | A fixed proportion of the instruction it travels in | A fixed proportion of the instruction it travels in |

Four constraints apply to both, and together they are the mechanism that protects the beneficiaries while permitting FundLok to be paid:

1. **Never a standalone movement.** A fee line is only permitted inside an instruction that pays a beneficiary in the same instruction. An instruction consisting solely of a fee is not executed.
2. **Never from idle balance.** FundLok cannot draw on a balance sitting in the escrow account. If no beneficiary is being paid, no fee moves.
3. **Bank-verifiable proportion.** The fee is a fixed proportion of the instruction it sits in, so VPBank checks arithmetic on the face of the instruction rather than relying on FundLok's representation. A registered ceiling applies as a backstop.
4. **Suspended while an account is frozen.** Where an account is held under the dispute mechanism, FundLok's fee entitlement is suspended for the duration. FundLok does not continue drawing fees on a loan in dispute or default.

The effect is that FundLok cannot sweep an escrow account, cannot take anything unless a beneficiary is being paid in the same movement, and cannot touch investor capital.

---

## 1.4.5 Diagrams

The accompanying diagram shows all eight movements across the four phases, with a legend distinguishing principal, FundLok's fee, repayment and allocation, and withdrawal and reinvestment. It is sized to remain legible when printed at A4. The M-references on the diagram match the inventory in 1.4.1.

*[Insert: `section-1.4-moneyflow` — four-phase money-flow diagram with legend.]*

A second diagram sets out the same eight movements as a swim-lane, one lane for each of the four parties, and expands the control VPBank applies to every instruction that carries a FundLok fee line. It is the companion to 1.4.3 and 1.4.4: the first establishes that the loop is closed, the second that FundLok's fee is bounded on the face of the instruction rather than by FundLok's own undertaking. The four checks shown — permitted destination, pairing with a beneficiary line, proportion and registered ceiling, and suspension while an account is held — are the same four constraints listed in 1.4.4, expressed as steps VPBank performs.

*[Insert: `section-1.4-closedloop` — closed-loop swim-lane, with VPBank's control on fee-bearing instructions.]*

---

## 1.4.6 Availability and transfer are different things

Investors expect their returns to be available promptly, and the daily collection cycle means value accrues to them every business day. It is worth being precise about what that means operationally, because "available daily" and "transferred daily" are not the same requirement.

An investor's balance is **available** as soon as the day's allocation is posted — visible on the FundLok platform, and theirs. It is **transferred** to their own bank account when they ask for it, at M7. Daily availability therefore does not require a daily outbound payment to every investor's external bank, which would multiply transaction volume without improving the investor's position.

This distinction also determines where an un-withdrawn balance physically rests, which is the substance of the account-structure choice in Section 1.8 and is not settled in this section.

---

## 1.4.7 Volumes

Movement counts follow directly from the daily cycle. On the working case of eight investors per loan, each active loan generates ten movements per business day: one inbound receipt, eight allocations and one fee.

| Active loans | Movements per business day | Movements per month | Of which internal to VPBank |
|---|---|---|---|
| 10 | 100 | 2,200 | 1,980 |
| 30 | 300 | 6,600 | 5,940 |
| 60 | 600 | 13,200 | 11,880 |
| 120 | 1,200 | 26,400 | 23,760 |

Assumptions: eight investors per loan, 22 business days per month, one inbound receipt and one fee movement per loan per day. FundLok internal estimates dated 5 August 2026.

This table counts the **daily cycle only** — M4, M5 and M6. It therefore excludes investor funding (M1), disbursement (M2, M3) and withdrawals (M7), which are one-off or on-request. The totals in Sections 1.8.3, 3.4.4 and 3.6.5 include those as well, and are correspondingly higher.

The allocation column assumes Option B of Section 1.8, where each investor holds their own escrow account. Under Option A, M5 is a posting in FundLok's ledger and generates no bank movement, which removes the eight allocations per loan per day and leaves two.

Which of these settle **inside** VPBank and which cross to another bank depends on where each party banks, and no party is required to bank at VPBank (Section 1.8.3).

| Movement | Settles internally at VPBank if… | Otherwise |
|---|---|---|
| M1 investor funding | the investor banks at VPBank | interbank inbound |
| M2 disbursement · M3 fee | the SME banks at VPBank; M3 if FundLok's fee account is at VPBank | interbank outbound |
| M4 daily revenue share | the SME banks at VPBank | interbank inbound — **the largest external flow**, at roughly 1,320 a month at 60 active loans |
| M5 allocation · M6 fee | always internal under Option B; not a bank movement at all under Option A | — |
| M7 withdrawal | the investor banks at VPBank | interbank outbound |

On the assumption that neither party banks at VPBank, externally settled movements total roughly **1,568 a month at 60 active loans** — and that figure is the same under Option A and Option B, because everything Option B adds is internal. Two consequences follow. Internal book transfers cost VPBank very little, so Option B's higher movement count is largely an accounting artefact rather than a real expense. And if the SME banks at VPBank, M4's 1,320 monthly payments become internal, which is worth raising with VPBank as a benefit rather than leaving implicit.

---

## 1.4.8 Items to be confirmed

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 1 | The loan management fee rate, and whether it is a proportion of each allocation or of return | M6's proportion must be stated for VPBank to verify it on the instruction | Loc, with Edward | 2026-08-12 |
| 2 | The revenue-share percentage, and whether it varies by grade | Determines the size of M4 and therefore the whole daily cycle | Loc + Edward | 2026-08-12 |
| 3 | Where an un-withdrawn investor balance physically rests — an investor-level account at VPBank, or the project escrow account with the entitlement tracked in FundLok's ledger | Determines whether M5 is a bank transfer or a ledger posting, and changes monthly movement volumes by roughly a factor of ten | Loc + Edward (Section 1.8) | 2026-08-12 |
| 4 | Whether VPBank can execute internal allocation volumes of the order shown in 1.4.7, and how it prices them | Determines whether the daily allocation in M5 is feasible as designed | VPBank, requested by Edward | Pending VPBank confirmation |
| 5 | Treatment of an SME overpayment or a receipt exceeding the outstanding balance | Needs a defined destination; the closed-loop rule does not by itself say where a surplus goes | Edward | 2026-08-12 |
| 6 | Whether the registered external destination may be changed, and under what verification | 1.4.3 assumes a controlled re-verification rather than self-service | Edward, with VPBank | Pending VPBank confirmation |
| 7 | Ceiling values for the fee backstop in 1.4.4 constraint 3 | VPBank needs a registered maximum, not only a proportion | Loc, with Edward | 2026-08-12 |


<!-- ══════════════════ PASTE INTO SECTION 1.5 ══════════════════ -->

> ## ▼ Mục 1.5 — Dòng dữ liệu
> ## Section 1.5 — Data flow
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 1.5.
> Paste the block below in place of `[CONTENT — …]` at section 1.5.
> **Sơ đồ kèm theo / Diagram:** `section-1.5-dataflow (three-zone data-flow diagram)`


# 1.5 Data flow

**FundLok moves data and instructions, not money.** Funds move only between the parties' own accounts and the restricted escrow account held at VPBank; at no point does money pass through an account controlled by FundLok. What FundLok moves is information: the appraisal that produces a loan, the instruction that asks the bank to release funds to a permitted destination, and the reconciliation that proves the two records agree.

This section sets out every category of data that crosses the boundary between FundLok and VPBank, in which direction, and — equally important — what deliberately never crosses it. The governing principle is **minimum necessary**: VPBank receives what it needs to open an account, execute an instruction and report what it did, and nothing beyond that.

Three properties of the design follow from that principle and are visible in the inventory below.

First, **credit information never reaches VPBank.** VPBank makes no lending decision, so it has no need for a credit score, a grade, a rate tier or an SME's financial statements, and it receives none of them. This is what makes the statement "VPBank takes no credit risk" a structural fact about the data as well as a contractual one.

Second, **due diligence data does not route through FundLok.** Each party submits its account-opening documentation directly to VPBank for the bank's own customer due diligence. FundLok neither collects that set on VPBank's behalf nor transmits it, because the bank's assessment is the bank's own and is not built on FundLok's records.

Third, **instructions carry no more personal data than a named bank transfer requires** — an account number, a holder name, an amount and a reference.

---

## 1.5.1 The boundary

| Zone | Holds | Boundary behaviour |
|---|---|---|
| Parties — investor and SME | Their own identity, financial and settlement-account data | Submit platform data to FundLok; submit account-opening documents directly to VPBank |
| FundLok — arranger and servicer | Platform records, appraisal, ledger, instruction history, reconciliation state | Sends instructions and account-provisioning data to VPBank; receives confirmations and statements. Never holds funds |
| VPBank — custodian | The escrow account, its permitted destinations, and the record of what it executed | Receives instructions; returns outcomes, statements and balances. Holds no credit information |

---

## 1.5.2 Full inventory — data exchanged with VPBank

### FundLok → VPBank

| Ref | Exchange | Fields |
|---|---|---|
| F1 | Account provisioning request | Loan reference · requested account title · permitted-destination list, each entry carrying destination account number, account-holder name, bank identifier and destination type (verified borrower account, or registered investor originating account) · identity of the requesting authorised user |
| F1a | Permitted-destination amendment | Loan reference · escrow account number · entry to add or remove · authorising users · reason code |
| F2 | Payment instruction, per transfer | Escrow account number · destination account number and holder name · amount · currency (VND) · unique FundLok instruction reference · batch reference · requested value date · narrative to appear on the beneficiary's statement · identity of the two authorising users |
| F3 | Channel administration | Authorised user names and roles · entitlement level (prepare or approve) · additions, amendments and revocations |
| F4 | Account closure request | Loan reference · escrow account number · confirmation of nil balance · authorising users |

### VPBank → FundLok

| Ref | Exchange | Fields |
|---|---|---|
| B1 | Account provisioning confirmation | Escrow account number · account title as registered · status · opening date |
| B2 | Instruction outcome | Batch acknowledgement · per-transfer status · bank reference per executed transfer · rejection reason code and text where applicable · execution timestamp |
| B3 | Daily statement, per line | Bank transaction identifier (stable across retrievals) · booking date · value date · amount · direction, credit or debit · counterparty name · counterparty account · payment reference or narrative as received · running balance |
| B3a | Statement header | Escrow account number · statement period · opening and closing balance |
| B4 | Balance enquiry response | Escrow account number · balance · timestamp |
| B5 | Final statement on closure | Full transaction history for the account · nil closing balance · closure date |

### Parties → VPBank, directly

| Ref | Exchange | Fields |
|---|---|---|
| V0 | Account-opening documentation for the bank's own due diligence | As specified by VPBank — identity documents, enterprise registration, beneficial ownership and authorised signatories. **FundLok does not collect, hold or transmit this set on VPBank's behalf** |

### Parties ↔ FundLok — recorded for completeness, none of which crosses to VPBank

| Ref | Exchange | Fields |
|---|---|---|
| P1 | Identity and enterprise data | Identity verification result and supporting documents · enterprise registration and licence data · authorised representative identity |
| P2 | Financial and appraisal inputs | Financial statements · trading history · sector classification · personal guarantee terms |
| P3 | Settlement account and consent | Settlement account details, stored masked · consent record with timestamp, scope and withdrawal state |
| P4 | Returned to the parties | Loan terms and rate · daily amounts requested and collected · statements and holdings · settlement confirmations |
| P5 | Daily sales data, via a licensed T-VAN provider | Invoice-level sales records for the prior day, from which the daily revenue-share amount is computed. Sourced from the borrower's e-invoice data with the borrower's consent, not from VPBank |
| P6 | Daily payment request to the borrower | Amount due · reference to quote · issued through the FundLok platform and its notification channel |


---

## 1.5.3 What never crosses to VPBank

- Credit score, grade, rate tier, or any appraisal output or working.
- SME financial statements or supporting documentation.
- Personal guarantee terms or any enforcement detail.
- Investor portfolio holdings, allocation preferences or platform behaviour.
- Borrower sales and invoice data obtained through the T-VAN provider, and any personal data of the borrower's own customers contained in it.
- Identity documents and verification evidence held by FundLok for its own onboarding.
- Any personal data beyond the account number, holder name, amount and reference that a named transfer requires.

This list is a design constraint, not an aspiration. Its practical consequence is that a compromise of the FundLok–VPBank interface would expose transfer instructions and statements, not the personal and credit data of the platform's users.

---

## 1.5.4 Handling and lawful basis

Personal data crossing to VPBank is limited to what is necessary to perform the loan contract and the custodial arrangement. Consent is captured from each party at the point their settlement account is registered, is recorded with timestamp and scope, and can be withdrawn. Transport is encrypted, access is restricted to named authorised users with separated prepare and approve entitlements, and every exchange in the inventory above is logged on both sides. Retention, encryption standards, breach response and the treatment of any processing outside Vietnam are specified in Section 4.4.

---

## 1.5.5 Diagram

The accompanying diagram shows the three zones, every flow in 1.5.2 with its reference, and the panel of data that never crosses. The flow from the parties directly to VPBank is drawn dashed and routed around FundLok, to make visible that the bank's due diligence does not pass through the platform. The T-VAN sales feed (P5) and the daily payment request (P6) are FundLok-side flows that do not cross the VPBank boundary, so they appear in the inventory above and in the diagram's non-crossing panel rather than as boundary flows.

*[Insert: `section-1.5-dataflow` — three-zone data-flow diagram with flow references and the non-crossing set.]*

---

## 1.5.6 Items to be confirmed

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 1 | VPBank's required field set and format for F1, F2 and F3 | The inventory above is FundLok's proposal; VPBank's channel will impose its own schema | VPBank, requested by Edward | Pending VPBank confirmation |
| 2 | Maximum length of the payment reference preserved end to end, and whether the counterparty name is always returned on inbound credits | Determines whether inbound credits can be attributed automatically or fall to manual investigation. Same dependency as Section 3.3 items C3 and D2 | VPBank, requested by Edward | Pending VPBank confirmation |
| 3 | Whether VPBank requires any beneficiary information beyond the permitted-destination entries in F1 | If it does, the minimisation position in 1.5.3 needs restating and Section 4.4 needs to cover the additional set | VPBank, requested by Edward | Pending VPBank confirmation |
| 4 | Whether account-opening documentation (V0) is submitted in branch, through VPBank's own digital channel, or by a route FundLok needs to signpost | Affects the party experience at Step 1 of Section 3.1 but not the data boundary itself | VPBank, requested by Edward | Pending VPBank confirmation |
| 5 | Account structure selected in Section 1.8 | If individual per-party accounts are adopted, F1 and B1 apply per party rather than per loan; field sets are unchanged | Loc + Edward | 2026-08-12 |
| 6 | Whether invoice-level data received through the T-VAN provider contains personal data of the borrower's own customers, and if so what is retained | A new category of personal data that no section previously considered. Bears directly on Section 4.4 | Edward, with counsel | 2026-08-14 |
| 7 | The notification channel used for the daily payment request, and what data it carries | Determines whether a further processor sits in the flow and what Section 4.4 must cover | Edward | 2026-08-12 |


<!-- ══════════════════ PASTE INTO SECTION 1.8 ══════════════════ -->

> ## ▼ Mục 1.8 — Cấu trúc tài khoản
> ## Section 1.8 — Account structure — Option A and Option B
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 1.8.
> Paste the block below in place of `[CONTENT — …]` at section 1.8.

# 1.8 Account structure — Option A and Option B

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

### Which accounts must be at VPBank

**No participant has to move their existing banking to VPBank.** Only the escrow account itself must be there.

| Account | Option A — FBO | Option B — Escrow |
|---|---|---|
| Project escrow account | **Must be at VPBank** | **Must be at VPBank** |
| Investor's everyday settlement account | Any bank | Any bank |
| Investor's own escrow account | Not required | **Must be at VPBank** — opened once, reused across every loan |
| SME's account receiving disbursement | Any bank | Any bank |
| SME's account paying the daily revenue share | Any bank | Any bank |
| FundLok's fee account | Any bank; VPBank preferable | Any bank; VPBank preferable |

Under Option B each investor gains **one** additional account at VPBank. That is inherent to Option B rather than a preference: an investor's escrow account can only exist at the custodian, and that is precisely what places the balance in the investor's own name and outside FundLok's estate. Their everyday account — which is also the registered withdrawal destination — stays where it already is. The borrower needs no VPBank account under either option.

**This carries a technical requirement that is easy to miss.** Because destinations sit at other banks, the escrow account must be able to execute interbank transfers and the permitted-destination list must accept accounts held elsewhere. Some restricted and blocked-account products permit same-bank destinations only. The requirement is stated at Section 3.3 A2b and asked as the fourth part of the question at 3.3.2.

FundLok's fee account is best held at VPBank so that the fee movement settles internally and appears on the same statement being reconciled, but nothing in the structure requires it.

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


<!-- ══════════════════ PASTE INTO SECTION 3.1 ══════════════════ -->

> ## ▼ Mục 3.1 — Quy trình end-to-end
> ## Section 3.1 — End-to-end process
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.1.
> Paste the block below in place of `[CONTENT — …]` at section 3.1.
> **Sơ đồ kèm theo / Diagram:** `section-3.1-swimlane (nine-step swim-lane diagram)`


# 3.1 End-to-end process — nine steps from onboarding to loan closure

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


<!-- ══════════════════ PASTE INTO SECTION 3.3 ══════════════════ -->

> ## ▼ Mục 3.3 — VPBank cần xây — Giai đoạn 1
> ## Section 3.3 — What VPBank needs to build — Phase 1
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.3.
> Paste the block below in place of `[CONTENT — …]` at section 3.3.

# 3.3 What VPBank needs to build — Phase 1

This section states, component by component, what VPBank needs to have in place for the pilot to operate. It is deliberately bounded: **Phase 1 requires no API integration.** Every requirement below can be met with a secure batch instruction channel and a daily machine-readable statement, both of which are ordinary corporate banking capabilities. The API, real-time notification and automated reconciliation work is specified separately in Section 3.4 and is **not** required for the pilot.

FundLok is aware of VPBank's published Open API programme and is not asking for it in Phase 1. The intent is to start the partnership on capabilities VPBank very likely already operates, prove the flow with real money at low volume, and only then decide whether the volume justifies Phase 2.

Each item is marked **CONFIGURATION** — existing capability set up for FundLok's use — or **NEW BUILD** — something VPBank would need to develop. These markings are FundLok's assessment of what is typically available in Vietnamese corporate banking, not a claim about VPBank's systems; VPBank is asked to confirm or correct each one. Where the marking depends on the answer to the question in 3.3.2, that is stated.

Nothing in this section asks VPBank to take credit risk, to make or review any lending decision, or to place reliance on FundLok's own customer checks. Due diligence on account holders is VPBank's own throughout.

---

## 3.3.1 The volumes Phase 1 is sized for

All figures are FundLok internal estimates for the pilot, dated 5 August 2026, on the following assumptions: 5–10 loans funded per month; an average of eight participating investors per loan, derived from FundLok's target profile of family offices deploying approximately USD 200,000 each across ten to fifteen borrowers; an assumed average term of 12 months; and 22 business days per month.

Repayment is a **daily revenue share**, not a fixed instalment schedule: each business day FundLok computes the amount due from the borrower's prior-day sales and requests it, and the borrower pays into the escrow account (Section 1.4). The cycle is therefore daily from the first loan onward.

| Period | Active loans | Investor funding credits / month | Disbursement instructions / month | Daily repayment credits / month | Allocation movements / month | Fee movements / month |
|---|---|---|---|---|---|---|
| Month 1 | 5–10 | 40–80 | 5–10 | 110–220 | 880–1,760 | 110–220 |
| Month 3 | 15–30 | 40–80 | 5–10 | 330–660 | 2,640–5,280 | 330–660 |
| Month 6 | 30–60 | 40–80 | 5–10 | 660–1,320 | 5,280–10,560 | 660–1,320 |

Three things follow from these numbers, and they shape the whole of Phase 1.

First, **allocation is the only high-volume flow.** Everything else stays in the low hundreds for the entire pilot. And allocation only generates *bank movements at all* under Option B of Section 1.8, where each investor holds their own escrow account; under Option A it is a posting in FundLok's ledger and no bank movement occurs. The allocation column above is therefore the Option B case, and requirement D5 below exists only for that option.

Second, **which movements settle internally depends on where each party banks**, and no participant is required to bank at VPBank (Section 1.8.3). Assuming neither party does, externally settled traffic is investor funding, disbursement, investor withdrawals and — the largest of them — the borrower's daily payment, together roughly 1,568 per month at 60 active loans. That figure is the same whichever option Section 1.8 selects, because everything Option B adds is internal to VPBank. If a borrower banks at VPBank its daily payments become internal too.

Third, because FundLok composes each batch programmatically, **the number of lines in a batch costs VPBank little; the number of batches is what costs effort.** One daily allocation batch is one batch whether it carries 80 lines or 800.

That is why a secure batch channel is sufficient for Phase 1, and why the Phase 2 trigger in Section 3.4 is expressed in movements per month rather than in loans.

---

## 3.3.2 The question that determines the scope of everything below

**Can VPBank's existing blocked-account product be used as the restricted-purpose escrow account — and can it enforce a bank-side permitted-destination list?**

This is the pivotal question in this proposal. If the answer is yes to both, most of section A below is configuration and the pilot can start quickly. If the product exists but cannot restrict destinations, then the single most important control in the structure has to be built, and that changes both the timeline and the risk position.

FundLok asks VPBank to answer four parts specifically:

1. Does an existing blocked-account or escrow product exist that can hold funds for a restricted purpose, segregated from FundLok's own operating accounts?
2. Can that product be configured so that funds may only be released to a defined list of destination accounts, with the restriction enforced by the bank rather than by FundLok's instruction discipline?
3. Can that destination list be amended in a controlled way during the life of the account, since investors join a loan over time?
4. Can the escrow account execute **interbank** transfers to destinations at other banks, and does the destination list accept accounts held at other banks? No participant is required to bank at VPBank, so if the product is restricted to same-bank destinations the arrangement cannot operate.

---

## 3.3.3 A — Escrow account configuration

Assumes one restricted escrow account per loan. If Section 1.8 selects a different account structure, the account count changes but the requirements below do not.

| Ref | Requirement | Configuration or new build | Why it is required |
|---|---|---|---|
| A1 | A restricted-purpose account per loan, holding investor funds segregated from FundLok's own operating accounts and from other loans | CONFIGURATION if the existing blocked-account product qualifies · otherwise NEW BUILD — depends on 3.3.2 | Segregation per loan is the structural basis of the whole arrangement; no pooled balance means one loan can never fund another |
| A2 | A bank-enforced permitted-destination list, so funds may leave the account only to (a) the verified borrower account, (b) a registered investor originating account, or (c) FundLok's fee account — the last only as a proportion of an instruction that pays a beneficiary in the same movement | CONFIGURATION if supported by the existing product · otherwise NEW BUILD — depends on 3.3.2 | This is the control that makes FundLok's inability to draw on idle funds a fact enforced by the bank rather than a promise. Section 1.4.4 sets out the fee constraints |
| A2a | Capacity for at least **12 destination entries per project account**, and at least 700 entries live across the portfolio at pilot volume | CONFIGURATION, or NEW BUILD if the product caps destinations | On the working case of eight investors, a project needs eight investor destinations plus the borrower, FundLok's fee account and headroom. A product capping destinations at a low number would break the model silently |
| A2b | The permitted-destination list must accept **accounts held at other banks**, and the escrow account must be able to execute interbank transfers to them | CONFIGURATION, or NEW BUILD if the existing product permits only same-bank transfers | Investors and borrowers keep their existing banks (Section 1.8.3). Some restricted and blocked-account products permit transfers only to accounts at the same bank. If VPBank's does, the model does not work at all — which is why this is asked alongside 3.3.2 rather than left to be discovered during integration |
| A3 | Controlled amendment of the destination list during the account's life, with each amendment authorised and logged | CONFIGURATION | Investors commit to a loan over days or weeks, so the list of valid return destinations grows before funding closes |
| A4 | Account titling that reflects the restricted, segregated nature of the account | CONFIGURATION | Makes the arrangement legible on statements and in any audit or dispute |
| A5 | Account opening for a batch of loans, and closure of a zero-balance account at loan closure | CONFIGURATION — process rather than system at pilot volume | At 5–10 project accounts per month, plus roughly 1–10 investor accounts per month under Option B, opening can be an operational process. Automation is not needed until new accounts exceed about 25 per month (Section 3.4, P6) |
| A6 | No overdraft, no credit line and no set-off against the escrow account | CONFIGURATION | The funds are not FundLok's, so they must not be available to secure or offset any obligation |

---

## 3.3.4 B — Instruction channel and dual control

| Ref | Requirement | Configuration or new build | Why it is required |
|---|---|---|---|
| B1 | A secure channel through which FundLok submits a batch of payment instructions against a named escrow account | CONFIGURATION — existing corporate banking channel is sufficient | Carries disbursement (Step 6) and distribution (Step 8). No API needed at pilot volume |
| B2 | Two-person authorisation on every instruction, with the two roles held by different named individuals at FundLok | CONFIGURATION — standard corporate banking entitlement | Ensures no single person at FundLok can cause money to move. This is a control VPBank enforces, not one FundLok self-certifies |
| B3 | Acknowledgement of receipt of each batch, and a per-transfer outcome for every line in it | CONFIGURATION | A batch of 200 transfers where three fail must be distinguishable from one where all succeed; FundLok must know which three |
| B4 | Rejection reasons at line level, in a consistent coded form | CONFIGURATION | Determines whether FundLok retries, corrects the destination, or escalates |
| B5 | Duplicate-instruction protection — a batch or line resubmitted with the same FundLok reference must not produce a second payment | NEW BUILD if the channel does not already enforce uniqueness on a client reference | The one failure mode with no clean remedy. A duplicated distribution sends investor funds twice and cannot be recalled unilaterally |
| B6 | Failed transfers leave the funds in the escrow account | CONFIGURATION | A failed return must stay ring-fenced for retry, never be redirected or applied elsewhere |

---

## 3.3.5 C — Statement feed

| Ref | Requirement | Configuration or new build | Why it is required |
|---|---|---|---|
| C1 | A daily statement per escrow account in a machine-readable format, retrievable without manual intervention | CONFIGURATION | The basis of FundLok's daily reconciliation. Without it, reconciliation is manual and errors surface late |
| C2 | A stable, unique transaction identifier on every statement line, unchanged across retrievals | CONFIGURATION, or NEW BUILD if identifiers are not stable | FundLok must be able to recognise the same transaction on two different days without double-counting it |
| C3 | Remitter name, remitter account and the full payment reference preserved on every inbound credit | CONFIGURATION, or NEW BUILD if reference text is truncated | This is how an incoming payment is attributed to the right investor and the right loan. If the reference is truncated or the remitter dropped, attribution fails and the money sits unallocated |
| C4 | Balance per escrow account, available at least daily | CONFIGURATION | Checked before every disbursement instruction and reconciled against FundLok's ledger |
| C5 | Statement retrieval covering a requested date range, not only the latest day | CONFIGURATION | Needed to re-reconcile a period after any correction, and to produce evidence in a dispute |

Item C3 deserves emphasis. Of everything in this section, a truncated payment reference or a missing remitter is the requirement whose absence would cause the most day-to-day operational pain, because every unattributable credit becomes a manual investigation while an investor waits for confirmation.

---

## 3.3.6 D — VietQR collection

| Ref | Requirement | Configuration or new build | Why it is required |
|---|---|---|---|
| D1 | VietQR collection into a specified escrow account | CONFIGURATION | The practical way for an SME to repay, and for investors to fund, without manual transfer entry |
| D2 | A FundLok-supplied reference carried through the VietQR payment and preserved intact on the statement line | CONFIGURATION, or NEW BUILD if the reference field is not passed through | Without it, a VietQR receipt cannot be attributed to a loan and instalment, which defeats the purpose of using VietQR at all |
| D3 | Per-payer virtual account numbers underneath an escrow account, so each investor and each borrower pays to a distinct number | NEW BUILD — highly desirable, not essential for Phase 1 | Makes attribution deterministic and removes reference-matching failure entirely. FundLok's assessment is that this is the single highest-value capability in the whole integration, and it would reduce operational load on both sides |
| D4 | Real-time notification of an inbound credit | NOT REQUIRED IN PHASE 1 — see Section 3.4 | At pilot volume, retrieving the daily statement is sufficient. The cost is latency between an investor paying and seeing their commitment confirmed |
| D5 | Capacity to execute a **daily internal allocation batch** across investor accounts held at VPBank — of the order of 2,200 movements per month at 10 active loans, rising to 13,200 at 60 | CONFIGURATION if the batch channel has no practical line limit · otherwise NEW BUILD | Required only if Option B of Section 1.8 is adopted, where each investor holds their own escrow account. Under Option A the allocation is a ledger posting and no bank movement occurs |

---

## 3.3.7 E — Access, security and control

| Ref | Requirement | Configuration or new build | Why it is required |
|---|---|---|---|
| E1 | Named authorised FundLok users with separated entitlements, so the preparer and the approver cannot be the same person | CONFIGURATION | Makes B2's dual control real rather than procedural |
| E2 | Prompt revocation of a user's entitlement when FundLok notifies a personnel change | CONFIGURATION | A departing employee must lose the ability to authorise a transfer the same day |
| E3 | Bank-side audit trail of every instruction received, authorised, executed or rejected | CONFIGURATION | Provides the independent record against which FundLok's own audit trail is reconciled, and the evidence set in any dispute |
| E4 | Encrypted transport for the instruction channel and statement retrieval | CONFIGURATION | Personal and financial data in transit, per Section 4.4 |
| E5 | VPBank's own customer due diligence on the account holders, to VPBank's own standards | CONFIGURATION — VPBank's existing process | FundLok's checks serve FundLok's purposes and are not offered as a substitute for the bank's |

---

## 3.3.8 Summary

| Marking | Count | Items |
|---|---|---|
| CONFIGURATION | 18 | A3, A4, A5, A6, B1, B2, B3, B4, B6, C1, C4, C5, D1, E1, E2, E3, E4, E5 — of which A5 is process rather than system |
| CONFIGURATION or NEW BUILD, depending on existing capacity | 3 | A2a (destination-list size), A2b (interbank destinations), D5 (daily internal allocation capacity — Option B only) |
| CONFIGURATION or NEW BUILD, depending on the answer to 3.3.2 | 2 | A1, A2 |
| CONFIGURATION or NEW BUILD, depending on existing capability | 3 | C2, C3, D2 |
| NEW BUILD | 2 | B5 (duplicate protection), D3 (per-payer virtual accounts — desirable, not essential) |
| Not required in Phase 1 | 1 | D4 (real-time notification) |

Total: 29 requirements.

The shape of the ask: **the great majority of Phase 1 is configuration of capabilities a corporate bank already operates.** The two items that could turn into meaningful build work are the permitted-destination list (A2) and duplicate-instruction protection (B5), and both are controls that protect VPBank as much as FundLok.

---

## 3.3.9 What FundLok is not asking for in Phase 1

Stated explicitly so the boundary of the request is unambiguous:

- No API integration of any kind.
- No real-time or push notification of inbound credits.
- No automated reconciliation on VPBank's side — FundLok reconciles, against VPBank's statement.
- No individual accounts per investor or borrower, unless Section 1.8 selects that structure.
- No credit assessment, appraisal, scoring or lending decision.
- No debt collection, guarantee enforcement or legal action against a borrower.
- No dispute arbitration.
- No contribution to FundLok's own build or running costs.

---

## 3.3.10 Items to be confirmed

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 1 | Whether VPBank can execute daily internal allocation at the volumes in 3.3.1, and how it prices them | Determines whether requirement D5 is achievable, and therefore whether Option B of Section 1.8 is available | VPBank, requested by Edward | Pending VPBank confirmation |
| 2 | Answer to the three-part question in 3.3.2 | Determines whether A1 and A2 are configuration or new build, and therefore the Phase 1 timeline | VPBank, requested by Edward | Pending VPBank confirmation |
| 3 | Whether the existing corporate banking channel supports uniqueness on a client-supplied reference | Determines whether B5 is configuration or new build | VPBank, requested by Edward | Pending VPBank confirmation |
| 4 | Statement format, transaction identifier stability, and the maximum length of the preserved payment reference | Determines whether C2, C3 and D2 are configuration or new build | VPBank, requested by Edward | Pending VPBank confirmation |
| 5 | Whether per-payer virtual accounts (D3) are feasible, and in which phase | FundLok's assessment is that this is the highest-value capability available; worth knowing early even if deferred | VPBank, requested by Edward | Pending VPBank confirmation |
| 6 | Account structure selected in Section 1.8 | Determines whether requirement D5 applies at all, and the number of accounts to open | Loc + Edward | 2026-08-12 |
| 7 | Maximum number of destination entries per account (requirement A2a) | On eight investors a project needs twelve entries; a product capping at five would break the model silently | VPBank, requested by Edward | Pending VPBank confirmation |
| 8 | Cut-off times, value dating and non-business-day handling for the instruction channel | Determines what FundLok can commit to investors and borrowers on timing | VPBank, requested by Edward — recorded in Appendix C | Pending VPBank confirmation |


<!-- ══════════════════ PASTE INTO SECTION 3.4 ══════════════════ -->

> ## ▼ Mục 3.4 — VPBank cần xây — Giai đoạn 2
> ## Section 3.4 — What VPBank needs to build — Phase 2
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.4.
> Paste the block below in place of `[CONTENT — …]` at section 3.4.

# 3.4 What VPBank needs to build — Phase 2

## 3.4.1 Status: deferred, and not required for the pilot

**Nothing in this section is required for the pilot to operate.** The pilot runs entirely on the Phase 1 capabilities in Section 3.3 — a secure batch instruction channel, dual authorisation and a daily machine-readable statement. Phase 2 is recorded here so that both parties can see where the arrangement leads if the pilot succeeds, and so that neither is surprised later. It is not a request, and it carries no date.

Phase 2 is activated by **volume**, not by a calendar. The trigger is stated as a number in 3.4.3, and 3.4.4 sets out the arithmetic showing why Phase 1 remains workable well beyond the pilot.

One point of context worth stating plainly: **Phase 2 largely overlaps capability VPBank is already committed to building.** Circular 64/2024/TT-NHNN, which took effect on 1 March 2025, requires implementation of open API standards in the banking sector by **1 March 2027** (source: State Bank of Vietnam, Circular 64/2024/TT-NHNN). FundLok's Phase 2 requirements are conventional open-banking capabilities — token-based API authorisation, payment initiation, balance and statement query, and event notification — so in most cases Phase 2 asks FundLok to consume something VPBank will have built regardless, rather than asking for bespoke development.

---

## 3.4.2 Components

| Ref | Component | What it replaces from Phase 1 | What it delivers |
|---|---|---|---|
| P1 | Payment instruction API — submit an instruction and receive a per-transfer outcome | The batch file channel (3.3 B1) | Removes the manual batch cycle. Instructions become same-day and per-event rather than per-batch |
| P2 | Instruction status query by FundLok's own reference | Line-level outcomes on a returned batch file (3.3 B3) | Lets FundLok resolve a timed-out instruction without risking a duplicate payment |
| P3 | Idempotency on a client-supplied key, enforced by the API | Reference-uniqueness on the file channel (3.3 B5) | Makes duplicate protection a property of the interface rather than of operational discipline |
| P4 | Real-time notification of inbound credits | Daily statement retrieval (3.3 C1) | Removes up to 24 hours of latency between a party paying and FundLok confirming it. This is the component that most improves the experience for investors and borrowers |
| P5 | Balance and statement query on demand | The daily statement file (3.3 C1, C4) | Allows reconciliation to run continuously rather than once a day, so a break is detected in minutes |
| P6 | Automated escrow account opening and closure | The operational account-opening process (3.3 A5) | Needed once new accounts per month exceed what an operational process absorbs comfortably |
| P7 | Per-payer virtual account numbers at scale | Payment-reference matching (3.3 D2, D3) | Makes inbound attribution deterministic and removes reference-matching failure as a class of exception |
| P8 | Token-based API authorisation with refresh, and consent records where an end user's own account is accessed | Named-user entitlements on the banking channel (3.3 E1) | The access-control layer any API integration requires |
| P9 | Individual accounts per investor and per borrower | The per-loan escrow account structure | **Only if Section 1.8 selects Option A at launch and migrates to Option B later.** If Option B is adopted from the start, this is Phase 1 work rather than Phase 2 |
| P10 | Bulk internal allocation at scale, with per-line outcome | The daily allocation batch on the ordinary channel (3.3 D5) | Under Option B the daily allocation is the highest-volume flow in the arrangement — of the order of 10,600 movements a month at 60 active loans. This is the component that most reduces processing load on VPBank's own side |

P1 through P5 are the substance of Phase 2. P6 and P8 are supporting. P7 is the highest-value single item and is also offered as an optional Phase 1 capability in Section 3.3 (D3), because if VPBank can provide it early it removes work on both sides. P9 depends entirely on Section 1.8 and is flagged rather than requested.

---

## 3.4.3 Activation trigger

**Phase 2 is activated when total monthly payment events across all escrow accounts exceed 1,000 for two consecutive months.**

Under Option B of Section 1.8 this threshold is passed almost immediately, because daily allocation alone generates 880–1,760 movements in the first month. Where Option B is adopted, the trigger above should be read as applying to the *externally settled* movements — investor funding, disbursement and withdrawals — with the internal allocation volume handled instead by requirement D5 of Section 3.3 and component P10 above. Under Option A the threshold applies as written.

A payment event is one inbound credit or one outbound transfer. It is chosen as the unit because it is the thing that actually generates work — a batch of 200 transfers costs the same to authorise as a batch of 20, but 200 transfers carry ten times the exception load.

Component-level thresholds, for cases where one capability becomes worthwhile before the headline trigger is reached:

| Ref | Component | Activate when |
|---|---|---|
| P7 | Per-payer virtual accounts | Unattributable inbound credits exceed 30 per month for two consecutive months |
| P4 | Real-time credit notification | Inbound credits exceed 500 per month, or investor confirmation latency becomes a substantiated complaint theme |
| P1, P2, P3 | Instruction API and idempotency | Instruction batches exceed 20 per month — that is, more frequent than weekly |
| P6 | Automated account opening | New escrow accounts exceed 25 per month |
| P5 | On-demand balance and statement | Concurrently active escrow accounts exceed 100 |
| P9 | Individual per-user accounts | Only on selection of that structure in Section 1.8, with its own volume trigger stated there |

The Section 1.8 migration trigger should be set consistently with this table rather than independently.

---

## 3.4.4 Why this is deferred rather than scheduled

FundLok has modelled the manual effort Phase 1 requires, so that the claim "Phase 1 is sufficient" can be checked rather than asserted.

**Assumptions.** All figures are FundLok internal estimates dated 5 August 2026: 5–10 loans funded per month; an average of eight participating investors per loan, derived from FundLok's family-office investor profile; assumed average term of 12 months; 22 business days per month; daily revenue-share collection. Exception rates are split by settlement type — **3% for externally settled movements** (interbank transfers to accounts supplied by a third party) and **0.2% for movements internal to VPBank** between accounts VPBank itself opened and FundLok pre-registered, which fail far less often. Twenty minutes to review and dual-authorise one instruction batch, 15 minutes per account opening, 10 minutes per account closure, 12 minutes per exception, and 5 minutes per business day reviewing the automated reconciliation summary. One full-time equivalent is 160 working hours per month.

| Period | Movements / month, Option A | Movements / month, Option B | Manual touchpoints / month | Staff-hours / month | Full-time equivalent |
|---|---|---|---|---|---|
| Month 1 | 168–336 | 1,158–2,316 | 62–78 | 14.1–17.6 | 0.09–0.11 |
| Month 3 | 414–829 | 3,384–6,769 | 69–101 | 15.6–22.2 | 0.10–0.14 |
| Month 6 | 784–1,568 | 6,724–13,448 | 81–135 | 17.8–29.0 | 0.11–0.18 |
| Month 12 | 1,523–3,046 | 13,403–26,806 | 108–213 | 23.1–44.3 | 0.14–0.28 |

Touchpoint, staff-hour and FTE ranges span both options — the lower bound is Option A at 5 loans a month, the upper Option B at 10.

The conclusion is that Phase 1 does not fail at the trigger point — it degrades gradually. Even at month 12 under Option B, manual effort is roughly 28–44 staff-hours per month, which is a quarter of one full-time role. **Phase 2 is therefore justified by latency and by risk reduction, not by headcount**, until volumes well above the pilot. On this model FundLok would not need a full additional person until externally settled movements reached roughly 24,000 per month — an order of magnitude beyond the pilot.

Two risks do grow faster than the effort figures suggest, and they are the real reason Phase 2 exists. First, the 24-hour confirmation latency inherent in daily statement retrieval becomes a product problem before it becomes a staffing problem, because an investor who has sent money and cannot see it credited will contact support. Second, exception volume grows linearly with events while the consequence of a *missed* exception does not — one unattributed credit sitting in an escrow account is a minor annoyance, and thirty of them is a reconciliation control failure.

---

## 3.4.5 Sensitivity to the account structure

The account structure is not yet settled (Section 1.8). It has a direct and material effect on when Phase 2 activates.

| Cadence | 1,000 events / month reached, low case | 1,000 events / month reached, high case |
|---|---|---|
| Option A — allocation is a ledger posting | Month 9 | Month 4 |
| Option B — allocation is a daily bank movement | Month 1 | Month 1 |

The account structure, not the collection cadence, is what moves this. Daily collection alone adds only the borrower's own payment — one movement per loan per business day. It is daily *allocation* under Option B that multiplies volume, because each receipt fans out across every investor on the loan. FundLok's recommendation is therefore to settle Section 1.8 before the pilot begins, and to confirm requirement D5 with VPBank at the same time.

---

## 3.4.6 Items to be confirmed

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 1 | Account structure selected in Section 1.8 | Determines when the activation trigger is reached, per 3.4.5. The single largest variable in this section | Loc + Edward | 2026-08-12 |
| 2 | Account structure selected in Section 1.8, and its own migration trigger | Determines whether P9 is in scope at all, and the trigger must be set consistently with 3.4.3 | Loc + Edward | 2026-08-07 |
| 3 | Which Phase 2 components VPBank expects to have available under its Circular 64 implementation by 1 March 2027, and which would be additional to it | Determines how much of Phase 2 is genuinely incremental work for VPBank rather than consumption of committed capability | VPBank, requested by Edward | Pending VPBank confirmation |
| 4 | Whether VPBank prefers to bring P7 forward into Phase 1 as capability 3.3 D3 | Would remove a class of exception from the pilot itself and reduce operational load on both sides | VPBank, requested by Edward | Pending VPBank confirmation |
| 5 | Review point for the trigger — whether the 1,000-event threshold is reviewed jointly at a fixed interval | Avoids a dispute later about whether the trigger has been met | Edward, with VPBank | Pending VPBank confirmation |


<!-- ══════════════════ PASTE INTO SECTION 3.5 ══════════════════ -->

> ## ▼ Mục 3.5 — FundLok xây & chi trả
> ## Section 3.5 — What FundLok builds and pays for
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.5.
> Paste the block below in place of `[CONTENT — …]` at section 3.5.

# 3.5 What FundLok builds — and pays for

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
| 1 | Whether the operations dashboards (component 7) are required for the pilot or can follow it | At pilot volume, exception handling could be run from existing administrative screens, which would remove one component from the pilot scope | Edward | 2026-08-07 |
| 2 | Whether exposure and reporting (component 8) is in pilot scope or deferred | Depends on the reporting VPBank expects to receive during the pilot | Edward, with VPBank | Pending VPBank confirmation |
| 3 | Hosting region for personal data, and the position on in-country processing | Stated in Section 4.4; affects the infrastructure line of this section. Current deployment is in a regional cloud location outside Vietnam, so an in-country commitment is a migration rather than a description of today | Edward | 2026-08-07 |


<!-- ══════════════════ PASTE INTO SECTION 3.6 ══════════════════ -->

> ## ▼ Mục 3.6 — Ước lượng khối lượng & chi phí
> ## Section 3.6 — Effort and cost estimate
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.6.
> Paste the block below in place of `[CONTENT — …]` at section 3.6.

# 3.6 Effort and cost estimate

This section estimates the engineering effort behind Sections 3.3, 3.4 and 3.5, states what FundLok absorbs, and sets out the ongoing operational load the arrangement creates once live.

**On the VPBank estimates.** The man-day figures for VPBank's components are FundLok's indicative estimates, provided so that both parties can size the conversation and sequence the work. They are not a statement about VPBank's internal costs, resources or rates, and **no monetary value is placed on VPBank's effort** — VPBank prices its own build. Where a component's effort depends on whether an existing product can be configured or something must be built, both figures are given: the lower is the configuration path, the higher the build path.

**On the FundLok estimates.** These reflect FundLok's own observed delivery velocity with a team of two engineers — Edward Wong and Phat — both working with AI-assisted development. A reviewer benchmarking these figures against conventional day rates should note that assumption explicitly: the numbers describe how quickly this team ships, evidenced by the double-entry ledger and the appraisal engine both being specified, built, tested and merged within the last two months. They are not a claim that the work is small.

All figures are FundLok internal estimates dated 4 August 2026. One man-day is one engineer for one working day.

---

## 3.6.1 VPBank — Phase 1

| Ref | Component | Man-days, configuration path | Man-days, build path | FundLok absorbs or co-funds |
|---|---|---|---|---|
| A1 | Restricted-purpose account per loan | 2 | 15 | No — bank product |
| A2 | Bank-enforced permitted-destination list | 3 | 20 | **Co-fund — see 3.6.4** |
| A2a | Destination-list capacity — 12 entries per account, 700 across the portfolio | 1 | 8 | No |
| A3 | Controlled amendment of the destination list | 1 | 3 | No |
| A4 | Account titling | 0.5 | 0.5 | No |
| A5 | Batch account opening and closure process | 2 | 2 | No — process design |
| A6 | No overdraft, credit line or set-off | 0.5 | 0.5 | No |
| B1 | Secure batch instruction channel | 1 | 1 | No — existing channel |
| B2 | Two-person authorisation | 1 | 1 | No — existing entitlement |
| B3 | Batch acknowledgement and per-line outcome | 1 | 3 | No |
| B4 | Line-level rejection reason codes | 1 | 2 | No |
| B5 | Duplicate-instruction protection | 4 | 10 | **Co-fund — see 3.6.4** |
| B6 | Failed transfers remain in escrow | 0.5 | 0.5 | No |
| C1 | Daily machine-readable statement | 1 | 3 | No |
| C2 | Stable transaction identifier | 1 | 5 | No |
| C3 | Remitter and full reference preserved | 1 | 6 | No |
| C4 | Daily balance availability | 0.5 | 0.5 | No |
| C5 | Date-range statement retrieval | 1 | 2 | No |
| D1 | VietQR collection into the escrow account | 1 | 3 | No |
| D2 | Reference pass-through on VietQR | 1 | 6 | No |
| D3 | Per-payer virtual accounts — optional in Phase 1 | 15 | 25 | **Co-fund — see 3.6.4** |
| D4 | Real-time credit notification | Deferred to Phase 2 | Deferred to Phase 2 | Not applicable |
| D5 | Daily internal allocation capacity — Option B only | 2 | 18 | **Co-fund — see 3.6.4** |
| E1 | Named users, separated entitlements | 1 | 1 | No — existing entitlement |
| E2 | Entitlement revocation | 0.5 | 0.5 | No |
| E3 | Bank-side audit trail | 0.5 | 0.5 | No |
| E4 | Encrypted transport | 0.5 | 0.5 | No |
| E5 | VPBank's own customer due diligence | Existing process | Existing process | No |

**Phase 1 totals.** Excluding the optional per-payer virtual accounts: **29.5 man-days on the configuration path, 112.5 on the build path.** Including them: 44.5 and 137.5.

D5 applies only if Option B of Section 1.8 is adopted. Under Option A the figures are 27.5 and 94.5 excluding virtual accounts.

The spread between the two paths is almost entirely accounted for by two items. A1 and A2 together are 5 man-days if VPBank's existing blocked-account product can be configured, and 35 if it cannot — a 30 man-day swing that rests on the single question in Section 3.3.2. **Answering that question is worth more to the planning of this partnership than any other item in this proposal.**

---

## 3.6.2 VPBank — Phase 2 (deferred)

Recorded for completeness. Not required for the pilot, and activated only by the volume trigger in Section 3.4.

| Ref | Component | Man-days, low | Man-days, high | Note |
|---|---|---|---|---|
| P1 | Payment instruction API | 15 | 25 | Likely within VPBank's Circular 64 implementation |
| P2 | Instruction status query | 5 | 10 | Likely within that implementation |
| P3 | API-enforced idempotency | 4 | 8 | Reduced if B5 was built in Phase 1 |
| P4 | Real-time inbound credit notification | 10 | 18 | The component that most improves party experience |
| P5 | On-demand balance and statement query | 6 | 12 | Likely within that implementation |
| P6 | Automated account opening and closure | 8 | 15 | — |
| P7 | Per-payer virtual accounts at scale | 15 | 25 | Zero additional if delivered as D3 in Phase 1 |
| P8 | Token-based API authorisation and consent | 6 | 12 | Likely within that implementation |
| P9 | Individual accounts per party | 12 | 22 | Only if Option A launches and migrates to Option B later |
| P10 | Bulk internal allocation at scale | 12 | 20 | Only under Option B; reduces VPBank's own processing load |

**Phase 2 totals.** Excluding P9 and P10: **69 to 125 man-days.** Including both: **93 to 167.**

A material share of P1, P2, P5 and P8 is conventional open-banking capability that VPBank is required to implement by 1 March 2027 under Circular 64/2024/TT-NHNN. To the extent that work is already planned, FundLok's Phase 2 requirement is consumption of committed capability rather than incremental build. Item 3 of Section 3.4.6 asks VPBank to confirm which components fall on which side of that line.

---

## 3.6.3 FundLok — its own build

| Ref | Component | Man-days, low | Man-days, high |
|---|---|---|---|
| N1 | Payment instruction engine with dual control | 6 | 9 |
| N2 | Escrow provisioning and lifecycle | 4 | 6 |
| N3 | Bank settlement records and automated reconciliation | 8 | 12 |
| N4 | Collection matching | 6 | 10 |
| N5 | Distribution engine | 5 | 8 |
| N6 | Settlement account registration and verification | 3 | 5 |
| N7 | Operations and reconciliation dashboards | 5 | 8 |
| N8 | Exposure and reporting module | 4 | 6 |
| N9 | Data protection controls | 4 | 6 |
| N10 | T-VAN integration — daily pull of invoice-level sales data | 7 | 12 |
| N11 | Daily revenue-share engine — computes the amount due, issues the request, tracks the obligation | 6 | 10 |
| N12 | Integration and testing, FundLok side (Section 3.7) | 6 | 9 |

**FundLok total: 64 to 101 man-days.** Across two engineers this is approximately six to ten working weeks. The increase over an earlier estimate reflects two components added once the repayment mechanism was confirmed as a daily revenue share rather than an instalment schedule: N10 and N11 together are 13 to 22 man-days, and N10 is a dependency of the money flow itself — without the sales feed there is no figure to collect against. Neither is started; nothing relating to the T-VAN integration appears in FundLok's repository as at 5 August 2026. It excludes the eight components already built and operating, listed in Section 3.5.1, whose cost FundLok has already borne.

---

## 3.6.4 What FundLok absorbs or co-funds

FundLok bears **the entire cost of everything in 3.6.3** — build, testing, hosting, third-party verification fees, and ongoing operation. No part of it is charged to VPBank or shared with it.

For VPBank's own build, FundLok's position is as follows.

FundLok does not expect VPBank to absorb the cost of capability that exists principally for FundLok's benefit. For that reason FundLok **offers to co-fund three specific items**, on terms to be agreed:

- **A2, the permitted-destination list.** This is the control that makes the whole structure sound, and it is the item most likely to require real build work. FundLok would rather contribute to it than see it descoped.
- **B5, duplicate-instruction protection.** The one failure mode with no clean remedy. FundLok considers it non-negotiable and is willing to pay toward it.
- **D3 or P7, per-payer virtual accounts.** Optional, but it removes a whole class of operational exception from both sides. FundLok would co-fund bringing it forward into Phase 1.
- **D5, daily internal allocation capacity.** Required only under Option B of Section 1.8, and it exists purely to serve FundLok's allocation model. FundLok would not ask VPBank to absorb it.

Everything else in 3.6.1 is either existing capability being configured or ordinary custody-product functionality, and FundLok makes no offer against it. FundLok does not propose to co-fund any part of Phase 2 that falls within VPBank's Circular 64 implementation.

Co-funding is offered as a contribution to development effort. The form, amount and mechanism are commercial matters for negotiation and are not proposed here.

---

## 3.6.5 Ongoing run cost

Run cost is expressed as FundLok's manual touchpoints per month and the staff-hours they consume, concluding with an incremental headcount figure — the operational cost of running the arrangement, not a monetary estimate.

**Assumptions.** All figures are FundLok internal estimates dated 5 August 2026: 5–10 loans funded per month; an average of eight participating investors per loan, derived from FundLok's family-office investor profile; assumed average term of 12 months; 22 business days per month; daily revenue-share collection. Exception rates are split by settlement type — **3% for externally settled movements** (interbank transfers to accounts supplied by a third party) and **0.2% for movements internal to VPBank** between accounts VPBank itself opened and FundLok pre-registered, which fail far less often. Twenty minutes to review and dual-authorise one instruction batch, 15 minutes per account opening, 10 minutes per account closure, 12 minutes per exception, and 5 minutes per business day reviewing the automated reconciliation summary. One full-time equivalent is 160 working hours per month.

| Period | Movements / month, Option A | Movements / month, Option B | Manual touchpoints / month | Staff-hours / month | Full-time equivalent |
|---|---|---|---|---|---|
| Month 1 | 168–336 | 1,158–2,316 | 62–78 | 14.1–17.6 | 0.09–0.11 |
| Month 3 | 414–829 | 3,384–6,769 | 69–101 | 15.6–22.2 | 0.10–0.14 |
| Month 6 | 784–1,568 | 6,724–13,448 | 81–135 | 17.8–29.0 | 0.11–0.18 |
| Month 12 | 1,523–3,046 | 13,403–26,806 | 108–213 | 23.1–44.3 | 0.14–0.28 |

Touchpoint, staff-hour and FTE ranges span both options — the lower bound is Option A at 5 loans a month, the upper Option B at 10.

A manual touchpoint is one action requiring a person: authorising an instruction batch, requesting an account opening or closure, investigating an exception, or reviewing the daily reconciliation summary.

### Incremental headcount

**0.5 full-time equivalent — one half-time operations analyst — covers the pilot through month 12.**

The modelled load at month 12 is 0.14 to 0.28 FTE depending on the account structure. FundLok states 0.5 rather than 0.28 to carry the variance the model does not: exception rates above the assumed levels in early months, the daily rather than periodic cadence of the collection cycle, and the supervised daily reconciliation review that Stage 4 of Section 3.7 requires before reverting to review by exception.

The load is dominated by a fixed component of roughly 16 staff-hours per month and a variable component that depends on settlement type: about 0.006 staff-hours per externally settled movement, and about 0.0004 per movement internal to VPBank. On that basis FundLok reaches one full role at roughly 24,000 externally settled movements per month, or 360,000 internal ones — both an order of magnitude beyond pilot volume. **The arrangement does not become staffing-intensive before it becomes worth automating.**

The account structure, not the collection cadence, is what moves these figures. Daily collection adds one movement per loan per business day. Daily *allocation* under Option B of Section 1.8 adds one per investor per loan per business day, which accounts for the eightfold difference between the two movement columns above. Because those movements are internal to VPBank and fail rarely, the effect on FundLok's own effort is modest — roughly 0.28 against 0.21 of a role at month 12 — but the effect on VPBank's processing is not, and requirement D5 of Section 3.3 exists to test it.

---

## 3.6.6 Items to be confirmed

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 1 | Answer to the question in Section 3.3.2 | Moves the Phase 1 estimate between 26.5 and 86.5 man-days. The single largest uncertainty in this section | VPBank, requested by Edward | Pending VPBank confirmation |
| 2 | VPBank's own assessment of effort against each component in 3.6.1 | FundLok's figures are indicative only; VPBank's own numbers govern | VPBank, requested by Edward | Pending VPBank confirmation |
| 3 | Which Phase 2 components fall within VPBank's Circular 64 implementation | Determines how much of the 69–125 man-day Phase 2 range is genuinely incremental | VPBank, requested by Edward | Pending VPBank confirmation |
| 4 | Form and scale of the co-funding offer in 3.6.4 | FundLok has stated which items it will contribute toward but not how much; this is a commercial decision | Loc | 2026-08-07 | 
| 5 | Account structure selected in Section 1.8 | Moves the movement volumes in 3.6.5 by roughly a factor of eight, though not the pilot headcount conclusion | Loc + Edward | 2026-08-12 |
| 6 | Whether the operations dashboards (N7) are in pilot scope | Would remove 5–8 man-days from 3.6.3 if deferred | Edward | 2026-08-12 |


<!-- ══════════════════ PASTE INTO SECTION 3.7 ══════════════════ -->

> ## ▼ Mục 3.7 — Tích hợp & kiểm thử
> ## Section 3.7 — Integration and testing
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.7.
> Paste the block below in place of `[CONTENT — …]` at section 3.7.

# 3.7 Integration and testing

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


<!-- ══════════════════ PASTE INTO SECTION 4.4 ══════════════════ -->

> ## ▼ Mục 4.4 — Bảo vệ dữ liệu & an toàn thông tin
> ## Section 4.4 — Data protection and information security
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 4.4.
> Paste the block below in place of `[CONTENT — …]` at section 4.4.

# 4.4 Data protection and information security

FundLok processes personal data of investors and of the representatives of borrowing enterprises. This section sets out the legal framework FundLok operates under, the controls in place, and the controls still to be completed before go-live.

The governing instrument is **Law No. 91/2025/QH15 on Personal Data Protection**, which took effect on **1 January 2026** (source: Law on Personal Data Protection No. 91/2025/QH15, National Assembly, 2025). It is in force now, not pending. Two of its provisions bear directly on this arrangement: breach notification is required **within 72 hours of detection**, and for a financial service provider that notification extends to the affected data subjects and not only to the regulator. The law also carries sector-specific safeguards for financial, banking and credit activities, with detail to follow in implementing regulations.

Nothing in this section asks VPBank to accept responsibility for FundLok's data protection obligations, and FundLok does not offer its own controls as a substitute for any assessment VPBank performs on its own account.

**Where this section states a commitment rather than a current state, it says so.** Items 3 and 4 of 4.4.10 are commitments with a trigger, not descriptions of today.

---

## 4.4.1 Personal data processed

| Category | Examples | Source | Crosses to VPBank |
|---|---|---|---|
| Identity data | Name, date of birth, national identifier, address, contact details | The individual | Name only, as part of a permitted-destination entry or a transfer instruction |
| Identity evidence | Identity document images, and the biometric facial comparison performed during verification | The individual, via a third-party verification provider | No |
| Enterprise data | Business registration, licence data, authorised representative identity | The SME | Name only, as above |
| Financial data | Financial statements, trading history, appraisal inputs and outputs | The SME | No |
| Settlement data | Bank or e-wallet account details, held masked | The individual or enterprise | Account number and holder name, as required for a named transfer |
| Platform data | Commitments, holdings, repayment history, access logs | Generated in use | No |
| Borrower sales data | Invoice-level sales records for the prior day, drawn from the borrower's e-invoice data through a licensed T-VAN provider, from which the daily repayment amount is computed | The borrower's e-invoice records, with the borrower's consent | No |
| Consent records | Scope, timestamp, withdrawal state | Generated in use | No |

The set that crosses to VPBank is limited to what a named bank transfer requires, and is specified in full in Section 1.5.2. The biometric facial comparison performed during verification is the most sensitive category FundLok handles; it is not shared with VPBank and is addressed specifically at 4.4.5.

**Borrower sales data requires its own treatment, and it is new.** The daily revenue-share mechanism in Section 1.4 depends on reading each borrower's prior-day sales through a licensed T-VAN provider. Invoice-level sales records are principally the borrower's own commercial data, but where the borrower sells to individuals those records may also contain personal data belonging to **the borrower's own customers** — people who have no relationship with FundLok and have given FundLok no consent. FundLok's position is that it needs only aggregate daily revenue, not counterparty detail, and that the integration should therefore either not request invoice-level counterparty fields or discard them on receipt rather than store them. Whether the T-VAN interface permits that separation is an open item at 4.4.10, and it is far cheaper to design out now than to justify later.

---

## 4.4.2 Consent mechanism

Consent is obtained at the point of collection, separately for each purpose, and is never bundled into acceptance of the platform terms as a whole. Each consent record carries its scope, the version of the notice presented, a timestamp, and its withdrawal state; the records are held in the platform and are auditable.

Consent is obtained separately for identity verification, including the biometric comparison, and for the registration of a settlement account and its use as a transfer destination. A party can withdraw consent through the platform. Where consent is withdrawn for a purpose that is a precondition of an active loan, FundLok can no longer act for that party prospectively but retains the records the loan and the law require — see 4.4.4.

Not all processing rests on consent. Processing necessary to perform the loan contract and the management authorisation contract rests on that contractual necessity, which Law 91/2025 recognises as a basis distinct from consent. FundLok's position is that this is the correct basis for instruction issuance, reconciliation and record retention, and it is one of the items for counsel confirmation at 4.4.10.

---

## 4.4.3 Access control

| Control | Implementation | Status |
|---|---|---|
| Role-based access control | Every platform endpoint authorises against the caller's role; no endpoint relies on client-side restriction | In production |
| Authentication | Token-based authentication with separate access and refresh tokens, and server-side revocation so a session can be terminated | In production |
| Credential storage | Passwords stored using Argon2 hashing; no reversible credential storage anywhere | In production |
| Least privilege | Staff access is granted per role, and access to personal data is limited to the roles that require it | In production, formal review to be documented |
| Separation of duties on money movement | Preparation and approval of a payment instruction are held by different named individuals, enforced by VPBank's channel entitlements rather than by FundLok's procedure | To be built — Section 3.5, component 1 |
| Revocation | Platform access and banking-channel entitlement are both withdrawn on a personnel change, on the same day | In production for the platform; banking channel per Section 3.3 item E2 |
| Secrets management | Application secrets held in a managed secret store, never in source control or configuration files | In production |
| Audit logging | Administrative and financial actions recorded to an append-only log; the ledger itself cannot be edited or deleted at either the application or the database layer | In production |

---

## 4.4.4 Retention

FundLok retains loan and transaction records, and the personal data necessary to interpret them, for **ten years from loan closure**. The period is set to align with the retention obligation applicable to accounting and financial records under Vietnamese law; the precise statutory basis is for counsel to confirm.

Categories held for shorter periods: identity evidence, including document images and the biometric comparison result, is retained only for as long as required to evidence that verification was performed, and the underlying images are not retained beyond that need. Access and session logs are retained for two years. Consent records are retained for the life of the relationship plus the ten-year period, because a consent record is the evidence that processing was lawful and must outlive the processing itself.

Retention and erasure interact, and the position should be stated rather than left implicit. Where a data subject requests erasure, FundLok deletes what it holds on consent and no longer needs. It does not delete records it is required by law to retain, or that are necessary to evidence a loan that existed — a completed loan cannot be unwound because one party later asks for its record to be removed, and the other party to that loan has its own interest in the record. FundLok's response to an erasure request therefore distinguishes the two sets and explains which is which.

At the end of the retention period records are deleted, and deletion is logged.

---

## 4.4.5 Biometric and sensitive data

The verification process includes a facial comparison between a submitted image and the identity document. This produces biometric data, which Law 91/2025 treats with heightened protection — and it is specifically one of the categories for which a breach must be notified to the affected individuals, not only to the regulator.

FundLok's position: the biometric comparison is performed by a specialist third-party verification provider acting as a processor on FundLok's instruction; the comparison result is retained as evidence that verification occurred; the underlying images are not retained beyond the need described in 4.4.4; and the data is not shared with VPBank at any point.

**One matter is open and material.** If the verification provider performs any part of that processing outside Vietnam, it is a cross-border transfer of biometric data and requires a transfer impact assessment, and it also sits in tension with the localisation commitment at 4.4.6. FundLok has flagged this rather than assumed it resolved — item 5 of 4.4.10.

---

## 4.4.6 Data localisation

**Commitment.** FundLok will process and store personal data relating to this arrangement within Vietnam, and will complete the migration to in-country hosting **before go-live** — that is, before Stage 3 of Section 3.7, the first live loan.

Stated plainly, because a bank should not have to infer it: FundLok's platform currently runs in a managed cloud region in South-East Asia outside Vietnam, with object storage on a globally distributed provider. That is the present state, and it is why this is written as a commitment with a trigger rather than as a description. The migration covers the application runtime, the database, object storage holding uploaded documents, and backups.

Law 91/2025 does not itself impose a general localisation requirement on all personal data. FundLok's commitment is therefore made as a matter of policy and of assurance to VPBank, and to remove any question about where data relating to a Vietnamese custodial arrangement is held. Whether any additional statutory localisation obligation applies to this activity is for counsel to confirm.

---

## 4.4.7 Encryption

| Layer | Standard |
|---|---|
| Data at rest — database, object storage, backups | **AES-256**, applied by the managed platform to all stored data and backups |
| Data in transit — party to platform, platform to VPBank, platform to processors | **TLS 1.2 or above**, with weaker protocol versions and cipher suites disabled |
| Credentials | Argon2 password hashing; application secrets in a managed secret store, encrypted at rest |
| Settlement account details | Stored masked; the full account number is used to compose an instruction and is not persisted in full |
| Document access | Time-limited pre-signed access to object storage; documents are not served from long-lived public URLs |

---

## 4.4.8 Breach response procedure

Law 91/2025 requires notification within **72 hours of detection**, and for a financial service provider that extends to affected data subjects. FundLok's procedure is built to that clock, working backwards from it.

1. **Detection and logging.** Any suspected incident is recorded on detection with the detection timestamp, which starts the 72-hour period. The timestamp is recorded first, before assessment begins, so the clock is never reconstructed after the fact.
2. **Containment.** Immediate steps to limit exposure — revoking credentials or tokens, disabling an affected integration, isolating a component. Containment does not wait for the assessment to complete.
3. **Assessment.** Within 24 hours of detection: what data, whose, how many, what cause, whether it is ongoing. Any incident touching biometric data, identity evidence or settlement data is treated as notifiable unless assessment positively establishes otherwise.
4. **Notification.** To the regulator within 72 hours of detection. To affected data subjects within the same period where the incident involves their data, in plain language, describing what happened, what data was involved, what FundLok has done, and what the individual should do.
5. **Notification to VPBank.** Where an incident affects the integrity of instruction data, the escrow arrangement or any data exchanged with VPBank, FundLok notifies VPBank without waiting for the regulatory deadline. FundLok asks VPBank to reciprocate, so that each party's 72-hour clock can be met — item 6 of 4.4.10.
6. **Remediation and record.** Root cause addressed, and the incident, timeline, decisions and rationale recorded. The record is retained whether or not the incident was notifiable, because the decision not to notify must itself be evidenced.
7. **Review.** Each incident is reviewed for whether the impact assessment at 4.4.9 needs updating.

A named individual is accountable for running this procedure. The procedure is tested rather than merely written: FundLok runs a tabletop exercise against it before go-live.

---

## 4.4.9 Impact assessments and accountability

Law 91/2025 requires a data processing impact assessment, and a transfer impact assessment where personal data is transferred across borders, with reassessment when the processing changes. It also requires an organisation to designate a data protection function, internally or through an external provider. Small businesses and startups have a five-year exemption from the impact assessment requirement.

FundLok's position:

- A **data processing impact assessment** covering the platform, the verification provider and the VPBank exchange will be completed before go-live, and reviewed on any material change to processing.
- A **transfer impact assessment** will be completed for any processing that occurs outside Vietnam, including by the verification provider, and will be closed out by the migration at 4.4.6 where the transfer ceases.
- A **designated data protection responsibility** is assigned to a named individual, with external counsel engaged for the legal assessment.
- FundLok will **not rely on the small-business exemption** unless counsel advises that it clearly applies. Producing the assessments is useful discipline regardless of whether the exemption is available, and relying on an exemption whose applicability is uncertain is a poor position to hold in front of a banking partner.

FundLok also notes the prohibition in Law 91/2025 on trading personal data, and states for the record that FundLok does not sell, license or otherwise trade personal data, and does not use investor or borrower personal data for any purpose beyond operating the platform and the loans on it.

---

## 4.4.10 Items to be confirmed

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 1 | Precise statutory basis for the ten-year retention period | Stated in 4.4.4 as aligned with accounting-record retention; the citation must be exact before this goes to VPBank | Edward, with counsel | 2026-08-14 |
| 2 | Lawful basis analysis — which processing rests on consent and which on contractual necessity | Determines whether withdrawal of consent can halt processing needed to service an active loan | Edward, with counsel | 2026-08-14 |
| 3 | Migration of application runtime, database, object storage and backups into Vietnam | 4.4.6 is a commitment, not a current state. Must complete before Stage 3 of Section 3.7 | Edward | Before go-live |
| 4 | Separation-of-duties control on payment instructions | Listed as to-be-built in 4.4.3; depends on the banking channel entitlements in Section 3.3 item E1 | Edward | Before go-live |
| 5 | Whether the third-party verification provider processes identity or biometric data outside Vietnam | Determines whether a transfer impact assessment is required for biometric data and whether the provider must be replaced or relocated to meet 4.4.6. **The most material open item in this section** | Edward, with counsel | 2026-08-14 |
| 6 | Reciprocal incident notification with VPBank, and the contact route for it | FundLok has a 72-hour clock that starts at detection, not at the point it hears about an incident on the bank side | Edward, with VPBank | Pending VPBank confirmation |
| 7 | Whether the small-business exemption from impact assessments applies to FundLok | FundLok's stated intention is not to rely on it; confirmation lets that position be stated as a choice rather than an assumption | Edward, with counsel | 2026-08-14 |
| 8 | Whether VPBank requires a data processing agreement, and on whose template | Determines the contractual layer over the exchange specified in Section 1.5 | Edward, with VPBank | Pending VPBank confirmation |
| 9 | Implementing regulations under Law 91/2025 for financial and credit activities | The law's sector-specific safeguards await implementing detail; this section may need revision when it is published | Edward, with counsel | Ongoing |
| 10 | Whether the T-VAN interface can supply aggregate daily revenue without invoice-level counterparty detail | Determines whether FundLok processes personal data of the borrower's own customers at all | Edward, with counsel | Before the integration is built |
| 11 | Lawful basis and consent wording for the T-VAN sales feed, including the borrower's authority to permit it | The borrower consents to FundLok reading its sales data; whether that consent extends to data about the borrower's own customers is a distinct question | Edward, with counsel | 2026-08-14 |
