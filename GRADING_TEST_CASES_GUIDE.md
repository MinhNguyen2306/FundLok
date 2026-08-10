# FundLok ML Grading Engine — Business Analyst (BA) Excel Test Guide

This guide explains how **Business Analysts (BAs)** and **Product Owners (POs)** can define and manage test cases using **Microsoft Excel** or **Google Sheets** for the FundLok ML Underwriting & Grading Engine.

---

## 🚀 Quick Start: Using the Excel / CSV Template

We have provided a ready-to-use CSV template file in the repository:
📂 **[grading_test_cases.csv](file:///Users/huynhphat/Downloads/Machine%20Learning/FundLok/grading_test_cases.csv)**

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
| `expected_decision` | Expected Result | `APPROVED`, `REVIEW`, `REJECT`, or `INSUFFICIENT_DATA` | `APPROVED` |
| `company_code` | SME Identifier Code | Text (e.g., `SME-BA-005`) | `SME-BA-005` |
| `industry` | Primary Sector | `IT Services`, `Retail Trade`, `Manufacturing`, `Logistics`, `Healthcare` | `IT Services` |
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

---

## ⚡ Underwriting Outcomes Cheat Sheet for BAs

| Decision | Description | Final Score Range | Key Triggers |
| :--- | :--- | :---: | :--- |
| **`APPROVED`** | Low-risk prime application | **80.00 – 100.00** | Strong financials, high margins, CIC > 700, 0 knockout gates fired. |
| **`REVIEW`** | Moderate risk / Needs manual sign-off | **70.00 – 79.99** | Triggers a **Soft Gate** (e.g. daily repayment $\ge 30\%$ of daily revenue or operating history < 24 months). |
| **`REJECT`** | High risk / Non-compliant | **< 70.00** or Gate Reject | Fails KYC/AML, contains fraud flags, or operates in prohibited industries. |
| **`INSUFFICIENT_DATA`** | Incomplete application | **N/A** | Missing monthly revenue numbers (< 24 months) or missing CIC score. |

---

## 🛑 Knockout Gates Reference

| Gate ID | Gate Key | Severity | Condition Trigger |
| :---: | :--- | :---: | :--- |
| **Gate 1** | `operating_history` | Soft | Operating history < 24 months |
| **Gate 2** | `history_vs_term` | Soft | Loan Duration > 25% of Operating History |
| **Gate 5** | `excluded_industry` | Hard | Prohibited industry (gambling, tobacco, weapons, etc.) |
| **Gate 6** | `kyc_aml` | Hard | `kyc_aml_passed = False` OR `fraud_flags` non-empty |
| **Gate 7** | `cic_floor` | Hard | CIC Score $\le 500$ |
| **Gate 8** | `daily_repayment_rate` | Soft | Daily repayment $\ge 30\%$ of average daily revenue |
