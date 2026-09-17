"""Score-run persistence and replay; bank rate config (T3/T4, HANDOFF-03).

  - bank_rate_config              -- T0b: bank_rate_pct is a board-set
                                      constant with an effective date,
                                      replacing a GradingInput dataclass
                                      default. Seeded with the baseline
                                      12.0% effective 2026-09-17 (the T0b
                                      resolution date), so start_score_run
                                      always has a rate.
  - loan_application_financials   -- new, mutable/upsert: the raw material
                                      a GradingInput is assembled from
                                      (T3) -- nothing else in the codebase
                                      stores an SME's revenue history,
                                      concentration ratios, AI scores,
                                      CIC/KYC outcome anywhere at all.
                                      Progressive: financial fields are
                                      nullable, since incompleteness is
                                      what produces INSUFFICIENT_DATA
                                      (R8), not an input error.
  - score_runs                    -- new columns: decision (the grading
                                      outcome, distinct from the existing
                                      lifecycle `status` -- see
                                      app/lending/models.py's ScoreRun
                                      docstring for why), engine_version,
                                      params_version,
                                      sector_reference_version,
                                      final_grade_precise,
                                      interest_rate_pct, bank_rate_pct,
                                      bank_rate_effective_from.
  - score_run_inputs              -- new, append-only (BEFORE UPDATE/DELETE
                                      trigger, reusing
                                      ledger_immutability_guard()): the
                                      exact structured GradingInput used
                                      for one score run, for replay.

Spec: docs/specs/underwriting/grading-engine-integration.md

Revision ID: 298cd240e4f1
Revises: 9142fb4c8540
Create Date: 2026-09-17 00:00:00.000000

"""
import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, UUID

# revision identifiers, used by Alembic.
revision: str = "298cd240e4f1"
down_revision: Union[str, None] = "9142fb4c8540"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------
    # loan_application_financials (T3) -- mutable, upsert-style
    # -----------------------------------------------------------------
    op.create_table(
        "loan_application_financials",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("industry", sa.Text(), nullable=False),
        sa.Column("company_size", sa.Text(), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=False),
        sa.Column("operating_months", sa.Integer(), nullable=False),
        sa.Column("monthly_revenue_vnd", ARRAY(sa.Numeric(20, 0)), nullable=True),
        sa.Column("cogs_y1_vnd", sa.Numeric(20, 0), nullable=True),
        sa.Column("fixed_cost_y1_vnd", sa.Numeric(20, 0), nullable=True),
        sa.Column("variable_cost_excl_cogs_y1_vnd", sa.Numeric(20, 0), nullable=True),
        sa.Column("conc_top1_pct", sa.Float(), nullable=True),
        sa.Column("conc_top3_pct", sa.Float(), nullable=True),
        sa.Column("crr", sa.Float(), nullable=True),
        sa.Column("rri", sa.Float(), nullable=True),
        sa.Column("tcp", sa.Float(), nullable=True),
        sa.Column("sector_cagr_pct_override", sa.Float(), nullable=True),
        sa.Column("ai_score_regulatory_override", sa.Float(), nullable=True),
        sa.Column("ai_score_input_cost_vol_override", sa.Float(), nullable=True),
        sa.Column("ai_score_cyclicality_override", sa.Float(), nullable=True),
        sa.Column("ai_score_competitor_override", sa.Float(), nullable=True),
        sa.Column("ai_score_macro_override", sa.Float(), nullable=True),
        sa.Column("ai_score_uncontrollable_override", sa.Float(), nullable=True),
        sa.Column("ai_score_founder_override", sa.Float(), nullable=True),
        sa.Column("owner_withdrawal", sa.Float(), nullable=True),
        sa.Column("cic_score", sa.Integer(), nullable=True),
        sa.Column("kyc_aml_passed", sa.Boolean(), nullable=True),
        sa.Column("fraud_flags", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["application_id"], ["loan_applications.id"], ondelete="CASCADE"),
    )

    # -----------------------------------------------------------------
    # bank_rate_config (T0b)
    # -----------------------------------------------------------------
    op.create_table(
        "bank_rate_config",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("rate_pct", sa.Numeric(6, 4), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by_actor_id", UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("rate_pct > 0 AND rate_pct < 20", name="bank_rate_config_rate_pct_check"),
        sa.ForeignKeyConstraint(["created_by_actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.execute(
        """
        INSERT INTO bank_rate_config (id, rate_pct, effective_from)
        VALUES (gen_random_uuid(), 12.0, '2026-09-17')
        """
    )

    # -----------------------------------------------------------------
    # score_runs: T4 new columns
    # -----------------------------------------------------------------
    op.add_column("score_runs", sa.Column("decision", sa.Text(), nullable=True))
    op.add_column("score_runs", sa.Column("engine_version", sa.Text(), nullable=True))
    op.add_column("score_runs", sa.Column("params_version", sa.Text(), nullable=True))
    op.add_column("score_runs", sa.Column("sector_reference_version", sa.Text(), nullable=True))
    op.add_column("score_runs", sa.Column("final_grade_precise", sa.Float(), nullable=True))
    op.add_column("score_runs", sa.Column("interest_rate_pct", sa.Float(), nullable=True))
    op.add_column("score_runs", sa.Column("bank_rate_pct", sa.Numeric(6, 4), nullable=True))
    op.add_column("score_runs", sa.Column("bank_rate_effective_from", sa.Date(), nullable=True))
    op.create_check_constraint(
        "score_runs_decision_check",
        "score_runs",
        "decision IS NULL OR decision IN ('APPROVED', 'REVIEW', 'REJECT', 'INSUFFICIENT_DATA', 'AI_PENDING')",
    )

    # -----------------------------------------------------------------
    # score_run_inputs (T4) -- append-only
    # -----------------------------------------------------------------
    op.create_table(
        "score_run_inputs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("score_run_id", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("company_code", sa.Text(), nullable=False),
        sa.Column("industry", sa.Text(), nullable=False),
        sa.Column("company_size", sa.Text(), nullable=False),
        sa.Column("loan_size_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=False),
        sa.Column("operating_months", sa.Integer(), nullable=False),
        sa.Column("monthly_revenue_vnd", ARRAY(sa.Numeric(20, 0)), nullable=False),
        sa.Column("cogs_y1_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("fixed_cost_y1_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("variable_cost_excl_cogs_y1_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("conc_top1_pct", sa.Float(), nullable=True),
        sa.Column("conc_top3_pct", sa.Float(), nullable=True),
        sa.Column("crr", sa.Float(), nullable=True),
        sa.Column("rri", sa.Float(), nullable=True),
        sa.Column("tcp", sa.Float(), nullable=True),
        sa.Column("sector_cagr_pct", sa.Float(), nullable=False),
        sa.Column("sector_reference_version", sa.Text(), nullable=True),
        sa.Column("ai_score_regulatory", sa.Float(), nullable=True),
        sa.Column("ai_score_input_cost_vol", sa.Float(), nullable=True),
        sa.Column("ai_score_cyclicality", sa.Float(), nullable=True),
        sa.Column("ai_score_competitor", sa.Float(), nullable=True),
        sa.Column("ai_score_macro", sa.Float(), nullable=True),
        sa.Column("ai_score_uncontrollable", sa.Float(), nullable=True),
        sa.Column("ai_score_founder", sa.Float(), nullable=True),
        sa.Column("owner_withdrawal", sa.Float(), nullable=True),
        sa.Column("cic_score", sa.Integer(), nullable=True),
        sa.Column("kyc_aml_passed", sa.Boolean(), nullable=True),
        sa.Column("fraud_flags", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("bank_rate_pct", sa.Numeric(6, 4), nullable=False),
        sa.Column("bank_rate_effective_from", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["score_run_id"], ["score_runs.id"], ondelete="CASCADE"),
    )

    # Append-only: reuses ledger_immutability_guard() (created by 862160bce972),
    # same pattern as state_transition (9142fb4c8540).
    op.execute(
        """
        CREATE TRIGGER trg_score_run_inputs_append_only
        BEFORE UPDATE OR DELETE ON score_run_inputs
        FOR EACH ROW EXECUTE FUNCTION ledger_immutability_guard();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_score_run_inputs_append_only ON score_run_inputs")
    op.drop_table("score_run_inputs")
    op.drop_constraint("score_runs_decision_check", "score_runs", type_="check")
    op.drop_column("score_runs", "bank_rate_effective_from")
    op.drop_column("score_runs", "bank_rate_pct")
    op.drop_column("score_runs", "interest_rate_pct")
    op.drop_column("score_runs", "final_grade_precise")
    op.drop_column("score_runs", "sector_reference_version")
    op.drop_column("score_runs", "params_version")
    op.drop_column("score_runs", "engine_version")
    op.drop_column("score_runs", "decision")
    op.drop_table("bank_rate_config")
    op.drop_table("loan_application_financials")
