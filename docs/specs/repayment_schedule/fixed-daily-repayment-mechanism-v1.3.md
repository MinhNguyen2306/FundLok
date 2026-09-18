<!--
SOURCE OF TRUTH. Faithful markdown rendering of
`FundLok_Fixed_Daily_Repayment_Mechanism_Spec_v1_3.docx` (Loc Vuong, 27 Aug 2026),
committed so it is greppable and indexable by the fl-knowledge MCP. The original
.docx sits beside this file. Per CLAUDE.md: if it is not written down, it does not
exist -- HANDOFF-03's implementer had to RECONSTRUCT the backstop formula and the
state-transition table because this document was not in the repo. Do not edit this
file to change the spec; Loc owns the .docx and this is regenerated from it.
-->

# FundLok — Fixed-Daily Repayment Mechanism
## System Design Specification (v1.3)

FundLok

Fixed-Daily Repayment Mechanism

System Design Specification


| Document | Fixed-Daily Repayment Mechanism — System Design Specification |
|---|---|
| Version | 1.3 |
| Date | 27 August 2026 |
| Author | Loc Vuong (loc.vuong@fundlok.com) |
| Audience | FundLok engineering / system design |
| Status | For implementation. Locked decisions in §2 are not open for re-litigation. |
| Supersedes | v1.0 (27 Aug 2026) — fixed 24-month bound replaced by the proportional backstop, see §4.5. And the revenue-sweep model (12 Aug 2026) — withdrawn, see §1.2 |
| Change in v1.3 | The extension charge is now a LATE-REPAYMENT UPLIFT: extension months bear 1.5x the contract rate per Điều 466.5(b) BLDS 2015, capped at 30%. It passes through to investors. Early repayment inside the original term rebates it. §4.2-§4.4 rewritten; D6, D7 revised; D21-D22 added. |
| Change in v1.2 | FundLok has NO direct-debit / pull capability and no OpenAPI banking access. All collection is SME-initiated PUSH, reconciled against inbound transfers. §6 rewritten; D9 revised; D18-D20 added. |
| Change in v1.1 | The terminal rule is no longer a 24-month write-off. It is ACCELERATION at 1.33x the declared term: the full remaining balance falls due. Affects D13, D15-D17, §4.5, §5, §7.3, §10, §11, §12. |
| Currency | VND, integer đồng. No sub-unit. No decimals anywhere in the system. |

Why this exists.  The prior mechanic computed each repayment as a percentage of verified daily revenue, sourced from TVAN e-invoice intermediaries. TVAN integration is not achievable — providers will neither share data nor integrate. A mechanic whose payment amount cannot be computed is not a mechanic. This document specifies the replacement.


## 1  Purpose and scope


### 1.1  What this specifies

The complete repayment mechanic for a FundLok SME facility: how the obligation is sized at origination, how it is collected daily, what happens when a collection fails, how and when the schedule may be extended, and how the facility terminates.


### 1.2  In scope

Origination sizing and schedule generation

Daily collection, retry, arrears and recovery escalation

Month-end review and the extension (relief) path

Late-repayment uplift on extension months, and both statutory ceilings

Early repayment

Terminal states: settlement and write-off

Data model, emitted events, and system invariants


### 1.3  Out of scope

Each of the following is a separate workstream and must not be inferred from this document.


| Excluded | Where it lives |
|---|---|
| Credit scoring / underwriting | Underwriting spec. This document consumes the output rate r as an input. |
| Investor-side allocation & returns | Investor platform spec. This document only emits repayment events. |
| Disbursement and fund custody | Bank/FBO custodial workstream (VPBank). This document starts at DISBURSED. |
| Revenue-data acquisition & integration | E-invoice data workstream. §7 treats revenue evidence as an input. |
| Tamper / fraud detection on revenue evidence | Deferred by decision, 27 Aug 2026. Separate spec. |
| Contract drafting and legal wording | Legal workstream. §4.3 states the compliance arithmetic only. |


## 2  Locked design decisions

These are settled. They are listed so implementation choices can be traced to a decision rather than re-derived, and so any future change has a single place to be recorded.


| ID | Decision | Value | Decided |
|---|---|---|---|
| D1 | Repayment mechanic | Fixed daily instalment. NOT a revenue sweep. | 27 Aug 2026 |
| D2 | Daily floor level | 100% of the scheduled daily amount. Hard. No tolerance band, no grace amount. | 27 Aug 2026 |
| D3 | True-up direction | DOWNSIDE ONLY. The floor is also a ceiling — the daily amount never rises above its current value. Revenue above expectation produces NO change. | 27 Aug 2026 |
| D4 | Total repayable | Fixed at origination. Increases ONLY by an approved extension fee (D6). Never otherwise. | 27 Aug 2026 |
| D5 | Duration | Variable. Extends on approved relief. Never shortens automatically (follows from D3). | 27 Aug 2026 |
| D6 | Late-repayment uplift | Extension months bear **1.5 × the contract rate**, capped at 30%. Statutory basis: Điều 466 khoản 5 điểm b, BLDS 2015 (overdue principal at 150% of the contract rate); Điều 468 caps the contract rate at 20%, so the late rate caps at 30%. Total interest is REBUILT, not incremented. | 27 Aug 2026 |
| D7 | Uplift distribution | PASSES THROUGH to investors; FundLok takes its agreed cut. Verified investor-positive: extension raises investor APY, and the uplift covers incremental risk up to ~10.5× the book-average PD. | 27 Aug 2026 |
| D8 | Early repayment | Permitted, no penalty, no discount. SME-initiated only. Same total, received sooner. | 27 Aug 2026 |
| D9 | Missed payment path | Warning emitted to local system + SME call task within the grace window → arrears if still unpaid → recollection. Note there is no bank response code: the system cannot distinguish 'unable to pay' from 'chose not to'. | 27 Aug 2026 |
| D10 | Relief authority | Automatic rules engine, with escalation to human on defined exceptions (§7.4). | 27 Aug 2026 |
| D11 | Revenue evidence | E-invoice data. Monthly review cadence. | 27 Aug 2026 |
| D12 | Interest basis | Flat on original principal. The 20% cap is tested on total nominal interest as a flat fee on the borrowed amount — NOT on realised IRR. | 27 Aug 2026 |
| D13 | Backstop | 1.33x the declared term, computed in SCHEDULED BUSINESS DAYS: ceil(4 x N0 / 3). Reaching it ACCELERATES the entire remaining balance to immediately due — it is a demand, not a write-off. | 27 Aug 2026 |
| D15 | Maximum declared term | 12 months. The former 24-month outer bound is RETIRED. The decree tenor wall still exists in law but sits outside policy and never binds. | 27 Aug 2026 |
| D16 | Backstop immutability | Computed once at origination, stored on the facility. No process, extension or human may move it. | 27 Aug 2026 |
| D17 | Write-down ordering | A write-down can only FOLLOW a missed backstop, never precede it. Recovery activity may start earlier; the write-down event may not (INV-9). | 27 Aug 2026 |
| D14 | Business-day calendar | Default 22 days/month, configurable per SME (§11, EC-01). | 27 Aug 2026 |
| D18 | NO PULL AUTHORITY | FundLok cannot debit an SME account. No direct-debit mandate, no OpenAPI banking. Every collection is an SME-initiated PUSH, detected by reconciling inbound transfers. This is a hard external constraint, not a design choice. | 27 Aug 2026 |
| D19 | Collection channels | Three, assigned at onboarding as a waterfall: (A) rail sweep — SME's customers pay a FundLok-issued QR; (B) standing order set up by the SME at their own bank; (C) manual push against an automated reminder. | 27 Aug 2026 |
| D21 | Uplift rebate | Clearing inside the ORIGINAL term incurs NO uplift. Because the uplift is folded into the recalculated daily instalments, it must be REBATED at payoff — pro-rata for extension days not used. Without the rebate the promise is hollow. | 27 Aug 2026 |
| D22 | Legal characterisation | Document the mechanism as FORBEARANCE on an amount that has fallen due — original obligation stands and remains overdue, FundLok agrees not to enforce while the revised schedule is met — NOT as the grant of a new term. An agreed new term is not quá hạn, which would forfeit the statutory 150% basis and fall back to the plain 20% ceiling. | 27 Aug 2026 |
| D20 | Payment reference | Every facility carries a unique payment reference so inbound transfers self-identify. Without it, reconciliation at ~4,400 transfers/month is not tractable. | 27 Aug 2026 |

D3 is the counter-intuitive one.  The share percentage remains in the product as a sizing input and as the month-end shortfall test, but it is not a live payment mechanic. Engineering consequence: there is no code path that increases the daily amount. Assert this (INV-2) rather than trusting it.

D18 is the most consequential constraint in this document.  Every reference to a debit, an instruction, or a retry in earlier versions assumed FundLok could pull funds. It cannot. Collection is voluntary on every single scheduled day, which means compliance is behavioural rather than technical, and the arrears signal is noisier than a bank rejection would be. Design accordingly: the system observes payments, it does not cause them.

Why the backstop is measured in days, not months.  Rounding 1.33x up to whole months distorts any term not divisible by three — a 4-month facility would get 6 months (1.50x) instead of ~5.4 (1.33x). Business days are the unit the schedule already runs on, so days give the stated multiple for every term and need no special cases.

D12 closes a previously open question.  Realised IRR under daily collection runs materially above the nominal rate. That is a disclosure and positioning matter, not a compliance breach, and it has no effect on any calculation in this document.


## 3  Definitions and notation


| Symbol | Name | Definition |
|---|---|---|
| P | Principal | Amount disbursed to the SME. Never changes. |
| r | Flat annual rate | Underwriting output. Annual, flat on original principal. Never changes after origination. |
| x | Declared duration | Duration in months declared by the SME at application. Used for sizing only. |
| D | Business days per month | Scheduled collection days per month. Default 22, per-SME configurable. |
| s | Share percentage | Target repayment as a share of monthly revenue. Sizing input and shortfall test only. |
| I | Total interest | I = P × r × x/12. Fixed at origination. |
| T | Total repayable | Current total the SME owes across the life of the facility. T₀ at origination. |
| N | Scheduled payment days | Total collection days across the facility. N₀ = D × x. |
| A | Daily instalment | Amount DUE each business day (not debited — see D18). A₀ at origination. Monotonically non-increasing. |
| B | Outstanding balance | B = T − collected_to_date. |
| Δ | Extension increment | Additional months granted by an approved extension. |
| E | Expected monthly revenue | Derived at origination: E = (T₀ / x) / s. |
| y | Actual duration | Realised duration in months at settlement, acceleration or write-off. |
| N_bs | Backstop day | ceil(4 × N₀ / 3). The scheduled business day on which the full balance falls due. Immutable (D16). |
| Δ_max | Max cumulative extension | N_bs − N₀, in business days. All extensions together cannot exceed it. |
| lr | Late rate | min(1.5 × r, 30%). Applied to extension months only (D6). |
| U | Uplift | P × lr × Δ_months/12. The rebatable component of total interest (D21). |
| ref | Payment reference | Unique per facility. The sole basis on which inbound transfers are matched (D20). |
| channel | Collection channel | A, B or C per D19. Stored on the facility; feeds expected compliance. |


## 4  Calculation rules

Arithmetic discipline.  All money is integer VND. Division uses floor. Every rounding remainder is absorbed by the FINAL instalment, never distributed. This guarantees INV-1 exactly with no floating-point drift. Do not use floats for money anywhere in this system.


### 4.1  Origination

Inputs: P, r, x, D, s. Executed once, on transition DISBURSED → ACTIVE.

I   = round( P × r × x / 12 )

T₀  = P + I

N₀  = D × x

A₀  = floor( T₀ / N₀ )

rem = T₀ − A₀ × N₀            // absorbed by instalment N₀

Sizing constraint, evaluated at approval. If it fails, the facility is not approved at this size:

monthly_obligation = T₀ / x

E                  = monthly_obligation / s

require:  s × declared_monthly_revenue  ≥  monthly_obligation


### 4.2  Extension — late-repayment uplift

Executed only on an approved extension (§7). Extension months bear 1.5× the contract rate. Total interest is REBUILT from the two rate bands, never incremented onto the old total.

lr      = min( 1.5 × r,  0.30 )                    // D6, Điều 466.5(b) + Điều 468

Δ_mo    = Δ_days / D

U       = round( P × lr × Δ_mo / 12 )              // uplift — rebatable (D21)

T       = P + round( P × r × M/12  +  P × lr × Δ_mo/12 )

B       = T − collected_to_date

N_rem   = ( D × M − days_elapsed ) + Δ_days

A_new   = floor( B / N_rem )

When an SME evidences a revenue shortfall at month-end, an approved extension adds business days to the schedule. Those days are priced at 1.5× the contract rate — a late-repayment uplift under Điều 466.5(b), capped at 30% since Điều 468 limits the contract rate to 20%.

Total interest is rebuilt from both rate bands rather than incremented: the base term at r, the extension days at the late rate. The outstanding balance is then re-spread across the remaining plus extension days, so the daily instalment always falls — provably, since the uplift is interest-only while the days it adds displace principal.

The uplift is stored separately from base interest and rebated pro-rata if the SME clears before using the extension days; clearing inside the original term rebates it in full. Cumulative extensions cannot pass the backstop at 1.33× the original term. The uplift passes through to investors.

The daily instalment always falls — this is provable, not asserted.  Before an extension the schedule satisfies B = A × N_rem exactly, so A_new < A exactly when U < A × Δ_days. The uplift is interest only; the instalments the extension days add contain PRINCIPAL. In the worked case the uplift is 2,250,000 against 38,999,994 of displaced instalments — 16.3× headroom. The inequality only fails at r × M = 24, i.e. a 600% annual rate on a 4-month facility. Assert INV-2 anyway: it is the guard that catches a mis-specified rate, not a real risk.

The uplift is compensation, not a deterrent — do not redesign it as one.  The SME gains roughly 10,500,000 of first-month cash-flow relief for a 2,250,000 charge: about 4.7 days of relief pays the fee. Making it a genuine deterrent would need ~84% annualised on the extension slice, far beyond the ceiling. The relief is deferred PRINCIPAL (large); the uplift is INTEREST (capped, small), so no interest-based charge can deter inside a 20% cap. Rationing is done by the approval rules in §7.4, not by price.


### 4.3  Statutory ceilings

Two ceilings, both mandatory. The first is tested on total nominal interest as a flat charge on the borrowed amount (D12); the second on the rate applied to extension months.

require:  r  ≤ 0.20                               // Điều 468 — contract rate

require:  lr ≤ 0.30                               // Điều 466.5(b) — 1.5 × 20%

duration_for_cap = max( M, y )                    // declared or actual, whichever longer

implied_nominal  = ( T / P − 1 ) × 12 / duration_for_cap

require:  implied_nominal ≤ 0.20                  // INV-5


| Contract rate r | × 1.5 | Applied lr | Ceiling binds? |
|---|---|---|---|
| 8.0% | 12.0% | 12.0% | no |
| 12.0% | 18.0% | 18.0% | no |
| 13.5% | 20.2% | 20.2% | no |
| 16.0% | 24.0% | 24.0% | no |
| 20.0% | 30.0% | 30.0% | yes — capped at 30% |

The 30% is narrower than it looks — see D22.  Điều 466.5(b) applies to amounts that are OVERDUE. If the mechanism is documented as an approved new term, the period is not quá hạn and the statutory 150% basis may not apply — an agreed late rate then falls back under Điều 468's 20% ceiling. At r = 12% → lr = 18% this is safe either way. At the top of the book (r = 20% → lr = 30%) it is not. Counsel item OP-12.


### 4.4  Early repayment and the uplift rebate

Clearing inside the original term incurs no uplift (D21). Because the uplift was folded into the recalculated daily instalments, honouring that requires an explicit rebate — pro-rata for extension days not used.

unused  = max( 0, Δ_days_granted − Δ_days_used )

rebate  = ( U × unused ) // Δ_days_granted

payoff  = ( T − collected_to_date ) − rebate

No penalty, no discount beyond the rebate. On receipt the facility moves directly to SETTLED. Per D8 this is a permitted and welcomed outcome; the system must not obstruct it.


### 4.5  Backstop and acceleration

The backstop replaces the former fixed 24-month bound. It is proportional to the facility, computed once at origination, and immutable thereafter (D16).

N_bs   = min( ceil( 4 × N₀ / 3 ),  24 × D )     // integer: (4×N₀ + 2) // 3

Δ_max  = N_bs − N₀                              // total extension budget, in days

On reaching business day N_bs with a balance outstanding, the entire remaining amount — unrecovered principal plus all incurred interest including any extension fees — falls due in a single demand:

acceleration_amount = T − collected_to_date


| Declared x | N₀ (days) | N_bs (days) | = months | Max extension |
|---|---|---|---|---|
| 3 months | 66 | 88 | 4.00 | 22 days (1 month) |
| 6 months | 132 | 176 | 8.00 | 44 days (2 months) |
| 12 months | 264 | 352 | 16.00 | 88 days (4 months) |

Offered terms are 6 and 12 months (D15); 3 months is shown as the illustrative case. Maximum possible facility life is therefore 16 months.

Acceleration is a demand, not a write-off.  This is the substantive change from v1.0. The facility moves to ACCELERATED and the balance is demanded in full. Daily collection CONTINUES during the cure period — it reduces the balance and requires no suspension logic. Only if the cure period expires unpaid does the facility move to IN_RECOVERY.

Ordering constraint (D17 / INV-9).  A write-down may only occur AFTER a missed backstop. Recovery activity can begin earlier — a facility in deep arrears at month 2 can be worked — but the write-down event itself cannot fire until the backstop has passed. Enforce this as a guard on the transition into WRITTEN_OFF, not as a convention.


## 5  Facility lifecycle


### 5.1  State machine

Figure 1 — Facility lifecycle state machine


### 5.2  States


| State | Meaning | Leaves when |
|---|---|---|
| DRAFT | Application received, not yet underwritten. | Underwriting passes or fails. |
| APPROVED | Underwritten and sized. Awaiting disbursement. | Funds released by the custodial process. |
| DISBURSED | Funds with the SME. Schedule not yet generated. | Schedule generated (§4.1). |
| ACTIVE | Daily collection running normally — payments observed as expected. | Payment missed, review opens, balance clears, or backstop reached. |
| ARREARS_WARNING | No matching inbound payment by cutoff, inside the grace window. Warning emitted, SME call task open. | Payment arrives, or grace window expires. |
| ARREARS | Grace window expired with the amount unpaid. Arrears balance accruing. | Arrears cleared, threshold breached, or backstop reached. |
| UNDER_REVIEW | Month-end review open. Collection CONTINUES at the current amount while under review. | Extension approved, or declined/not needed. |
| ACCELERATED | Backstop day N_bs reached with a balance outstanding. Full balance demanded. Daily collection continues during the cure period. | Balance paid in full, or cure period expires unpaid. |
| IN_RECOVERY | Arrears threshold breached, or cure period expired after acceleration. Recollection engaged. | Recovered in full, or unrecoverable AND backstop passed. |
| SETTLED | Total repayable fully collected. Terminal. | — |
| WRITTEN_OFF | Unrecoverable, and only after the backstop has passed (D17). Terminal. | — |

Collection does not pause during review.  UNDER_REVIEW is an overlay on collection, not a suspension of it. The SME keeps paying A_current until an extension is approved and a new schedule is generated. A review request is not a payment holiday.


### 5.3  Transitions


| From | To | Trigger | Guard |
|---|---|---|---|
| DRAFT | APPROVED | Underwriting decision | Sizing constraint §4.1 satisfied |
| APPROVED | DISBURSED | Funds released | Custodial confirmation received |
| DISBURSED | ACTIVE | Schedule generated | T₀, N₀, A₀ computed and persisted |
| ACTIVE | ARREARS_WARNING | No matching inbound by cutoff | inside grace_window |
| ARREARS_WARNING | ACTIVE | Matched payment received | Inside grace_window |
| ARREARS_WARNING | ARREARS | Grace window expired | Amount still unpaid |
| ARREARS | ACTIVE | Arrears balance cleared | arrears_balance = 0 |
| ARREARS | IN_RECOVERY | Threshold evaluation | arrears_balance ≥ recovery_threshold |
| ACTIVE | UNDER_REVIEW | Month-end reached | Review window open |
| UNDER_REVIEW | ACTIVE | Review concluded | Schedule regenerated, or unchanged |
| ACTIVE | SETTLED | Final collection or payoff | B = 0 |
| IN_RECOVERY | SETTLED | Recovery complete | B = 0 |
| ACTIVE | ACCELERATED | Backstop day reached | day_index ≥ N_bs and B > 0 |
| ARREARS | ACCELERATED | Backstop day reached | day_index ≥ N_bs and B > 0 |
| ACCELERATED | SETTLED | Full balance received | B = 0 |
| ACCELERATED | IN_RECOVERY | Cure period expired | B > 0 at cure expiry |
| IN_RECOVERY | WRITTEN_OFF | Unrecoverable determination | day_index > N_bs — INV-9 |


## 6  Daily collection (push model)

Read D18 first.  FundLok cannot debit an SME account. There is no direct-debit mandate and no OpenAPI banking access. The system does not initiate collection — it detects it. Everything in this section is reconciliation, not instruction.

Figure 2 — Daily collection: channel waterfall, reconciliation, and arrears escalation


### 6.1  Collection channels (D19)

Assigned at onboarding as a waterfall — take the highest channel the SME qualifies for. The channel is a field on the facility and materially changes expected compliance, so it should feed the risk grade.


|  | Channel | Behaviour |
|---|---|---|
| A | Rail sweep | The SME's own customers pay a FundLok-issued QR. Funds arrive without the SME acting at all — the closest available substitute for a pull. Best compliance. Only viable for consumer-facing merchants. |
| B | Standing order | The SME sets up a recurring transfer at their own bank at onboarding. Automated after one setup, but cancellable by them unilaterally, and requires re-setup whenever A changes on extension. |
| C | Manual push | An automated reminder is emitted each business day; the SME transfers by hand. Highest friction and highest decay. Fallback only. |

Channel A has a side effect worth deciding deliberately.  If the SME's customers pay into a FundLok QR, inflow is revenue-driven and will routinely exceed the daily amount. Sweeping the excess makes this a revenue sweep again — the model this document replaced. Sweeping exactly A and leaving the rest keeps one product. This is unresolved: see OP-10.


### 6.2  Daily cycle

At the open of each scheduled business day the system emits a reminder — always on channel C, and on channel B only if the standing order has lapsed.

Inbound transfers are reconciled against facilities on the per-facility payment reference (D20). Matching is on the reference, never on amount or payer name.

A scheduled payment is satisfied when matched inbound funds for that day meet or exceed the amount due, by the daily cutoff.

A transfer whose reference is missing or ambiguous goes to an UNMATCHED queue for manual attribution. It must never be silently discarded, and never auto-applied by best guess.

Non-business days per the SME's calendar generate no reminder, no expectation, and consume no schedule slot.


### 6.3  Missed payment path (D9)

There is no bank response code. The system cannot tell inability from unwillingness, so the escalation is time-based only.


| Step | Trigger | Required behaviour |
|---|---|---|
| 1 | No matching inbound by cutoff, inside the grace window | Move to ARREARS_WARNING. Emit warning to the local system. Create an SME call task carrying facility, amount and the channel in use. Continue daily reminders. |
| 2 | Payment arrives during the grace window | Return to ACTIVE. Close the call task. No fee, no arrears record, no credit consequence. |
| 3 | Grace window expires unpaid | Move to ARREARS. Increment arrears_balance by the shortfall. Reminders continue daily. |
| 4 | arrears_balance ≥ recovery_threshold | Move to IN_RECOVERY. Trigger recollection. Halt automated relief eligibility (§7.4 exception). |

Configuration required.  grace_window and recovery_threshold are policy parameters and must be runtime-configurable, not compiled in. Pilot suggestions: grace_window = 2 business days; recovery_threshold = 5 × A_current. Expect to retune both once real channel-mix compliance data exists.


## 7  Month-end review and extension

Figure 3 — Month-end review and extension decision flow


### 7.1  Trigger and cadence

A review window opens at each month-end. The SME may submit revenue evidence within it. No submission means no change — the system must never initiate an extension on the SME's behalf.


### 7.2  Shortfall test

capacity = s × evidenced_revenue

shortfall = capacity < monthly_obligation

If shortfall is false the review closes with no change. Per D3 there is no upside branch: revenue above expectation must not alter A, T, or duration.


### 7.3  Eligibility guards

Evidence must validate against the e-invoice data source. Unvalidated evidence is not a shortfall.

elapsed_days + Δ_days must not exceed N_bs (D13). If it would, the extension is REFUSED — the backstop cannot be moved (D16) and acceleration applies on schedule.

A_new must be ≤ A_current (INV-2). This is guaranteed by §4.2 for any lawful rate, so a larger value means the rate or the uplift is mis-specified — reject, do not clamp silently.


### 7.4  Authority and escalation (D10)

The rules engine auto-approves by default. Escalate to human review on any of:

A second or subsequent extension on the same facility

Shortfall exceeding a configurable materiality threshold

Resulting duration within a configurable margin of the backstop day N_bs

Facility currently in ARREARS or IN_RECOVERY

Cost constraint.  The approved cost model assumes algorithmic decisioning with no credit officers. The exception queue is therefore a deliberate, bounded carve-out — instrument its volume from day one. If exceptions exceed a few percent of reviews, the thresholds are wrong, not the staffing.


## 8  Data model

Minimum entities. Field lists are the required core, not an exhaustive schema.


#### facility


| Field | Type | Notes |
|---|---|---|
| facility_id | uuid | Primary key. |
| principal_p | int64 | P. Immutable after disbursement. |
| flat_rate_r | decimal(6,4) | r. Immutable after origination. |
| declared_months_x | int | x. Immutable — sizing basis and cap reference. |
| business_days_per_month | int | D. Default 22, per-SME. |
| share_pct_s | decimal(5,4) | s. Sizing and shortfall test only. |
| total_repayable | int64 | T. Mutable ONLY via approved extension fee. |
| collected_to_date | int64 | Monotonically increasing. |
| current_daily_amount | int64 | A_current. Monotonically NON-INCREASING (INV-2). |
| state | enum | See §5.2. |
| disbursed_at | timestamptz | Starts the schedule. backstop_date is derived from this plus the business-day calendar. |
| arrears_balance | int64 | 0 when not in arrears. |
| backstop_day_index | int | N_bs. Computed at origination. IMMUTABLE (D16) — enforce at DB level. |
| backstop_date | date | Derived from the business-day calendar. Recompute if the calendar changes; never move N_bs. |
| accelerated_at | timestamptz null | Set once, when the backstop is reached with a balance outstanding. |
| cure_period_ends | date null | Set on acceleration. Daily collection continues throughout. |
| collection_channel | enum | A_RAIL_SWEEP \| B_STANDING_ORDER \| C_MANUAL_PUSH (D19). Feeds expected compliance. |
| payment_reference | text unique | Unique per facility. Sole basis for matching inbound transfers (D20). |
| standing_order_status | enum null | Channel B only: ACTIVE \| LAPSED \| CANCELLED. Lapse triggers reminders. |


#### schedule_version


| Field | Type | Notes |
|---|---|---|
| schedule_version_id | uuid | New row per regeneration. Never update in place. |
| facility_id | uuid | FK. |
| version_no | int | 1 at origination. |
| daily_amount | int64 | A for this version. |
| total_days | int | N for this version. |
| effective_from | date | First business day this version governs. |
| created_by_extension_id | uuid null | Null for version 1. |


#### scheduled_payment


| Field | Type | Notes |
|---|---|---|
| scheduled_payment_id | uuid | One per facility per business day. |
| scheduled_date | date | Business day per SME calendar. |
| amount_due | int64 | A_current, or A + remainder on the final day. |
| status | enum | PENDING \| SATISFIED \| MISSED \| SKIPPED_NON_BUSINESS_DAY. No FAILED — nothing was attempted (D18). |
| satisfied_by | uuid[] null | The inbound_transfer rows that satisfied this day. A lump sum may satisfy several days. |
| cutoff_at | timestamptz | The moment after which a day counts as MISSED. |


#### inbound_transfer

New in v1.2. Because collection is push-based, the inbound transfer is a first-class record — it arrives independently of any schedule and must be reconciled to one.


| Field | Type | Notes |
|---|---|---|
| inbound_transfer_id | uuid | Primary key. |
| received_at | timestamptz | Bank value date, not import time. |
| amount | int64 | As received. |
| raw_reference | text | Verbatim from the statement. Never normalised in place. |
| matched_facility_id | uuid null | Null while unmatched. |
| match_status | enum | MATCHED \| UNMATCHED \| AMBIGUOUS \| MANUALLY_ATTRIBUTED |
| attributed_by | text null | Set only on manual attribution. Audit requirement. |
| bank_statement_id | text | Source statement, for reconciliation trace. |


#### revenue_submission  /  extension  /  fee_ledger


| Field | Type | Notes |
|---|---|---|
| revenue_submission_id | uuid | One per review window per facility. |
| review_period | date | Month being evidenced. |
| evidenced_revenue | int64 | As validated, not as claimed. |
| validation_status | enum | PENDING \| VALIDATED \| REJECTED |
| extension_id | uuid | Null if no extension resulted. |
| delta_days | int | Δ in business days. The contractual unit. |
| late_rate_applied | decimal(6,4) | lr = min(1.5×r, 30%). Stored per extension — r can differ by facility. |
| uplift_amount | int64 | U. Stored SEPARATELY from base interest so it can be rebated (D21). |
| uplift_rebated | int64 | 0 until settlement. Set on early payoff. |
| delta_days_used | int | Extension days actually consumed. Drives the pro-rata rebate. |
| decision_path | enum | AUTO_APPROVED \| HUMAN_APPROVED \| DECLINED \| REFUSED_BOUND |
| fee_ledger_id | uuid | Separate from interest for investor/FundLok split (D7). |


#### state_transition


| Field | Type | Notes |
|---|---|---|
| transition_id | uuid | Append-only. Never delete, never update. |
| from_state / to_state | enum | Both recorded explicitly. |
| trigger | text | Event that caused it. |
| occurred_at | timestamptz | ICT. |
| actor | text | system \| rules_engine \| user_id. |


## 9  Emitted events

The investor platform, notification service, and reporting all consume these. Events are facts about the past — never mutate or retract one; emit a correcting event instead.


| Event | Emitted when |
|---|---|
| facility.disbursed | Funds confirmed released. Starts the schedule and fixes N_bs. |
| facility.schedule_generated | Origination or regeneration. Carries schedule_version_id. |
| reminder.emitted | Start of each scheduled business day. Carries channel and amount due. |
| transfer.received | An inbound transfer was imported. Emitted before matching is attempted. |
| transfer.matched | Reconciled to a facility. Carries facility_id and amount. |
| transfer.unmatched | Reference missing or ambiguous. Requires manual attribution — must page someone. |
| payment.satisfied | A scheduled day was met in full. Carries new outstanding. |
| payment.missed | Cutoff passed with the day unmet. Carries shortfall. |
| facility.arrears_warning_raised | Entered ARREARS_WARNING. Consumed by the SME call workflow. |
| facility.arrears_opened | Retry window exhausted unpaid. |
| facility.recovery_triggered | Arrears threshold breached. |
| review.opened | Month-end review window opened. |
| revenue.submitted / revenue.validated | Evidence received / validation concluded. |
| extension.approved / extension.declined | Review concluded. Carries Δ_days, late_rate_applied, uplift_amount, decision_path. |
| uplift.rebated | Early settlement inside or partway through the extension. Carries rebate amount and unused days. Investor-visible — it reduces their receipt. |
| facility.accelerated | Backstop day reached with a balance outstanding. Carries acceleration_amount and cure_period_ends. Investor-visible. |
| facility.settled | B reached 0. Carries actual duration y and whether settlement was on schedule, early, or at acceleration. |
| facility.written_off | Unrecoverable, and only after the backstop has passed. Carries recovered amount and shortfall. |


## 10  System invariants

Each must be asserted in code, not assumed. A violation is a hard failure, not a warning.


| ID | Invariant | Enforcement point |
|---|---|---|
| INV-1 | collected_to_date + outstanding = total_repayable, exactly, at all times | After every payment posting and every extension |
| INV-2 | current_daily_amount never increases (D3) | Schedule regeneration — reject, do not clamp |
| INV-3 | total_repayable increases only via an approved extension fee (D4/D6) | Any write to total_repayable |
| INV-4 | No facility remains in ACTIVE or ARREARS past day N_bs with B > 0 — it must be ACCELERATED | Daily backstop evaluation |
| INV-9 | WRITTEN_OFF is reachable only when day_index > N_bs (D17) | Guard on the transition into WRITTEN_OFF |
| INV-10 | backstop_day_index never changes after origination (D16) | DB-level immutability on the column |
| INV-11 | Sum of all extensions in days ≤ Δ_max = N_bs − N₀ | Every extension approval |
| INV-13 | late_rate_applied ≤ 30% and contract rate r ≤ 20% | Origination and every extension |
| INV-14 | uplift_amount is stored separately from base interest and is never merged into it | Schema — it must remain rebatable (D21) |
| INV-15 | On settlement inside the original term, uplift_rebated = uplift_amount exactly | Payoff calculation |
| INV-5 | implied_nominal ≤ 20% (D12, §4.3) | Origination and every extension |
| INV-6 | At most one scheduled_payment per facility per date | DB unique constraint on (facility_id, scheduled_date) |
| INV-12 | An inbound_transfer is applied to at most one facility, exactly once | Unique constraint plus a settled match_status transition |
| INV-7 | Sum of scheduled amounts in the active version = outstanding balance | Schedule generation |
| INV-8 | No money field is ever a float | Type system / schema review |


## 11  Edge cases


| ID | Case | Required behaviour |
|---|---|---|
| EC-01 | Tết and public holidays | No instruction, no schedule slot consumed. Duration extends in calendar terms without an extension event or fee. Tết in particular can remove ~1–2 weeks; the calendar must be maintained per year, not derived from a weekday rule. |
| EC-02 | Rounding remainder | Absorbed entirely by the final instalment. Never distributed across days. Verify A×(N−1)+final = T. |
| EC-03 | Partial payment received | Do not treat as success. Apply to outstanding, leave the scheduled payment FAILED, and let the retry path run on the shortfall. |
| EC-04 | Payment while in arrears | Apply to arrears_balance first, then to the current day's instalment. Never net them into a single larger debit. |
| EC-05 | Overpayment | Apply to outstanding. If it clears B, settle and return the excess. Never hold a credit balance. |
| EC-06 | Extension requested while in arrears | Escalate to human (§7.4). Never auto-approve — the shortfall test cannot distinguish inability to pay from unwillingness. |
| EC-07 | Multiple sequential extensions | Permitted only up to Δ_max = N_bs − N₀. Each generates its own fee and schedule version. Second and later always escalate. The sum of all extensions is hard-capped (INV-11). |
| EC-08 | Extension would cross the backstop | Refuse it outright. The backstop cannot be moved (D16). Do not grant a reduced Δ silently — refuse, and let acceleration occur on schedule. |
| EC-09 | Early repayment mid-month | Accept B, settle immediately, cancel all remaining scheduled payments. No fee, no rebate. |
| EC-10 | Standing order lapses or is cancelled (channel B) | Detect from the absence of the expected transfer, not from any bank notification — none will arrive. Emit a distinct event, switch the facility to reminder-driven behaviour, and contact the SME. Do not treat as ordinary arrears on day one. |
| EC-11 | Transfer arrives with a missing or wrong reference | Queue as UNMATCHED. Never auto-apply on a best guess of amount or payer name. Manual attribution must record who attributed it (audit). |
| EC-17 | Lump sum covering several days | Apply forward across consecutive scheduled days until exhausted. Record every day it satisfied. Do not treat the excess as prepayment unless it clears the whole balance. |
| EC-18 | Duplicate statement import | Idempotency now sits on the INBOUND side. A re-imported statement must not create a second inbound_transfer or double-credit the facility (INV-12). |
| EC-20 | Second or later extension | Each is priced at the late rate on its own Δ, and total interest is rebuilt from all bands. Do not compound the uplift on a previous uplift — the late rate applies to PRINCIPAL, not to accrued interest. |
| EC-21 | Contract rate already at the 20% ceiling | Late rate caps at 30%, not 1.5 × 20% computed freely. Enforce the ceiling, do not let the multiplier run past it (INV-13). |
| EC-22 | SME clears part-way through the extension | Rebate the uplift pro-rata on unused extension days (§4.4). Do not rebate all-or-nothing — the SME used some of the time. |
| EC-23 | Extension approved, then SME clears inside the ORIGINAL term | Full uplift rebate. This is the case D21 exists for, and the one most likely to be missed because the uplift is already sitting inside the collected instalments. |
| EC-19 | Rail-sweep inflow exceeds the daily amount (channel A) | Policy undecided — see OP-10. Do not implement a default silently; the choice between sweeping the excess and leaving it determines whether this is still a fixed-instalment product. |
| EC-12 | Final instalment smaller than A | Occurs when outstanding < A. Debit exactly outstanding, never more. |
| EC-13 | Acceleration reached while already in arrears | Both apply. The facility moves to ACCELERATED; the arrears balance is subsumed into the accelerated amount, not tracked separately. |
| EC-14 | Partial payment during the cure period | Reduces the accelerated balance. Does NOT extend the cure period and does not return the facility to ACTIVE. Only B = 0 settles it. |
| EC-15 | Business-day calendar revised after origination | backstop_date may be recomputed, but backstop_day_index must not change (INV-10). The day index is the contractual anchor; the calendar date is derived. |
| EC-16 | Backstop falls on a non-business day | Cannot happen — N_bs is a scheduled business-day index, not a calendar date. This is the reason the definition is in days. |


## 12  Worked examples

Use these as implementation tests.  Every figure below was computed from the formulas in §4 and verified. An implementation that does not reproduce these exactly is wrong.


### 12.1  Origination

Inputs: P = 300,000,000 · r = 12% · M = 4 months · D = 22 · s = 10%. This is the average facility; r is an underwriting output and 12% is illustrative.


| Item | Value | Note |
|---|---|---|
| Total interest | 12,000,000 | P × 0.12 × 4/12 |
| Total repayable T₀ | 312,000,000 | Fixed at origination |
| Scheduled payment days N₀ | 88 | 22 × 4 |
| Daily instalment A₀ | 3,545,454 | floor(312,000,000 / 88) |
| Rounding remainder | 48 | Absorbed by day 88 |
| Final instalment | 3,545,502 | 3,545,454 + 48 |
| Reconciliation check | PASS | A₀ × 87 + final = 312,000,000 |
| Monthly obligation | 78,000,000 | T₀ / 4 |
| Min expected revenue E | 780,000,000 | 78,000,000 / 0.10 |
| Backstop N_bs | 118 days | 5.36 months · max extension 30 days |
| Late rate on extension | 18.0% | min(1.5 × 12%, 30%) |
| Implied nominal | 12.00% | Within the 20% ceiling |


### 12.2  Extension — the daily instalment always falls


| Requested | Extension | Uplift | New daily | Change |
|---|---|---|---|---|
| end month 1 | 11 d (0.5 mo) | 2,250,000 | 3,068,181 | −13.5% |
| end month 1 | 22 d (1.0 mo) | 4,500,000 | 2,710,227 | −23.6% |
| end month 2 | 11 d (0.5 mo) | 2,250,000 | 2,877,273 | −18.8% |
| end month 2 | 22 d (1.0 mo) | 4,500,000 | 2,431,818 | −31.4% |
| end month 3 | 11 d (0.5 mo) | 2,250,000 | 2,431,819 | −31.4% |
| end month 3 | 22 d (1.0 mo) | 4,500,000 | 1,875,000 | −47.1% |

Detail for the first row — request at end of month 1, +0.5 month:


| Item | Value | Note |
|---|---|---|
| Collected in month 1 | 77,999,988 | 22 × 3,545,454 |
| Uplift (18% on 0.5 mo) | 2,250,000 | 300,000,000 × 0.18 × 0.5/12 |
| New total repayable | 314,250,000 | Rebuilt: P + base interest + uplift |
| Outstanding | 236,250,012 | T − collected |
| Remaining days | 77 | 22 × 3.5 |
| NEW DAILY INSTALMENT | 3,068,181 | floor(236,250,012 / 77) |
| Final instalment | 3,068,256 | includes remainder 75 |
| INV-2 check | PASS | 2,250,000 < 38,999,994 — 16.3× headroom |
| Implied nominal, blended | 12.67% | over 4.5 months |


### 12.3  Early repayment — the uplift rebate

Extension of 11 days granted at end of month 1, uplift 2,250,000, gross balance 236,250,012.


| Extension days used | Rebate | Payoff | Case |
|---|---|---|---|
| 0 of 11 | 2,250,000 | 234,000,012 | clears inside the original term (D21) |
| 6 of 11 | 1,022,727 | 235,227,285 | part-uses the extension — pro-rata |
| 11 of 11 | 0 | 236,250,012 | uses the full extension |


### 12.4  Worst case — the backstop


| Item | Value | Note |
|---|---|---|
| Backstop N_bs | 118 days | ceil(4 × 88 / 3) = 5.36 months |
| Max cumulative extension | 30 days | 1.36 months |
| Max uplift | 6,136,364 | 300,000,000 × 0.18 × 1.36/12 |
| MAX TOTAL EVER OWED | 318,136,364 | knowable at origination |
| Daily at max extension | 2,501,420 | still below A₀ = 3,545,454 |
| Implied nominal at backstop | 13.53% | INV-5 PASS — 6.5pp of headroom |

318,136,364 is the maximum this facility can ever owe, at a blended nominal of 13.53%. Both are knowable the day it is written — which is the point of pairing a capped late rate with a proportional backstop.


## 13  Open items and external dependencies

These block full implementation. None blocks starting on §4–§6, which is the recommended first slice.


| ID | Item | Status / owner |
|---|---|---|
| OP-01 | Statement feed and reconciliation mechanics | Blocked on VPBank. With no API, inbound transfers must arrive as a file or export. At ~200 facilities × 22 days this is roughly 4,400 transfers/month to reconcile — the import path and its cadence are the single biggest unresolved operational dependency. |
| OP-10 | Rail-sweep excess policy (channel A) | UNDECIDED and consequential. If customer inflow exceeding the daily amount is swept, the product becomes a revenue sweep again. If it is left with the SME, channel A stays consistent with the fixed-instalment model but forgoes faster recovery. Decide before building channel A. |
| OP-11 | Expected credit loss re-estimation | The fee model's 2.61%/yr was not set against push-only collection. Voluntary payment on every scheduled day is structurally weaker than mandate-based collection and the loss assumption almost certainly needs revising upward. |
| OP-02 | Revenue-evidence integration | E-invoice data workstream. §7 assumes a validated revenue figure is available; the acquisition path is not yet chosen. |
| OP-12 | Legal characterisation of the extension (D22) | COUNSEL ITEM, gating for top-of-book pricing. Điều 466.5(b) applies to overdue amounts. If the mechanism is documented as an approved new term it is not quá hạn and the statutory 150% basis may fall away, capping the late rate at 20% rather than 30%. At r = 12% this is moot; at r = 20% it is not. Resolve before the contract template is finalised. |
| OP-13 | Điều 466.5(a) entitlement not used | The statute also allows 10%/yr on overdue INTEREST, separate from the 150% on principal. Currently unclaimed. Small money, already lawful — decide whether to include. |
| OP-03 | grace_window, recovery_threshold, and cure_period length | Policy. Pilot suggestions in §6.3. The cure period after acceleration is NOT yet set — suggest 10 business days. All must be configurable, not compiled, and all three should be retuned once real channel-mix compliance data exists. |
| OP-04 | Exception thresholds for §7.4 | Policy. Instrument exception volume from day one. |
| OP-05 | Business-day calendar source | Needs an annual Vietnamese public-holiday calendar including Tết. Do not derive from weekday rules (EC-01). |
| OP-06 | Tamper/fraud controls on revenue evidence | Deferred by decision 27 Aug 2026. Separate spec. §7 currently trusts validated evidence. |
| OP-07 | Provisioning and aging policy | Materially improved by the backstop: the loss-recognition tail is now bounded at 16 months (12-month term × 1.33) rather than 24. A portfolio-level aging and provisioning standard is still undecided. |
| OP-08 | Investor duration forecasting | With D3 (downside-only) duration can only extend, but the backstop now caps it. Investor modelling should treat scheduled duration as a floor and N_bs as a hard ceiling. |
| OP-09 | Re-run the volume model | Duration, escrow float and capital-recycling assumptions predate the backstop and must be recomputed against a maximum 16-month facility life. |


## 14  Non-functional requirements

Idempotency now sits on the INBOUND side, and it is still the highest-risk area. There is no debit to duplicate (D18), but a re-imported bank statement can double-credit a facility. Enforce uniqueness on the inbound transfer at the database level, not in application code (INV-12).

Money is integer VND everywhere. No floats in schema, DTOs, or calculations.

All timestamps in Asia/Ho_Chi_Minh (ICT). The daily batch window must be explicit and must not straddle midnight.

state_transition and all ledgers are append-only. Corrections are new rows with a reversal reference, never updates.

Reconciliation is no longer a control on top of collection — it IS the collection mechanism (D18). Its reliability sets the reliability of every downstream signal: arrears, relief eligibility, and the backstop evaluation all read from it.

Schedule regeneration must be a new schedule_version row. Never mutate an existing schedule; the history is needed for dispute resolution and for the cap audit trail.

Every §10 invariant assertion must fail loudly and halt the affected facility's processing rather than continuing with inconsistent state.

End of specification. Locked decisions in §2 and verified figures in §12 are the two sections to read first. Questions on mechanism to Loc Vuong; questions on the excluded workstreams in §1.3 to their respective owners.
