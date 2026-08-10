# Stakeholder Mock Data Checklist & Excel Template Guide

Use this checklist to prepare mock SME data for the **FundLok ML Underwriting & Grading Engine**.

---

## 📋 The 6 Categories of Required Mock Data (Total 28 Inputs)

### Category 1: SME Profile
| Field Name | Description for Stakeholders | Valid Options / Example |
| :--- | :--- | :--- |
| **Company Code** | Unique business identifier | e.g., `SME-2026-001` |
| **Industry** | Sector operating in | `IT Services`, `Retail Trade`, `Manufacturing`, `Logistics`, `Healthcare` |
| **Company Size** | Size category | `micro` (1-10 staff), `small` (11-50), `medium` (51-200) |
| **Operating History** | How long the business has operated | Number of months (e.g. `36` = 3 years) |

---

### Category 2: Loan Request Details
| Field Name | Description for Stakeholders | Valid Options / Example |
| :--- | :--- | :--- |
| **Loan Amount (VND)** | Requested loan principal | `1,000,000,000` to `10,000,000,000` VND |
| **Loan Term (Months)** | Loan duration | Must be: `3`, `6`, `9`, or `12` months |
| **Base Bank Rate (%)** | Benchmark interest rate | e.g. `10.5%` |

---

### Category 3: Financial History (Trailing 24 Months)
| Field Name | Description for Stakeholders | Valid Options / Example |
| :--- | :--- | :--- |
| **Monthly Revenue (M1..M24)** | 24 revenue numbers in VND (M1 = 2 years ago, M24 = last month) | e.g. `200,000,000` per month |
| **Cost of Goods Sold (COGS)** | Total COGS in the past 12 months | VND amount (e.g. `1,200,000,000`) |
| **Fixed Costs** | Annual rent, salaries, fixed overhead | VND amount (e.g. `400,000,000`) |
| **Variable Costs** | Annual utilities, freight, marketing | VND amount (e.g. `200,000,000`) |

---

### Category 4: Customer & Operational Ratios
| Field Name | Description for Stakeholders | Valid Options / Example |
| :--- | :--- | :--- |
| **Top 1 Client Share (%)** | % revenue from biggest customer | `0%` to `100%` (e.g. `25%`) |
| **Top 3 Clients Share (%)** | % revenue from top 3 customers combined | `0%` to `100%` (e.g. `50%`) |
| **Customer Retention Rate** | Repeat customer rate | Score `0` to `100` (e.g. `70`) |
| **Repeat Revenue Index** | Index of recurring billing | Score `0` to `100` (e.g. `65`) |
| **Timely Collection Rate** | % invoices collected on time | Score `0` to `100` (e.g. `80`) |
| **Sector Growth Rate (%)** | Annual industry CAGR | Percentage (e.g. `12.5%`) |
| **Owner Withdrawal Ratio** | Capital/salary drawn by owner | Score `0` to `100` (e.g. `30`) |

---

### Category 5: Credit Bureau & Compliance Checks
| Field Name | Description for Stakeholders | Valid Options / Example |
| :--- | :--- | :--- |
| **CIC Credit Score** | Vietnam CIC Credit Score | `300` to `850` (Leave empty if unrated) |
| **KYC / AML Passed** | Did the company pass KYC & AML checks? | `TRUE` or `FALSE` |
| **Fraud Flags** | System security / fraud alerts | Leave empty if clean, or e.g. `SUSPICIOUS_KYB` |

---

### Category 6: AI Qualitative Risk Scores (Scale 0 to 100)
*Scale: 0 = Extreme Risk, 50 = Average Risk, 100 = Extremely Low Risk / Excellent*

| Field Name | What It Evaluates | Stakeholder Input (0 - 100) |
| :--- | :--- | :---: |
| **Regulatory Risk** | Compliance & license stability | e.g. `75` |
| **Input Cost Volatility** | Material price fluctuation risk | e.g. `70` |
| **Cyclicality Resilience** | Resistance to economic downturns | e.g. `65` |
| **Competitive Position** | Market share & moat strength | e.g. `80` |
| **Macro Economic Exposure**| Inflation/Interest rate exposure | e.g. `70` |
| **External / Climate Risk**| Natural disaster & uncontrollable risks | e.g. `75` |
| **Founder Capability** | Executive track record & experience | e.g. `85` |

---

## 📄 Excel Sheet Layout for Stakeholders

Stakeholders can prepare data in Excel using either of these two formats:

### Format A: Simple Form (One Sheet per SME Application)
```
[ Field Name ]                       [ Stakeholder Input Value ]
Company Code:                        SME-DEMO-001
Industry:                            IT Services
Company Size:                        micro
Loan Amount Requested (VND):         1,000,000,000
Loan Term (Months):                  6
Operating History (Months):          36
CIC Credit Score:                    750
KYC/AML Passed:                      TRUE
...
Monthly Revenue (M1 to M24):         200000000 (each month)
```

### Format B: Multi-Case Table (1 Row per Application)
Use [grading_test_cases.csv](file:///Users/huynhphat/Downloads/Machine%20Learning/FundLok/grading_test_cases.csv) directly as the Excel table header.
