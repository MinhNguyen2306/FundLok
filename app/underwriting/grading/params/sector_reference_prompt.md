# Sector Reference Table — Authoring Prompt

**Purpose:** this is the prompt used to author and refresh
`sector_reference_v1.yaml`. It is checked in so that the next refresh is a
comparable re-run rather than a fresh guess.

**When to use it:** on the cadence recorded per column in the YAML, or when a
regulatory event affects a specific sector. Refresh a **column** at a time (one
factor across all 15 industries) — that is how the source data arrives.

**Who runs it:** an engineer runs the prompt, a human reviews the output, the CEO
signs off. The output is never used unreviewed to price a real loan.

**Critical:** this prompt runs *offline*, at authoring time. The grading engine
never calls an LLM. See `sector-reference-table.md` §6 R1.

---

## The prompt

> You are assisting a Vietnamese P2P lending platform (FundLok) that underwrites
> SME loans of 200m–5bn VND over 3–12 month terms. You are scoring **sector-level
> risk**, i.e. properties shared by every business in an industry — not any
> individual borrower.
>
> For each of the 15 industries listed below, assign a score from 0 to 100 for the
> factor described. **Higher always means lower risk.**
>
> Ground your reasoning in the Vietnamese market specifically — its regulatory
> regime, export dependencies, weather exposure, property cycle and competitive
> structure. Do not use figures from developed markets as a proxy.
>
> For every score, give one sentence naming the dominant driver. Be concrete: name
> the specific input cost, the specific regulation, the specific exposure. "Fuel
> prices swing hard and are the dominant cost" is useful; "moderately volatile
> costs" is not.
>
> **Calibration constraints — these matter more than any individual score, because
> this table drives 36% of the interest rate spread:**
>
> - Use the full range. The lowest-risk industry on a factor should score near 80–85
>   and the highest-risk near 20–25. Do not cluster everything in the 40s and 50s.
> - The **mean across all 15 industries** for each factor should land near **50**.
>   If your scores average 65 or 35, you have shifted the whole loan book's pricing.
> - Rank first, then assign numbers. Get the ordering right, then space the values.
>
> The 15 industries: Retail Trade, Construction Materials, Food & Beverage,
> Agriculture & Farming, IT Services, Professional Services, Tourism & Hospitality,
> Education & Training, Electronics Retail, Textile & Garment, Healthcare &
> Pharmacy, Beauty & Personal Care, Furniture & Woodwork, Logistics & Transport,
> Manufacturing.
>
> Output a table: industry, score, one-sentence driver.

---

## Per-factor rubric

Append the relevant block to the prompt above. One factor per run.

### Factor 14 — Regulatory Exposure

> How exposed is this industry to licensing requirements and regulatory change?
> **High score = light, stable regulation. Low score = heavily licensed or facing
> active regulatory change.**
>
> Consider: licences needed to operate, how often the rules change, whether a rule
> change can halt trading, and compliance cost as a share of a small operator's
> overhead. Note that heavy licensing cuts both ways — it is a burden here, but it
> also raises barriers to entry, which belongs in Competitor Proxy, not this factor.
>
> Anchors: 80 = essentially unregulated commercial activity. 30 = requires sector
> licences with ongoing inspection and periodic rule changes.

### Factor 15 — Input Cost Volatility

> How volatile are this industry's dominant input costs?
> **High score = stable inputs. Low score = volatile inputs.**
>
> Identify the single largest input cost first, then judge its volatility. A
> labour-dominated cost base is stable; a commodity-dominated one is not.
>
> Worked example (the CEO's own): for a logistics company, fuel is the dominant
> input, fuel prices swing hard, therefore risky, therefore a low score.
>
> Anchors: 82 = costs are mostly salaries. 25 = costs are mostly agricultural
> commodities or energy.

### Factor 16 — Cyclicality

> How sensitive is demand to a downturn?
> **High score = essential, defensive demand. Low score = discretionary.**
>
> Ask what happens to this industry's revenue when Vietnamese household or business
> spending contracts 15%. Medicine keeps selling; holidays do not.
>
> Anchors: 88 = non-deferrable necessity. 25 = pure discretionary spending.

### Factor 17 — Competitor Proxy

> How defensible is a small operator's position?
> **High score = real barriers to entry. Low score = anyone can enter and copy.**
>
> Consider capital intensity, licensing moats, technical skill, switching costs, and
> whether a competitor can replicate the offer in a month.
>
> Worked examples (the CEO's): a simple F&B business scores low — "anybody can copy
> anyone". Metal manufacturing scores higher — capital equipment is a genuine
> barrier.
>
> Anchors: 70 = licensed or capital-intensive. 25 = a competitor can open next door
> next month.

### Factor 18 — Macroeconomics Exposure

> How exposed is this industry to interest rates, FX, inflation and external demand?
> **High score = insulated. Low score = highly exposed.**
>
> Consider export dependence (FX and foreign demand), rate sensitivity (property and
> credit-linked sectors), and whether the customer base is domestic and stable.
>
> This is the fastest-moving column. Refresh quarterly against SBV conditions.
>
> Anchors: 78 = domestic, non-discretionary, unlevered demand. 25 = export-dependent
> or property-cycle-linked.

### Factor 19 — Uncontrollable Risks

> What exogenous risks can this industry not manage away?
> **High score = few. Low score = materially exposed.**
>
> Weather, flood, typhoon, crop or animal disease, physical supply chokepoints,
> spoilage. Vietnam-specific geography matters — this is not a generic score.
> Exclude anything the operator can insure or hedge cheaply.
>
> Anchors: 82 = office-based work with no physical exposure. 20 = open-field
> agriculture in a typhoon corridor.

### Factor 13 input — Sector CAGR

> Give the compound annual growth rate for this industry in Vietnam, as a
> percentage, over the most recent available multi-year period.
>
> **This is a raw figure, not a score.** Do not scale it to 0–100 — the engine feeds
> it through its own curve. Negative values are valid for contracting sectors.
>
> Cite the source and period for each figure. Prefer GSO (General Statistics Office)
> data. Where no official figure exists, say so and give a reasoned estimate flagged
> as such rather than presenting it as published.

---

## After running

1. Check the calibration block in the YAML still holds — mean premium near 54.75,
   premium range roughly 39–72. Run the check script.
2. Any change to a value means: update the cell, update that column's `as_of`,
   bump `sector_reference_version`, keep the previous file rather than overwriting.
3. Reset `reviewed_by` to null for any column you touched. Reviewed status does not
   survive a value change.
4. Re-run the full test suite. A change here does **not** affect the golden set,
   which supplies its own sector values — if the golden test fails after editing
   this file, something is wired wrong. See `sector-reference-table.md` §6 R2.
