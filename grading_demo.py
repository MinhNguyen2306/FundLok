"""Demo script for FundLok ML Underwriting & Grading Engine.

Demonstrates multiple underwriting scenarios spanning different grading ranges,
decision types (APPROVED, REVIEW, REJECT, INSUFFICIENT_DATA), and gate triggers.

Reads test cases directly from `grading_test_cases.csv` if present (easy for Excel/BAs).
Supports '#' comment lines in the CSV file for stakeholder instructions.

Run with:
    .venv/bin/python grading_demo.py
"""

import csv
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.underwriting.grading import (
    GradingInput,
    GradingResult,
    grade,
    load_params,
)

# ANSI escape codes for terminal styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

CSV_PATH = Path(__file__).parent / "grading_test_cases.csv"


def print_banner(text: str):
    width = 72
    print(f"\n{CYAN}{'=' * width}")
    print(f" {BOLD}{text}{RESET}{CYAN}".center(width + 8))
    print(f"{'=' * width}{RESET}\n")


def format_decision(decision: str) -> str:
    if decision == "APPROVED":
        return f"{GREEN}{BOLD}✓ APPROVED{RESET}"
    elif decision == "REVIEW":
        return f"{YELLOW}{BOLD}⚠ REVIEW (Soft Gate Fired){RESET}"
    elif decision == "REJECT":
        return f"{RED}{BOLD}✗ REJECT (Hard Gate Fired){RESET}"
    elif decision == "INSUFFICIENT_DATA":
        return f"{BLUE}{BOLD}ℹ INSUFFICIENT DATA{RESET}"
    return f"{BOLD}{decision}{RESET}"


def parse_csv_row_to_input(row: Dict[str, str]) -> GradingInput:
    """Parses a single row from grading_test_cases.csv into a GradingInput object."""
    # Monthly revenue m1..m24 (24 months)
    monthly_rev_list = []
    for i in range(1, 25):
        val = row.get(f"m{i}")
        if val is not None and str(val).strip() != "":
            monthly_rev_list.append(Decimal(str(val).strip()))
        else:
            monthly_rev_list.append(None)
    
    monthly_revenue = tuple(monthly_rev_list)

    # Fraud flags
    raw_flags = row.get("fraud_flags") or ""
    fraud_flags = tuple(flag.strip() for flag in str(raw_flags).split(",") if flag.strip())

    # AI Scores
    ai_scores = {
        "regulatory": float(row["ai_regulatory"]),
        "input_cost_vol": float(row["ai_input_cost_vol"]),
        "cyclicality": float(row["ai_cyclicality"]),
        "competitor": float(row["ai_competitor"]),
        "macro": float(row["ai_macro"]),
        "uncontrollable": float(row["ai_uncontrollable"]),
        "founder": float(row["ai_founder"]),
    }

    cic_val = row.get("cic_score")
    cic_score = int(float(str(cic_val).strip())) if cic_val is not None and str(cic_val).strip() != "" else None

    return GradingInput(
        company_code=str(row["company_code"]).strip(),
        industry=str(row["industry"]).strip(),
        company_size=str(row["company_size"]).strip(),
        loan_size_vnd=Decimal(str(row["loan_size_vnd"]).strip()),
        duration_months=int(float(row["duration_months"])),
        operating_months=int(float(row["operating_months"])),
        monthly_revenue=monthly_revenue,
        cogs_y1=Decimal(str(row["cogs_y1"]).strip()),
        fixed_cost_y1=Decimal(str(row["fixed_cost_y1"]).strip()),
        variable_cost_excl_cogs_y1=Decimal(str(row["variable_cost_excl_cogs_y1"]).strip()),
        conc_top1_pct=float(row["conc_top1_pct"]),
        conc_top3_pct=float(row["conc_top3_pct"]),
        crr=float(row["crr"]),
        rri=float(row["rri"]),
        tcp=float(row["tcp"]),
        sector_cagr_pct=float(row["sector_cagr_pct"]),
        ai_scores=ai_scores,
        owner_withdrawal=float(row["owner_withdrawal"]),
        cic_score=cic_score,
        kyc_aml_passed=str(row["kyc_aml_passed"]).strip().lower() in ("true", "1", "yes"),
        fraud_flags=fraud_flags,
        bank_rate_pct=float(row["bank_rate_pct"]),
    )


def evaluate_and_display_case(case_num: str, title: str, description: str, inputs: GradingInput, params: Any, expected_decision: Optional[str] = None):
    print(f"\n{CYAN}{'=' * 72}{RESET}")
    print(f"{BOLD}{YELLOW}{case_num}: {title}{RESET}")
    print(f"{BOLD}Description:{RESET} {description}\n")

    print(f"  Company Code:     {BOLD}{inputs.company_code}{RESET}")
    print(f"  Industry:         {CYAN}{inputs.industry}{RESET}")
    print(f"  Company Size:     {inputs.company_size}")
    print(f"  Loan Requested:   {YELLOW}{inputs.loan_size_vnd:,.0f} VND{RESET}")
    print(f"  Loan Duration:    {YELLOW}{inputs.duration_months} months{RESET}")
    print(f"  Operating History:{inputs.operating_months} months")
    print(f"  CIC Score:        {inputs.cic_score if inputs.cic_score is not None else 'Missing'}")
    print(f"  KYC/AML Passed:   {inputs.kyc_aml_passed} | Fraud Flags: {inputs.fraud_flags or 'None'}")

    result: GradingResult = grade(inputs, params)

    print(f"\n  {BOLD}Decision:{RESET}         {format_decision(result.decision)}")
    
    if expected_decision:
        match_str = f"{GREEN}✓ MATCHES EXPECTED{RESET}" if result.decision == expected_decision else f"{RED}✗ MISMATCH (Expected {expected_decision}){RESET}"
        print(f"  {BOLD}Validation:{RESET}       {match_str}")

    if result.final_grade is not None:
        print(f"  {BOLD}Final Score/Grade:{RESET} {GREEN if result.final_grade >= 80 else (YELLOW if result.final_grade >= 70 else RED)}{result.final_grade:.6f} / 100{RESET}")
    else:
        print(f"  {BOLD}Final Score/Grade:{RESET} {BLUE}N/A (Data incomplete){RESET}")

    if result.interest_rate_pct is not None:
        print(f"  {BOLD}Interest Rate:{RESET}     {YELLOW}{result.interest_rate_pct:.4f}%{RESET}")
        print(f"  {BOLD}Target Total Pay:{RESET}  {YELLOW}{result.target_payment_vnd:,.0f} VND{RESET}")
        print(f"  {BOLD}Target Daily Pay:{RESET}  {YELLOW}{result.target_daily_vnd:,.0f} VND{RESET}")
    else:
        print(f"  {BOLD}Interest Rate:{RESET}     {BLUE}N/A{RESET}")

    if result.fired_gates:
        print(f"\n  {BOLD}Fired Knockout Gates:{RESET}")
        for g in result.fired_gates:
            gate_color = RED if g.severity == "hard" else YELLOW
            print(f"    - [{gate_color}{g.severity.upper()}{RESET}] Gate #{g.id} ({g.key})")
    else:
        print(f"\n  {GREEN}✓ No Knockout Gates Fired.{RESET}")

    # Top & Bottom factor scores if scorable
    if result.factor_scores and any(s is not None for s in result.factor_scores.values()):
        valid_scores = {k: v for k, v in result.factor_scores.items() if v is not None}
        sorted_factors = sorted(valid_scores.items(), key=lambda x: x[1], reverse=True)
        top3 = [f"{k}: {v:.2f}" for k, v in sorted_factors[:3]]
        bottom3 = [f"{k}: {v:.2f}" for k, v in sorted_factors[-3:]]
        print(f"  {BOLD}Top 3 Factors:{RESET}     {', '.join(top3)}")
        print(f"  {BOLD}Lowest 3 Factors:{RESET}  {', '.join(bottom3)}")

    return {
        "case": case_num,
        "title": title,
        "decision": result.decision,
        "expected": expected_decision or "N/A",
        "grade": f"{result.final_grade:.2f}" if result.final_grade is not None else "N/A",
        "rate": f"{result.interest_rate_pct:.2f}%" if result.interest_rate_pct is not None else "N/A",
        "gates": len(result.fired_gates),
    }


def run_demo():
    print_banner("FundLok ML Underwriting Engine - CSV/Excel Test Suite")

    params = load_params()
    print(f"{GREEN}✓ Loaded Parameters{RESET} (Engine v{params.engine_version}, Params v{params.params_version})")

    summary_records: List[Dict[str, Any]] = []

    if CSV_PATH.exists():
        print(f"{GREEN}✓ Loading Test Cases from Excel CSV File:{RESET} {CYAN}{CSV_PATH.name}{RESET}\n")
        with open(CSV_PATH, mode="r", encoding="utf-8") as fh:
            # Filter out comment lines starting with '#'
            lines = [line for line in fh if not line.strip().startswith("#")]
            reader = csv.DictReader(lines)
            for row in reader:
                case_id = row.get("case_id", "Case").strip()
                title = row.get("title", "Test Case").strip()
                description = row.get("description", "").strip()
                expected_decision = row.get("expected_decision", "").strip()

                # Skip any row where case_id starts with #
                if case_id.startswith("#"):
                    continue

                inputs = parse_csv_row_to_input(row)
                rec = evaluate_and_display_case(case_id, title, description, inputs, params, expected_decision=expected_decision)
                summary_records.append(rec)
    else:
        print(f"{RED}⚠ Warning: CSV file {CSV_PATH.name} not found.{RESET}")
        return

    # -------------------------------------------------------------------------
    # SUMMARY COMPARISON TABLE
    # -------------------------------------------------------------------------
    print_banner("Underwriting Comparison Summary Across Excel Test Cases")
    print(f"  {'Case':<8} | {'Title':<42} | {'Actual Decision':<28} | {'Grade':<8} | {'Interest Rate':<13}")
    print(f"  {'-'*8}-+-{'-'*42}-+-{'-'*28}-+-{'-'*13}-+-{'-'*8}-+-{'-'*13}")

    for rec in summary_records:
        dec_formatted = format_decision(rec["decision"])
        print(f"  {rec['case']:<8} | {rec['title']:<42} | {dec_formatted:<37} | {rec['grade']:<8} | {rec['rate']:<13}")

    print("\n")


if __name__ == "__main__":
    run_demo()
