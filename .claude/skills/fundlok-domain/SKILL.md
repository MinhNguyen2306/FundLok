---
name: fundlok-domain
description: >-
  FundLok's business rules as engineering invariants, from the FundLok Handbook
  v3 (26 Aug 2026): what FundLok legally is and is not, how the rate is formed
  from the reference rate and the 0–100 internal grade, the immutable
  origination total, daily instalments, relief-only true-up, extension fees,
  the 1.33x backstop, terminal states, e-invoice revenue verification, custody
  and money movement, per-domain sources of truth, and the non-negotiable
  versioning/audit/override/least-privilege rules. Use this skill BEFORE
  writing or changing backend code that touches money, rates, grading,
  schedules, repayment, relief, extension, backstop, fees, the ledger,
  disbursement, revenue evidence, investor disclosure, eligibility, or audit —
  and before naming anything user-facing. It encodes rules that are not open
  for discussion; check here before inventing a behaviour.
---

# FundLok Domain Rules (Backend)

Source: **FundLok Handbook v3**, issued 26 August 2026, owner CEO. Where this
file conflicts with an older doc, this wins. Where the *handbook* conflicts
with this file, the handbook wins — say so rather than choosing yourself.

This is a fintech backend. Correctness, auditability and compliance outweigh
speed. Pair this skill with `test-driven-development`, `security-and-hardening`
and `doubt-driven-development` — see `AGENTS.md` for the full mapping.

---

## 1. What FundLok is — and what the data model may never say

FundLok is a **matching, servicing and reporting platform**. Investors provide
the capital; the credit agreement is between the **investor** and the **SME**.

| Fact | Consequence in code |
| --- | --- |
| FundLok is not a lender and not a party to the credit | **No entity in the data model may represent FundLok as a counterparty on a facility.** Lender of record is always the investor. |
| FundLok takes no credit risk | Credit risk is the investor's, and must be surfaced as such in every listing, statement and report the system generates. |
| FundLok is not a bank | Nothing in an API response, notification or generated document may imply licensed status. |
| FundLok is not a rating agency | See §9 — the grade is a *reference input*, never a credit rating. |
| FundLok does not own investor funds | See §7 — no code path may construct a payment instruction to a FundLok-owned account. |

Excluded sectors, non-negotiable regardless of the numbers: **gambling,
alcohol as a primary business, tobacco as a primary business, weapons/defence.**
Enforced as hard gate 5 in `app/underwriting/grading/gates.py`.

---

## 2. The invariants

Treat each as a testable property. If a change would break one, stop and
escalate — do not "improve" it.

**INV-1 — Rate formation.** Rate is a function of a per-application reference
rate and the 0–100 internal grade, clamped at the **statutory ceiling of 20%/yr**.
Grade 100 → the reference rate; grade 0 → the ceiling.

```
interest_rate_pct = min(rate_cap_pct,
                        bank_rate_pct + (rate_cap_pct - bank_rate_pct) * (100 - final_grade) / 100)
```

Implemented in `app/underwriting/grading/pricing.py`; parameters live in
`app/underwriting/grading/params/grading_params_v1.yaml`
(`rate_cap_pct: 20.0`, `bank_rate_default_pct: 12.0`). The quoted rate is
**all-in** — there is no second rate underneath it.

**INV-2 — Interest is flat and computed once.** Total interest is charged on
the principal at origination, **not on a reducing balance**:

```
target_payment_vnd = loan_size * (1 + interest_rate_pct/100 * duration_months/12)
```

**INV-3 — The origination total is immutable.** Written once at signing. It
does not grow because a month went badly, does not shrink because a month went
well, and **no process may recompute it**. The only thing that ever changes the
amount due is an extension fee, and that is a *separate linked ledger entry* —
never an amendment to the origination total.

**INV-4 — Outstanding balance is derived, never a mutable field.** Derive it
from the ledger. A stored, updatable `balance` column is a defect.

**INV-5 — Rate, grade and method version are stored with the offer and never
recomputed silently.** The engine already carries `engine_version` and
`params_version`; persist both alongside every grade and offer.

**INV-6 — Daily instalments.** A schedule is generated at disbursement across
the **business days of the declared term**; each instalment is the total
divided by the number of business days. The business-day calendar must be a
shared service accounting for public holidays. The schedule is the default
obligation against which everything else is measured.

**INV-7 — True-up is relief-only and strictly one-directional.**

```
adjusted_obligation = min(scheduled_obligation, agreed_share * verified_revenue)
```

It can never exceed the scheduled amount. **Relief extends duration; it never
reduces the total owed.** If revenue was strong we never ask for more. Every
relief request is evaluated against the revenue the business declared at
application — that declaration is the anchor, and verified revenue materially
below it requires a recorded explanation before relief is granted.

**INV-8 — One missed day raises a warning, not a default.** Monitoring is daily
and exception-based. A single unsettled instalment at the next business-day
reconciliation: write a risk event, notify the SME *and* the assigned internal
owner, move the facility to **watchlist** state. Watchlist ≠ default.

**INV-9 — Extension holds the annualised cost constant.** If the total is not
cleared by the declared term, the facility extends and a fee applies, derived
so the implied nominal annualised rate is **unchanged** across the extended
duration. The investor's expected yield is *restored, not increased.* Recorded
as a separate ledger entry, distributed with the standard platform share.
Permitted **only inside the backstop**.

**INV-10 — The backstop is a hard boundary.** Set at origination as
**1.33 × the declared term** and stored on the facility (6 months → ~8;
12 months → ~16). Reaching it accelerates the entire remaining balance —
unrecovered principal plus incurred interest, including any extension fee — to
immediately due. Relief and extension both operate strictly inside it, and
**no process may move the backstop date.** It is disclosed on every listing.

**INV-11 — Four terminal states only:** `repaid`, `repaid_early`,
`settled_at_backstop`, `written_down`. Early settlement clears the remaining
total **with no rebate** (paying early costs nothing extra but saves nothing —
never model or describe it as a discount). A write-down can only *follow* a
missed backstop, never precede it; the loss is partial (daily collection has
already recovered part) and is borne by the investor.

**INV-12 — Terms.** The SME declares a term; **12 months is the maximum and we
never write longer**. The declared term also sets the backstop date.
> ⚠️ Divergence to resolve, not to paper over: the handbook says the declared
> term is **6 or 12 months**, while `grading_params_v1.yaml` has
> `allowed_durations_months: [3, 6, 9, 12]`. Flag this rather than silently
> aligning either side.

---

## 3. Facility lifecycle

```
application → underwriting → offer → listing & funding → disbursement
   → active servicing → (watchlist | relief | extension)
   → repaid | repaid early | settled at backstop | written down
```

**Every transition is logged with who caused it, when, and on whose approval.**
States are not skipped, and are never reversed by editing a field — model
transitions explicitly and reject illegal ones at the service layer.

---

## 4. Where truth lives

Exactly one source of truth per domain. Nothing important is stored twice. If
you need a value that already has an owner, read it — do not copy it.

| Domain | Source of truth for | Roughly |
| --- | --- | --- |
| Business master | Legal identity, tax code, sector, ownership, authority to sign | `app/projects`, `app/sme` |
| Application | What was requested, by whom, through which channel, current state | `app/lending/models.py`, `app/loans` |
| Tax & invoice records | Verified revenue and the evidence behind it | `app/verification`, `app/gverify`, `app/uploads` |
| Credit & obligations | Existing debt, repayment history, burden | underwriting inputs (CIC) |
| Rating | Score, method version, and the inputs that produced them | `app/underwriting/grading` |
| Facility ledger | Origination total, schedule, collections, relief, fees, balance | `app/ledger`, `app/contracts` |
| Risk events | Warnings, watchlist entries, data gaps, anomalies | — |
| Investor | Profile, verification status, commitments, holdings, returns | `app/market`, `app/payments` |

---

## 5. Engineering rules that are not negotiable

1. **Version everything a user was shown** — every rating, method, offer and
   disclosure. If we cannot reconstruct what someone saw on the day they agreed
   to it, we have a problem we cannot answer.
2. **The audit log is immutable.** It records data access, rating changes,
   offer changes, approvals, consents and contract events. Append-only; no
   update or delete path.
3. **Every manual override captures who, why, when, and whose approval.**
   An override with no reason recorded is a defect — enforce it in the schema,
   not in a convention.
4. **Least-privilege access, enforced by role.** Sales, underwriting,
   engineering, compliance and operations do not see the same things. Note the
   existing pattern in `app/loans/service.py`: return **404, not 403**, when a
   resource exists but isn't the caller's — 403 confirms which ids are real and
   is an enumeration oracle over other SMEs' borrowing.
5. **Personal and financial data encrypted in transit.** No exceptions, no
   temporary ones.
6. **Source documents and derived features are stored separately**, so any
   decision can be audited back to the evidence it came from.
7. **Never build a production dependency on an endpoint we do not control.**
   External lookups (tax portal, CIC) are corroboration, not infrastructure —
   design the fallback as the primary path.
8. **Assume a regulator, bank, investor or auditor will read these records.**
   Build as if that review is already scheduled.

Plus the repo's own rules: schema changes need an Alembic migration; `pytest`
before done; money is `Decimal` at the boundary (see the money-boundary note in
`pricing.py`).

---

## 6. Revenue verification

Evidence comes from tax records — VAT declarations and **e-invoices**.

- **Accept the signed XML original only.** Reject PDFs, screenshots and
  spreadsheets **at upload** — they are editable and prove nothing.
- Validate signature and schema against the **current statutory appendix**.
- Check completeness **arithmetically, not by inspection**:
  - within a period: `count(invoices) == max_number - min_number + 1 - verified_cancellations`
  - across periods: this period's lowest number follows directly from last
    period's highest.
  - Invoice numbering is legally required to be continuous, so **a gap is
    evidence, not a formatting quirk.** Surface it; never auto-heal it.
- Portal lookup and sampling are **fallback controls** — never primary.

**Invoiced revenue ≠ true revenue.** We only measure what was invoiced, so our
share of invoiced revenue is a larger share of what the business actually
earns, and facilities must be sized knowing that. The sector's
invoiced-to-true ratio is itself an underwriting input; a borrower whose ratio
drops sharply is either losing business or starting to hide it — both material,
neither should pass unnoticed.

---

## 7. How money moves

- Investor funds sit with **custodial bank partners** (plural, unnamed — see §9).
- Money leaves in **exactly two directions**: to a verified SME account against
  a signed agreement, or back to the investor who sent it. **It never moves
  into a FundLok account.**
- The permitted-destination whitelist is **enforced by the bank, not by our
  application**, so a defect on our side cannot misroute funds. Do not
  re-implement it as the only control — and do not rely on our copy of it.
- FundLok holds **instruction rights only**, exercised under **dual control**.
- Beneficial ownership is maintained on the FundLok ledger and delivered to the
  custodian at an agreed cadence, with audit rights.
- **No code path may construct an instruction to a FundLok-owned account.**
  Treat this as a review blocker, not a style note.

Ledger architecture: double-entry, omnibus-first but escrow-compatible — see
`app/ledger/models.py`, ADR-002 and ADR-003 in `docs/adr/`.

---

## 8. Investor-facing obligations

Before committing, an investor must be able to see: the rating, the verified
revenue behind it, **how recent that data is**, the expected repayment pattern,
the fees, concentration risks, **the gaps in the data**, and what happens if
the business underperforms.

- Returns are presented as **ranges and scenarios — never a single precise
  figure, and never a guarantee.** Any API that returns a projected return
  should return a range, and any endpoint returning a point estimate needs a
  reason.
- Commitments are tiered: standard onboarding at lower levels, **EDD** above a
  defined threshold, and a **cap on total exposure per investor**.

---

## 9. Language — in identifiers and in anything we emit

Tone is a compliance control. These apply to API field names, enum values,
error `detail` strings, notification and email templates, and generated
documents — anywhere text can reach a user.

| Never | Always |
| --- | --- |
| "chấm điểm" in any form; "credit score"/"credit rating" for our grade | "Điểm doanh nghiệp và lãi suất tham khảo" / *business score and reference rate*. We are not a licensed rating company. |
| "FundLok never holds funds" | "FundLok is not the owner of the funds, has no right to draw on them for its own purposes, and holds only instruction rights within bank-enforced conditions." |
| Naming a specific custodial bank | "custodial bank partners" / "đối tác ngân hàng lưu ký" — plural and unnamed. Nothing is signed. |
| Naming or debating our regulatory framework | "We operate as a technology and arranger platform within reviewed legal boundaries." Route specifics to the CEO. |

Also never, in any outbound string: a promised or guaranteed return; principal
protection, a reserve or an insurance-like safety net; a claim of licensed
status; "no risk", "no documents needed", "approval guaranteed", "everyone
qualifies". And never pressure language in collections output — the first
question on a missed payment is **what happened**, not when they will pay.

Internal figures (costs, margins, pricing inputs, projections) must never leak
into an external response payload, even approximately.

---

## 10. Handbook mechanics not yet in this codebase

As of this writing, the repo implements grading and pricing (INV-1, INV-2),
the double-entry ledger, KYC/KYB and verification. **No code was found for
backstop dates, true-up/relief, extension fees, watchlist state, or the
business-day calendar** (`grep` for `backstop`, `true_up`, `extension_fee`,
`watchlist` returns nothing under `app/`).

When you implement any of them: build to §2 above, write a spec under
`docs/specs/` first (see `spec-driven-development`), and **do not invent
adjacent behaviour the handbook does not describe.** Ask.

Also note the current pricing approximation: `working_days_per_month: 21`,
`working_days_per_year: 252` are constants, while INV-6 requires a real
business-day calendar with public holidays. Closing that gap is a spec change,
not a silent constant swap.

---

## 11. Known conflicts with `CLAUDE.md` — raise, don't resolve

`CLAUDE.md` (v1.2, July 2026) predates Handbook v3 (August 2026) and describes
the platform differently in places. The handbook supersedes older documents,
but these are architectural, so **flag them to the CEO/CTO rather than
unilaterally rewriting either document or the code.**

| `CLAUDE.md` says | Handbook says |
| --- | --- |
| "a Vietnam-registered **P2P lending platform**" | Not a lender, not a party to the credit — an arranger/technology platform. External positioning must never read as lending. |
| "**FL holds a custodial account** at a licensed Vietnamese bank"; money flows `Lender → FL Omnibus Account → Borrower` | §5.12: funds sit with **custodial bank partners**; money **never moves into a FundLok account**; FundLok holds **instruction rights only**, under dual control, with the destination whitelist enforced by the bank. If "FL Omnibus Account" means *an account in FundLok's name*, that is a direct conflict. If it means *a partner-held omnibus account FundLok can instruct*, the wording needs to change to match §7.4. |
| `FL Omnibus Acct → FL Revenue` ledger leg | Same as above — a fee posting must not be modelled as money moving into a FundLok-owned bank account. |
| "converted **shares** after repayment", `app/share_conversion/` | The handbook describes four terminal states and no equity issuance. Out of scope as written. |
| "**ML grading engine** assigns interest rate tier" | Rate is a deterministic function of reference rate and grade (INV-1), versioned and reproducible. The shipped engine is deterministic; keep it that way unless a spec says otherwise. |
| Regulatory framework named in repo docs (Decree 94, Circular 64, ADR-004) | Fine **internally** — §9 says build to the strictest standard available. But it is **never discussed with an outside party**, so it must not leak into API responses, public docs or anything shipped to a partner. |

---

## Before you call it done

- [ ] No new path lets the origination total, the backstop date, or an audit
      row be mutated.
- [ ] Anything a user could be shown is versioned, and the version is persisted.
- [ ] New money paths keep `Decimal` precision and cannot target a
      FundLok-owned account.
- [ ] Role checks present; unauthorised access returns 404, not 403.
- [ ] Overrides capture who/why/when/approval.
- [ ] Outbound strings pass §9.
- [ ] Alembic migration written for schema changes; `pytest` clean.
