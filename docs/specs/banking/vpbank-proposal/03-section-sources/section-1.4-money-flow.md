# 1.4 Money flow

*[CONTENT — Edward. English draft for internal review; Vietnamese version to follow.]*

---

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

---

*Dependencies: Section 1.3 (four-sided structure). Consistent with Section 1.5 (data flow), Section 1.7 (role boundaries), Section 1.8 (account structure) and Section 3.1 (process). The daily revenue-share mechanism depends on the T-VAN integration recorded in Section 3.5.*
