# FundLok × VPBank — partnership issues register

**Internal · not for VPBank · 5 August 2026 · Edward Wong**

A working note for going into the VPBank conversation: what is genuinely open, what it costs, where FundLok should offer to help, and where it should not. Ordered by what would most change the outcome.

---

## 1. The one question that unblocks everything

**Can VPBank's existing blocked-account product serve as the restricted escrow account, with a bank-enforced permitted-destination list?** (Section 3.3.2.)

Yes to both, and Phase 1 is **29.5 man-days of configuration** and can start in weeks. No, and it is **112.5 man-days of build**, with the timeline and the risk conversation both changing. Two requirements account for 30 of those days on their own.

Everything else in this register is second-order. Get this answered before the meeting if at all possible, and if not, make it the first thing asked in it.

---

## 2. Cost exposure — where FundLok could quietly end up paying

The instinct to keep costs and fee expenditure low is right, and the place it will be tested is not the headline commercial terms. It is the per-unit fees that look trivial in isolation and are multiplied by a daily cycle.

### 2.1 Transaction fees — the largest single risk

The daily revenue-share model generates movements continuously. Under Option B, where each investor holds their own escrow account, each day's receipt fans out across every investor on the loan.

| | Movements / month | @ 1,100 VND | @ 3,300 VND | @ 5,500 VND |
|---|---|---|---|---|
| Option A, month 6 | 1,568 | 1.7m | 5.2m | 8.6m |
| Option A, month 12 | 3,046 | 3.4m | 10.1m | 16.8m |
| Option B, month 6 | 13,448 | 14.8m | 44.4m | 74.0m |
| Option B, month 12 | 26,806 | 29.5m | 88.5m | 147.4m |

At month 12 under Option B, a mid-range per-transaction fee is roughly **1.06 billion VND a year — about USD 42,000**. At the top of the range it is 1.77 billion. Under Option A the same fee costs a tenth of that.

**Position to take:** internal movements between accounts VPBank itself holds must be priced at or near zero. FundLok has a clean argument for it — those movements exist *because the money stays at VPBank* rather than being flushed out to other banks daily. The deposit float is the consideration; the transfers are the mechanism that creates it. If VPBank wants to charge per movement, then it is charging FundLok for delivering the float, and Option A becomes the better structure on cost grounds even though Option B is better on legal grounds.

**Make zero-rated internal movements a condition of adopting Option B.** Do not agree the structure and negotiate the pricing afterwards.

### 2.2 Account maintenance and minimum balances

Option B means many accounts, and accounts often carry a monthly fee and a minimum balance.

| | Accounts live | @ 50,000 VND/mo | @ 200,000 VND/mo |
|---|---|---|---|
| Month 6 | ~90 | 4.5m VND/mo | 18.0m VND/mo |
| Month 12 | ~180 | 9.0m VND/mo | 36.0m VND/mo |

A minimum balance is worse than a fee because it is dead capital that also has to come from somewhere: at 1m VND per account across 180 accounts that is 180m VND idle, and it is not obvious whose money it would be. Investor funds cannot be used to meet FundLok's minimum balance obligations without breaking the segregation story.

**Position:** no minimum balance on escrow accounts, and no per-account monthly fee on project accounts, which are short-lived by design. If a maintenance fee is unavoidable, argue for it on investor accounts only — those are long-lived and are the ones producing the float.

### 2.3 The full checklist to price before signing

Ask for all of these in writing. Each is small; together they are the actual cost of the arrangement.

- Account opening fee, per project account and per investor account
- Monthly maintenance, per account
- Minimum balance, per account, and whose capital satisfies it
- Per-transaction fee, split by internal book transfer versus interbank
- Batch instruction submission fee, per batch and per line
- Statement retrieval, and any charge for machine-readable formats
- VietQR collection fee, and who bears it — FundLok, the borrower, or netted from the receipt
- Account closure fee
- Any fee for the destination-list configuration or amendments
- Phase 2 API access and per-call charges, even if deferred
- FX or cross-border charges — should be none, the arrangement is VND only

### 2.4 Interest on escrow balances

Not a cost but an unresolved economic question. If balances earn interest, whose is it? FundLok's position should be that it belongs to the beneficiaries and FundLok will allocate it by a documented rule — claiming it would contradict the whole "not our money" position. But it needs saying before VPBank assumes otherwise.

---

## 3. Assistance without expenditure

FundLok is willing to assist, and assistance is not the same as money. Offer the first list freely; treat the second as a last resort.

### 3.1 Offer freely — costs FundLok little or nothing

1. **The integration specification is already written.** Sections 3.3 and 3.4 are a build backlog VPBank can hand to its own team. That is real work already done for them.
2. **The test plan is already written.** Section 3.7 has seventeen test cases with pass criteria and a ten-point sign-off. FundLok will run the tests and produce the evidence.
3. **FundLok will build and operate the reconciliation** and produce daily evidence that both records agree. VPBank does not need to build reconciliation on its side.
4. **Volume and activity data for VPBank's own pricing and P&L.** Loc has already noted they need this. It costs nothing to supply and it makes their internal approval easier — which is usually the real bottleneck inside a bank.
5. **Reference customer and co-marketing for VPBank's Open API programme.** They must implement Circular 64 by 1 March 2027 anyway. A live, named fintech case study is genuinely valuable to the team that has to justify that spend internally. This is the highest-value thing FundLok can offer at zero cost.
6. **Absorb the entire FundLok-side build and run cost** — already committed in 3.5, worth restating because it is a real number: 64 to 101 man-days plus ongoing operation.
7. **Phase the ask so Phase 1 is configuration only.** Already done, and worth naming as a deliberate concession rather than letting it pass unnoticed.
8. **Commit to a volume or float floor** if it helps their pricing — costs nothing if the business happens anyway, though do not commit to a floor the pilot might miss.

### 3.2 Cash co-funding — narrow this before it is offered

Section 3.6.4 currently offers to co-fund **four** items: A2 the destination list, B5 duplicate protection, D3/P7 virtual accounts, and D5 internal allocation capacity. That is inconsistent with keeping expenditure low, and it is a weak opening position because it concedes before being asked.

**Recommended narrowing:**

| Item | Current offer | Recommended |
|---|---|---|
| A2 — permitted-destination list | Co-fund | **Co-fund, capped.** This is the control the whole structure rests on and the one most likely to need real build. Worth paying for rather than losing |
| B5 — duplicate-instruction protection | Co-fund | **Withdraw the offer.** Reframe as a control that protects VPBank at least as much as FundLok — a duplicated payment is the bank's operational risk too. Banks do not usually charge a client for their own payment-integrity controls |
| D3 / P7 — virtual accounts | Co-fund | **Fund the specification and testing, not the build.** Optional capability; if VPBank does not want it, FundLok absorbs the reference-matching workload instead |
| D5 — internal allocation capacity | Co-fund | **Do not fund. Make it a pricing condition instead** (see 2.1). This exists to serve a structure that also delivers VPBank its deposit float |

Whatever is offered should carry a stated ceiling and be contingent on the partnership actually signing. An uncapped offer to co-fund a bank's build is an open cheque.

---

## 4. Issues to resolve before the document goes out

| # | Issue | Why it matters | Owner |
|---|---|---|---|
| 1 | **Section 1.7 contradicts the agreed fee mechanism.** It states funds never leave escrow to a FundLok account; the confirmed design has FundLok's fee travelling inside beneficiary instructions | If VPBank finds the contradiction before FundLok fixes it, it costs credibility on the one topic where credibility matters most | Cường |
| 2 | **Fee rates are unstated.** The management fee rate and both ceilings are to-be-confirmed | A bank will not agree a destination it cannot bound. The ceiling matters more than the rate | Loc |
| 3 | **The T-VAN integration is unbuilt and unconfirmed.** Nothing appears in the repository | If VPBank asks when FundLok can start, there is currently no answer. It is a dependency of the money flow, not a reporting nicety | Edward + Phat |
| 4 | **Hosting is outside Vietnam today.** 4.4.6 states this openly as a commitment with a trigger | Correct to disclose proactively. Being discovered would be much worse than being told | Edward |
| 5 | **Option B is recommended but its feasibility is unconfirmed.** Daily allocation volume and destination-list capacity are both unanswered | Recommending a structure VPBank cannot operate reads as unprepared. Present B as recommended *conditional on two confirmations*, with A as the stated fallback | Edward |
| 6 | **Appendices C and E scope** | Both marked "see if needed". C cannot be written without VPBank's cut-off times; E is largely inside 3.7 | Loc |

---

## 5. What FundLok is asking for, in one paragraph

VPBank holds investor funds in a restricted escrow account per loan, releases them only to a short list of pre-agreed destinations, requires two FundLok signatories on every instruction, and sends a daily machine-readable statement. FundLok does everything else and pays for it. No credit assessment, no lending decision, no credit risk, no debt collection, no dispute arbitration, and no contribution to FundLok's costs. In exchange VPBank earns custody and settlement fees and holds the deposit balances the arrangement generates.

If it cannot be said that plainly, something in the structure is wrong.

---

## 6. The two things that would most improve the odds

**Get 3.3.2 answered early.** It is the difference between a four-week start and a four-month one, and it is a question any product owner at VPBank can answer in a meeting.

**Lead with what VPBank gets, not with what FundLok needs.** Deposit float, settlement fee income, a Circular 64 reference implementation delivered by someone else's engineering team, and a segregation structure they can prove from their own records without relying on anyone's ledger. The ask reads very differently when it follows that rather than precedes it.

---

*Sources for figures: FundLok internal estimates dated 5 August 2026, on the assumptions stated in Sections 1.4.7, 3.3.1 and 3.6.5 — 5–10 loans per month, eight investors per loan, 22 business days, 12-month average term. Per-transaction and per-account fee levels are illustrative ranges for sensitivity, not quotes from VPBank.*
