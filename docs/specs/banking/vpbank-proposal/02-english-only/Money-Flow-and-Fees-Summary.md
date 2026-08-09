# How money moves, and how FundLok is paid

**Summary · 5 August 2026 · one page each way**

---

## How money moves

Money moves only between the parties' own bank accounts and the restricted escrow account held at VPBank. It never passes into an account FundLok can spend from. FundLok issues the instruction for every movement; VPBank executes it.

**Eight movements, four phases.**

**Funding.** Each investor transfers their committed principal from their own registered bank account into the project escrow account (**M1**). The account they paid from is recorded at that moment — this is what makes the closed loop enforceable later.

**Disbursement.** When the funding target is met, VPBank pays the SME's verified account (**M2**) and, in the same instruction, FundLok's disbursement fee (**M3**).

**Daily collection and allocation.** Each business day FundLok reads the SME's prior-day sales through a licensed T-VAN provider, computes the agreed percentage of revenue, and requests it. The SME pays into the project escrow account (**M4**). Once the receipt clears, each investor's pro-rata share is allocated (**M5**) and FundLok's management fee is paid in the same instruction (**M6**). Repayment therefore tracks actual trading: a slow week produces smaller receipts, a strong week larger ones, with the total obligation unchanged.

**Withdrawal or reinvestment.** An investor's balance is available as soon as the day's allocation is posted. On request, it transfers to that investor's own registered bank account (**M7**) — and to no other account. Alternatively it funds a new loan (**M8**) and the cycle begins again.

**The closed-loop rule.** Whatever an investor receives can be paid out only to the account that investor originally funded from. Changing that registered account requires re-verification that it belongs to the same verified party; it is not a self-service change. The same applies on the borrower side: the SME receives funds only at its own verified account.

**One distinction that matters operationally.** Availability and transfer are different things. An investor's money is *available* daily; it is *transferred* when they ask for it. Daily availability does not require a daily outbound payment to every investor's external bank.

**Where the un-withdrawn balance rests is not yet decided.** Under Option A it stays in the project escrow account with the entitlement tracked in FundLok's ledger. Under Option B it sits in an escrow account in the investor's own name. Section 1.8 recommends Option B, on the grounds that funds in the investor's own name are never part of FundLok's estate — but the recommendation is conditional on two confirmations from VPBank.

---

## How FundLok is paid

### Determined

**There are two fees, and who bears each is settled.**

| | Disbursement fee | Loan management fee |
|---|---|---|
| Movement | M3 | M6 |
| Funded by | **The SME** | **The investors** |
| Taken from | Gross principal, with the SME's repayment obligation calculated on the **gross** amount | Return only, never principal |
| Travels inside | The disbursement instruction (M2) | Each allocation instruction (M5) |
| Approximate rate | 1% of gross principal | To be confirmed |

The disbursement fee is the point on which fairness turns, and it is settled: because the SME repays on the gross principal, **investors are whole on their full capital**. None of their principal pays FundLok. On a VND 2.5 billion loan, investors fund 2.5 billion, FundLok takes 25 million, the SME receives 2.475 billion and repays on 2.5 billion.

**Four constraints are settled and apply to both fees.** These are what protect the beneficiaries while permitting FundLok to be paid:

1. **Never a standalone movement.** A fee line is permitted only inside an instruction that pays a beneficiary in the same movement. An instruction consisting solely of a fee is not executed.
2. **Never from idle balance.** If no beneficiary is being paid, no fee moves. FundLok cannot sweep an escrow account.
3. **Bank-verifiable.** The fee is a fixed proportion of the instruction it sits inside, so VPBank checks arithmetic on the face of the instruction rather than relying on FundLok's word.
4. **Suspended while an account is held.** Where an account is frozen under the dispute mechanism, FundLok's fee entitlement is suspended. FundLok does not keep drawing fees on a loan in default or dispute.

The net effect: FundLok can take nothing unless a beneficiary is being paid in the same movement, and can never touch investor capital.

### To be confirmed — bounded, and fine to settle with VPBank later

| # | Open | The bound it must respect |
|---|---|---|
| 1 | The loan management fee **rate** | A fixed proportion of the allocation instruction it travels in — not a periodic charge, not a balance-based charge |
| 2 | The registered **ceiling** for each fee | A maximum VPBank can enforce independently, so the constraint does not depend on FundLok's arithmetic being correct |
| 3 | The **revenue-share percentage** collected from the SME | Determines the size of M4, and therefore of M5 and M6 |
| 4 | Whether the ceiling is per instruction, per period, or both | Either is acceptable; it must be one VPBank can enforce mechanically |
| 5 | Treatment of a **rounding residual** on a pro-rata allocation | Must not accrue to FundLok. Proposal: allocate deterministically to the largest holder, so FundLok never benefits from rounding |
| 6 | Whether **interest** accrues on escrow balances | If it does it belongs to the beneficiaries, allocated by a documented rule. FundLok claiming it would contradict the structure |

Leaving the rates open is not a gap, provided the *shape* is fixed — and it is. VPBank is being asked to agree a mechanism it can verify and bound, not a number it has to trust. The number can follow.

### One point still to reconcile internally

Section 1.7 of the proposal currently states that funds never leave the escrow account to a FundLok account. The confirmed design has FundLok's fee travelling inside beneficiary instructions, which means the permitted-destination list needs a third entry, narrowly scoped to the agreed fee and bank-verifiable. That is a one-line amendment to 1.7, and it should be made before the document goes to VPBank rather than discovered by them.

### The diagram to take into the meeting

`section-1.4-closedloop` draws all of the above on one page: four party lanes across the five stages of the loop, FundLok's fee shown as a *line inside* a beneficiary instruction rather than a payment of its own, and — on the second page — VPBank's four checks expanded. It answers the two questions a bank actually asks, in the order it asks them: where can this money go, and what stops FundLok taking more than it should. A Vietnamese counterpart is at `section-1.4-closedloop-VI`.

The argument it is built to carry: how much FundLok can take is not a policy FundLok promises to keep. It is arithmetic VPBank checks on each instruction, bounded twice — as a proportion of that instruction, and by a registered ceiling.

---

*All figures are FundLok internal estimates dated 5 August 2026. The VND 2.5 billion loan and eight investors are an illustrative working case derived from the target investor profile, not a commitment on pricing or loan size. Detail in Sections 1.4 and 1.8.*
