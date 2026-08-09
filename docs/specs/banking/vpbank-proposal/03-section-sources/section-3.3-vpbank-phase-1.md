# 3.3 What VPBank needs to build — Phase 1

*[CONTENT — Edward. English draft for internal review; Vietnamese version to follow.]*

---

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

Second, **externally settled traffic is small.** Investor funding, disbursement and investor withdrawals together stay in the low hundreds per month. Everything else is movement between accounts VPBank itself holds.

Third, because FundLok composes each batch programmatically, **the number of lines in a batch costs VPBank little; the number of batches is what costs effort.** One daily allocation batch is one batch whether it carries 80 lines or 800.

That is why a secure batch channel is sufficient for Phase 1, and why the Phase 2 trigger in Section 3.4 is expressed in movements per month rather than in loans.

---

## 3.3.2 The question that determines the scope of everything below

**Can VPBank's existing blocked-account product be used as the restricted-purpose escrow account — and can it enforce a bank-side permitted-destination list?**

This is the pivotal question in this proposal. If the answer is yes to both, most of section A below is configuration and the pilot can start quickly. If the product exists but cannot restrict destinations, then the single most important control in the structure has to be built, and that changes both the timeline and the risk position.

FundLok asks VPBank to answer three parts specifically:

1. Does an existing blocked-account or escrow product exist that can hold funds for a restricted purpose, segregated from FundLok's own operating accounts?
2. Can that product be configured so that funds may only be released to a defined list of destination accounts, with the restriction enforced by the bank rather than by FundLok's instruction discipline?
3. Can that destination list be amended in a controlled way during the life of the account, since investors join a loan over time?

---

## 3.3.3 A — Escrow account configuration

Assumes one restricted escrow account per loan. If Section 1.8 selects a different account structure, the account count changes but the requirements below do not.

| Ref | Requirement | Configuration or new build | Why it is required |
|---|---|---|---|
| A1 | A restricted-purpose account per loan, holding investor funds segregated from FundLok's own operating accounts and from other loans | CONFIGURATION if the existing blocked-account product qualifies · otherwise NEW BUILD — depends on 3.3.2 | Segregation per loan is the structural basis of the whole arrangement; no pooled balance means one loan can never fund another |
| A2 | A bank-enforced permitted-destination list, so funds may leave the account only to (a) the verified borrower account, (b) a registered investor originating account, or (c) FundLok's fee account — the last only as a proportion of an instruction that pays a beneficiary in the same movement | CONFIGURATION if supported by the existing product · otherwise NEW BUILD — depends on 3.3.2 | This is the control that makes FundLok's inability to draw on idle funds a fact enforced by the bank rather than a promise. Section 1.4.4 sets out the fee constraints |
| A2a | Capacity for at least **12 destination entries per project account**, and at least 700 entries live across the portfolio at pilot volume | CONFIGURATION, or NEW BUILD if the product caps destinations | On the working case of eight investors, a project needs eight investor destinations plus the borrower, FundLok's fee account and headroom. A product capping destinations at a low number would break the model silently |
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
| CONFIGURATION or NEW BUILD, depending on existing capacity | 2 | A2a (destination-list size), D5 (daily internal allocation capacity — Option B only) |
| CONFIGURATION or NEW BUILD, depending on the answer to 3.3.2 | 2 | A1, A2 |
| CONFIGURATION or NEW BUILD, depending on existing capability | 3 | C2, C3, D2 |
| NEW BUILD | 2 | B5 (duplicate protection), D3 (per-payer virtual accounts — desirable, not essential) |
| Not required in Phase 1 | 1 | D4 (real-time notification) |

Total: 28 requirements.

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
| 8 | Maximum number of destination entries per account (requirement A2a) | On eight investors a project needs twelve entries; a product capping at five would break the model silently | VPBank, requested by Edward | Pending VPBank confirmation |
| 7 | Cut-off times, value dating and non-business-day handling for the instruction channel | Determines what FundLok can commit to investors and borrowers on timing | VPBank, requested by Edward — recorded in Appendix C | Pending VPBank confirmation |

---

*Dependencies: VPBank confirmation, per 3.3.2. Consistent with Section 3.1 (process), Section 1.7 (role boundaries), Section 1.8 (account structure) and Section 3.4 (Phase 2). Effort estimates for each component above are in Section 3.6.*
