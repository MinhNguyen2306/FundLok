# Grading Engine — Factor Calibration (DEFERRED)

| Field | Value |
|---|---|
| **Status** | DEFERRED — revisit when repayment data exists |
| **Owner** | Edward |
| **Related** | `grading-engine-core.md`, `grading-engine-deviations.md` (D19, D28) |
| **Version** | 1.0 |
| **Date** | 2026-07-28 |
| **Trigger to revisit** | See §6. Earliest meaningful point is ~100 defaults. |

---

## 1. Why this document exists

The 22 factor curves were each calibrated in isolation from the CEO's judgment. Nothing ever forced
them onto a common scale, so a score of 50 means something different on every factor. This was
discovered while investigating why knockout Gate 3 fires on 78–100% of applications.

**It is deliberately not being fixed now.** Recalibrating today would mean replacing the CEO's
judgment with the median of 10,000 synthetic rows generated *from that same judgment* — differently
arbitrary, not more accurate, and it would move every borrower's rate by roughly a percentage point.
The correct fix requires outcome data we do not have.

This note preserves the analysis so the work is a re-run rather than a rediscovery.

---

## 2. The finding

### 2.1 "50" is not a common unit

Share of the 10,000-row golden set scoring below 50, per factor:

| Factor | % below 50 | Median score |
|---|---|---|
| Revenue Volatility | 0.00% | 95.7 |
| Seasonality | 0.00% | 86.8 |
| Sector Growth | 0.00% | 86.5 |
| Cost Flexibility | 2.37% | 96.1 |
| Operating Margin | 6.13% | 89.9 |
| Gross Margin | 18.57% | 92.9 |
| Revenue Trend | 20.70% | 57.0 |
| Revenue Type (RTI) | 24.41% | 62.8 |
| Loan/Revenue | 25.72% | 87.9 |
| SCSR | 42.55% | 60.7 |
| Regulatory *(AI)* | 42.74% | 53.0 |
| Macro *(AI)* | 43.76% | 52.0 |
| Cyclicality *(AI)* | 44.30% | 53.0 |
| Uncontrollable *(AI)* | 46.99% | 51.0 |
| Concentration Top 1 | 48.50% | 50.0 |
| Founder *(AI)* | 49.22% | 50.0 |
| CIC | 50.71% | 49.4 |
| Input Cost Volatility *(AI)* | 51.15% | 49.0 |
| Contribution Margin | 56.09% | 33.6 |
| Owner Withdrawal | 57.57% | 45.0 |
| Competitor *(AI)* | 66.32% | 43.0 |
| **Concentration Top 3** | **81.19%** | **31.0** |

Three factors never fall below 50. Top-3 Concentration falls below it for four borrowers in five
regardless of quality. So Gate 3's "4 or more factors below 50" counts *how many curves sit low*,
not *how many things are wrong with the borrower*.

Median count below 50: **4 among the 15 deterministic factors alone**, before any AI-supplied score is
counted. The gate trips on financial factors by itself.

### 2.2 Where this actually matters

Miscalibration is nearly harmless for weighted sums — a factor that always scores ~34 contributes a
roughly constant amount that the weights absorb, so borrower *ranking* is largely preserved. It is
harmful only where a score is treated as an absolute quantity. There are exactly two such places:

1. **Gate 3** — the only place in the system that compares factor scores *across* factors.
2. **The pricing formula** — maps grade directly onto a rate, so a systematically depressed grade
   means systematically higher rates for everyone.

### 2.3 Magnitude

Recalibrating all 12 sigmoid factors so the median SME scores 50 on each:

| Percentile | Grade now | Grade after | Rate now | Rate after | Δ |
|---|---|---|---|---|---|
| p10 | 58.43 | 43.74 | 15.33% | 16.50% | +1.18 pp |
| p25 | 63.26 | 48.39 | 14.94% | 16.13% | +1.19 pp |
| **median** | **68.60** | **55.02** | **14.51%** | **15.60%** | **+1.09 pp** |
| p75 | 73.48 | 61.47 | 14.12% | 15.08% | +0.96 pp |
| p90 | 77.14 | 65.81 | 13.83% | 14.74% | +0.91 pp |

**Median grade −13.6 points, median rate +109bp.** For scale, the entire Founder Experience factor is
worth 4bp.

### 2.4 A second, separate finding — the rate spread is very narrow

Current grade distribution: min 46.19, median 68.60, max 86.53. Through the pricing formula that is a
**p10-to-p90 spread of only 1.50 percentage points** (15.33% → 13.83%).

This is not a calibration bug. It is what averaging does: 22 factors roll into 4, then 4 into 1, and
extremes cancel. Recalibration widens it only to ~1.76 points.

Commercially this is the more consequential finding of the two — a lender browsing the marketplace
sees near-identical rates on very different businesses, which weakens the premise of risk-based
pricing. Addressing it means either a steeper grade→rate mapping, or less aggregation (fewer, more
decisive factors), and both are model-design questions for the CEO rather than calibration.

### 2.5 Sector dominates pricing

Because the whole stack above the factor layer is linear, the spread decomposes exactly:

```
spread_contribution(group) = 8 × weight(group) × (100 − premium(group)) / 100
```

For the median borrower (grade 68.60 → 14.51%):

| Group | Median premium | Weight | Contribution | Share of spread |
|---|---|---|---|---|
| **Sector** | 54.75 | 0.25 | 0.91 pp | **36.1%** |
| BCQ | 74.06 | 0.40 | 0.83 pp | 33.1% |
| RSG | 79.67 | 0.25 | 0.41 pp | 16.2% |
| Behavioral | 53.99 | 0.10 | 0.37 pp | 14.7% |

Sector drives more of the price than Cashflow despite carrying 15 fewer points of weight, because its
scores sit low. **The group with the weakest data foundation moves prices most.** A 10-point error in
one column of the 15 × 7 sector reference table is roughly 30bp on every loan in that industry.

This decomposition is also directly reusable for borrower rate explanations and the investor summary
(§4.4) — it is exact, not an approximation.

---

## 3. The mechanic — recalibration is 12 numbers

For a sigmoid factor:

```
score = min(100, max(0, upper / (1 + exp(±(steepness·x − intercept)))))
```

At `x = intercept/steepness` the score is exactly `upper/2`. So the **true midpoint is
`intercept/steepness`**, and it is the sole calibration knob.

To make the median SME score ~50 on a factor: set `intercept = steepness × median(raw value)`.

That is 12 values, one per sigmoid factor. The arithmetic is trivial. The work is everything around
it — see §7.

Note the two linear factors (Concentration Top 1 and Top 3, `100 − x`) have no midpoint parameter at
all, so recalibrating them means replacing the map, not tuning it. Top 3 is the worst-behaved factor
in §2.1, so this is likely to come up.

---

## 4. What "properly calibrated" actually means

**Not** "the median SME scores 50." That is population normalisation, and it is the wrong target for
credit:

- It destroys absolute meaning. A 40% gross margin is good whether or not peers achieve it. Credit
  risk is partly absolute — can this business service the debt — not purely relative.
- Scores drift as the applicant pool changes, so the same SME scores differently next year with no
  change to its business. That corrodes replayability unless the reference distribution is itself
  versioned.
- It is circular in a marketplace: forcing half of applicants below the median guarantees a fixed
  rejection rate regardless of actual portfolio quality.

**The right target is calibration against outcomes:** a score of 50 should mean *"this factor value is
associated with average observed default risk."* That requires defaults.

For reference, the normalisation families and where they land:

| Approach | Effect | Verdict here |
|---|---|---|
| Min–max | fixed range | Already done by the clamp. Says nothing about where the mass sits. |
| Z-score | mean 0, sd 1 | Comparable but unbounded; assumes rough symmetry. |
| Percentile / quantile | median → 50 by construction | Fixes Gate 3, but see the three objections above. |
| **Outcome calibration** | score ↔ observed default rate | **The actual goal. Needs data.** |

---

## 5. What must happen NOW so this is possible later

**This is the only actionable item in this document today.** Calibration later is impossible unless
the data is being captured from the first loan.

Spec 2 (`grading-engine-integration.md`) must persist, per application:

- the full normalised `GradingInput` (not just the factor scores)
- all 22 factor scores, 4 premiums, final grade — at full precision
- `engine_version` and `params_version`
- the interest rate actually quoted, and the schedule actually issued

and it must be joinable to eventual repayment outcomes — paid on time, late, defaulted, early.

Without the inputs stored, factors cannot be recomputed under new parameters. Without the outcomes
joinable, there is nothing to calibrate against. **Anything computed but not persisted is a feature
that cannot be learned from.**

---

## 6. Trigger — when to revisit

Rules of thumb, not precision. Staged:

| Stage | Data available | Action |
|---|---|---|
| Launch → first repayments | none | Monitor only. Log score distributions per industry. |
| ~30–50 completed loans | too few defaults to fit anything | Sanity-check that grades rank-order outcomes at all. |
| **~100 defaults** | first meaningful signal | Check rank-ordering per factor — does a low score actually predict worse outcomes? Drop or reweight factors with no signal. |
| **~300–500 defaults** | enough to move midpoints | Recalibrate the 12 midpoints against observed default rates. This is the intended fix. |
| 1,000+ defaults | enough to fit | Consider replacing hand-set curves with a fitted model — decision forest, per the original plan. |

The honest caveat: with a low default rate, reaching 100 defaults may take a few thousand loans.
Rank-ordering checks are available much earlier and are worth doing first — a factor that does not
rank-order is worth removing regardless of calibration.

---

## 7. Procedure when the trigger is met

1. Update the workbook — it remains the source of truth for the model. New version, not an overwrite.
2. Re-run the extraction script to regenerate `grading_params_vN.yaml` **and** the golden-set fixture.
   The existing fixture is pinned to the current model shape and **will not reconcile** after any
   change to a factor, weight, or curve. This is by design.
3. Bump `params_version`. Historical score runs keep pointing at the old version and stay replayable.
4. Re-run the full test suite. The golden test is the gate.
5. Re-run the §2.3 impact analysis and record the actual rate movement before deploying — every live
   borrower's price shifts.
6. Update this document and the deviations register.

**Do not hand-edit the YAML.** It is generated.

---

## 8. Open items this interacts with

| Item | Interaction |
|---|---|
| D19 (Gate 3 threshold) | The interim fix — count only the 17 core factors — is a workaround for this issue, not a solution. Revisit together. |
| D28 (sector reference table) | Sector drives 36% of the spread (§2.5). Errors in that table are the largest single pricing risk. |
| §2.4 (narrow rate spread) | Separate problem, separate fix, CEO's call. Do not conflate with calibration. |
| Requirements Appendix item 2 | Premium clamping — theoretical grade ceiling is 102.67, and the pricing formula has a 20% cap but no floor. |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-28 | Edward | Initial. Analysis run against `golden_set.csv.gz` (10,000 rows) at `params_version: wb-v0-20260728`. |
