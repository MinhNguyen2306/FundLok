# 3.4 What VPBank needs to build — Phase 2

*[CONTENT — Edward. English draft for internal review; Vietnamese version to follow.]*

---

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

---

*Dependencies: Section 3.3 (Phase 1) and Section 1.8 (account structure). Effort estimates for each component above are in Section 3.6.*
