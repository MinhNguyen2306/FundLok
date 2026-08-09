# 3.6 Effort and cost estimate

*[CONTENT — Edward and Huy. English draft for internal review; Vietnamese version to follow.]*

---

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
| 4 | Form and scale of the co-funding offer in 3.6.4 | FundLok has stated which items it will contribute toward but not how much; this is a commercial decision | Loc, with Edward and Huy | 2026-08-07 |
| 5 | Account structure selected in Section 1.8 | Moves the movement volumes in 3.6.5 by roughly a factor of eight, though not the pilot headcount conclusion | Loc + Edward | 2026-08-12 |
| 6 | Whether the operations dashboards (N7) are in pilot scope | Would remove 5–8 man-days from 3.6.3 if deferred | Edward | 2026-08-12 |
| 8 | Confirmation from Phat of the T-VAN integration's status | N10's estimate of 7–12 man-days assumes nothing exists. Nothing appears in the repository as at 5 August 2026 | Edward, with Phat | 2026-08-12 |
| 7 | Validation of the FundLok estimates in 3.6.3 by Huy | Second opinion on the velocity assumption before the figures are shown externally | Huy, with Edward | 2026-08-07 |

---

*Dependencies: Section 3.3 (Phase 1) and Section 3.4 (Phase 2). Consistent with Section 3.5 (FundLok's build) and Section 3.7 (integration and testing).*
