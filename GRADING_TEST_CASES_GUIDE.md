# FundLok ML Grading Engine — Business Analyst (BA) Excel Test Guide

This guide explains how **Business Analysts (BAs)** and **Product Owners (POs)** can define and manage test cases using **Microsoft Excel** or **Google Sheets** for the FundLok ML Underwriting & Grading Engine.

---

## 🚀 Quick Start: Using the Excel / CSV Template

We have provided a ready-to-use CSV template file in the repository root:
📂 **[`grading_test_cases.csv`](./grading_test_cases.csv)**

### Step 1: Open in Microsoft Excel or Google Sheets
- Open **Microsoft Excel** or **Google Sheets**.
- Choose **File $\rightarrow$ Open** and select `grading_test_cases.csv`.
- Each row in the spreadsheet represents **one SME applicant / test case**.

### Step 2: Add or Edit Test Cases
- You can edit existing cases or scroll to a new row to add `Case 5`, `Case 6`, etc.
- Fill out the columns for financial numbers, loan details, credit scores, and AI risk scores.

### Step 3: Save as CSV
- In Excel, select **File $\rightarrow$ Save As**.
- Choose format: **CSV (Comma delimited) (*.csv)** or **CSV UTF-8**.
- Save the file as `grading_test_cases.csv` in the project root directory.

### Step 4: Run Automated Evaluation
Run this single command in your terminal:
```bash
.venv/bin/python grading_demo.py
```
The script will automatically read your Excel file, grade every test case, validate actual vs expected decision, and display a detailed report!

---

## 📊 Excel Column Reference Guide

| Column Name | Business Meaning | Allowed Values / Format | Example Value |
| :--- | :--- | :--- | :--- |
| `case_id` | Test Case Identifier | Text (e.g. `Case 5`) | `Case 5` |
| `title` | Brief Title | Text | `High Margin Tech Startup` |
| `description` | Case Description | Text | `Evaluating 6-month term loan for SaaS startup` |
| `expected_decision` | Expected Result | `APPROVED`, `AI_PENDING`, `REVIEW`, `REJECT`, or `INSUFFICIENT_DATA` | `APPROVED` |
| `company_code` | SME Identifier Code | Text (e.g., `SME-BA-005`) | `SME-BA-005` |
| `industry` | Primary Sector | One of the 15 supported values **exactly** (see below), or an excluded industry. Any other value raises an error — it is not graded as "unknown". | `IT Services` |
| `company_size` | Scale Category | `micro` (1-10 staff), `small` (11-50), `medium` (51-200) | `micro` |
| `loan_size_vnd` | Requested Amount in VND | Number without commas (e.g., `2000000000`) | `2000000000` |
| `duration_months` | Loan Term in Months | `3`, `6`, `9`, or `12` | `6` |
| `operating_months` | Months in Business | Integer (e.g. `36`) | `36` |
| `cogs_y1` | Cost of Goods Sold (Year 1) | VND number | `1200000000` |
| `fixed_cost_y1` | Fixed Costs (Rent, Salaries) | VND number | `400000000` |
| `variable_cost_excl_cogs_y1` | Variable Operating Costs | VND number | `200000000` |
| `conc_top1_pct` | % Revenue from Top 1 Client | Percentage number (0 to 100) | `25.0` |
| `conc_top3_pct` | % Revenue from Top 3 Clients | Percentage number (0 to 100) | `50.0` |
| `crr` | Customer Retention Rate | 0 to 100 | `70.0` |
| `rri` | Repeat Revenue Index | 0 to 100 | `65.0` |
| `tcp` | Timely Collection Percentage | 0 to 100 | `80.0` |
| `sector_cagr_pct` | Sector Growth Rate % | Percentage number (e.g. `12.5`) | `12.5` |
| `owner_withdrawal` | Owner Salary/Capital Ratio | 0 to 100 | `30.0` |
| `cic_score` | Vietnam Credit Bureau Score | 300 to 850 (Leave blank if missing) | `740` |
| `kyc_aml_passed` | KYC / AML Compliance | `True` or `False` | `True` |
| `fraud_flags` | Fraud Warnings | Empty or flag names e.g. `SUSPICIOUS_KYB` | ` ` |
| `bank_rate_pct` | Benchmark Bank Rate | Percentage (e.g. `10.5`) | `10.5` |
| `ai_regulatory` | AI Regulatory Score | 0 to 100 | `75.0` |
| `ai_input_cost_vol` | AI Input Cost Volatility Score | 0 to 100 | `70.0` |
| `ai_cyclicality` | AI Cyclicality Resilience Score | 0 to 100 | `65.0` |
| `ai_competitor` | AI Competitive Position Score | 0 to 100 | `80.0` |
| `ai_macro` | AI Macroeconomic Exposure | 0 to 100 | `70.0` |
| `ai_uncontrollable` | AI Climate/External Risk Score | 0 to 100 | `75.0` |
| `ai_founder` | AI Founder Capability Score | 0 to 100 | `85.0` |
| `m1` ... `m24` | 24 Monthly Revenue Columns | VND numbers per month (m1 = 24 months ago, m24 = last month). Leave blank if unknown. | `200000000` |

### Supported `industry` values

Copy these strings exactly — spelling and `&` included. Source of truth is
`supported_industries` in `app/underwriting/grading/params/grading_params_v1.yaml`.

`Retail Trade` · `Construction Materials` · `Food & Beverage` · `Agriculture & Farming` ·
`IT Services` · `Professional Services` · `Tourism & Hospitality` · `Education & Training` ·
`Electronics Retail` · `Textile & Garment` · `Healthcare & Pharmacy` · `Beauty & Personal Care` ·
`Furniture & Woodwork` · `Logistics & Transport` · `Manufacturing`

The five **excluded** industries — `gambling`, `alcohol`, `tobacco`, `weapons`, `defence` — are
also accepted as input, and are hard-rejected by Gate 5. Use them to test rejection paths.

### The seven `ai_*` columns

These are **inputs, not outputs**. The engine never calls an AI service — it reads the seven
scores you type here as already-committed 0–100 numbers. The AI service that will eventually
produce them is not built yet.

**Leave any one of them blank and the decision becomes `AI_PENDING`** — the engine will not
guess, and will not score that factor as 0. `Case 5` in the template is exactly this: a prime
applicant with `ai_founder` left empty.

---

## ⚡ Underwriting Outcomes Cheat Sheet for BAs

There are **five** decision states.

> ⚠️ **The decision is not a score band.** The grade does not decide anything — the **gates** do.
> A borrower graded 55 with no gates fired is `APPROVED`; a borrower graded 85 that fails KYC is
> `REJECT`. The grade only sets the **interest rate**. (For scale: across the 10,000-row golden set
> the grade runs 46.19 → 86.53 with a median of 68.60, so a score-band rule would reject almost
> everyone. Earlier versions of this table showed 80–100 / 70–79.99 / <70 bands — those never
> existed in the engine and have been removed.)

| Decision | Description | Key Triggers |
| :--- | :--- | :--- |
| **`APPROVED`** | Priceable, no blockers | All 7 AI scores present and **no** gate fired. |
| **`AI_PENDING`** | Grading not finished | One or more of the 7 `ai_*` scores is missing. Not an error — the normal state until the AI scoring service exists. A **provisional** grade and rate are still returned; see the warning below. |
| **`REVIEW`** | Needs manual sign-off | A **soft** gate fired (operating history < 24 months, duration > 25% of history, or daily repayment ≥ 30% of daily revenue). |
| **`REJECT`** | Non-compliant / blocked | A **hard** gate fired: KYC/AML failed, any fraud flag, or an excluded industry. Not overridable. |
| **`INSUFFICIENT_DATA`** | Cannot score at all | Fewer than 24 monthly revenue values or any month blank; `cic_score` blank; `kyc_aml_passed` blank; or Year-1 revenue, total cost, or the minimum trailing-12 revenue computes to zero. No grade and no rate are produced — the fields come back empty, never `0`. |

### Resolution order

When more than one condition is true, the engine resolves in this order — first match wins:

```
REJECT  (any hard gate)
  → AI_PENDING  (any of the 7 AI scores missing)
    → REVIEW  (any soft gate)
      → APPROVED
```

`INSUFFICIENT_DATA` is checked before any of the above, and no scoring is attempted.

A hard gate therefore outranks `AI_PENDING` — KYC failure blocks the application whether or not
the AI scores have arrived. `AI_PENDING` outranks `REVIEW`, because we cannot ask a human to
sign off on a grade that is not finished.

> ⚠️ **An `AI_PENDING` grade and rate are provisional — never quote them.** The engine still
> computes them from whatever factors are present: the Sector group is renormalised over its
> present factors, but `founder` is a *bonus* factor, so a missing founder score contributes
> **0** rather than being renormalised away. A provisional grade is therefore biased **low**, and
> the quoted rate would be too high. Treat grade and rate as absent until the decision is no
> longer `AI_PENDING`.
>
> Case 1 and Case 5 in the template demonstrate this: identical applicants, except Case 5 is
> missing its `ai_founder` score. Case 1 grades **92.45** at **11.22%**; Case 5 grades **91.98** at
> **11.26%**. Same borrower, worse price, purely because a score has not arrived yet.

---

## 🛑 Knockout Gates Reference

| Gate ID | Gate Key | Severity | Status | Condition Trigger |
| :---: | :--- | :---: | :---: | :--- |
| **Gate 1** | `operating_history` | Soft | Active | Operating history < 24 months |
| **Gate 2** | `history_vs_term` | Soft | Active | Loan duration > 25% of operating history |
| **Gate 3** | `low_factor_count` | Soft | **Disabled** | Count of factor scores below 50 ≥ threshold. Fires on 95–98% of the golden set at the specified thresholds, so it ships off pending a business decision. |
| **Gate 4** | `first_loan_tenor` | — | Not in engine | Enforced in the application UI, not here. |
| **Gate 5** | `excluded_industry` | Hard | Active | `gambling`, `alcohol`, `tobacco`, `weapons`, `defence` |
| **Gate 6** | `kyc_aml` | Hard | Active | `kyc_aml_passed = False` **or** `fraud_flags` non-empty |
| **Gate 7** | `cic_floor` | Hard | **Disabled** | CIC score ≤ 500. Ships off until the CIC scale is confirmed against the real CIC report layout. |
| **Gate 8** | `daily_repayment_rate` | Soft | Active | Daily repayment ≥ 30% of average daily revenue |

**Gates 3 and 7 are switched off in the params file, not in code.** A test case that expects a
reject on a CIC score of 450 will come back `APPROVED` today — that is correct current behaviour,
not a bug. Enabling either is a one-line YAML change.

Note that `cic_score` is still **required** — a blank one gives `INSUFFICIENT_DATA`. Only the
`≤ 500` floor is disabled.
