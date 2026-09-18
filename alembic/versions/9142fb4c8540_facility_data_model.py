"""Facility data model (T6, HANDOFF-03).

Five tables for the fixed daily repayment mechanism (spec §8), S4 scope
(no revenue_submission, extension, or fee_ledger -- extensions are out of
MVP):

  - facility           -- one row per disbursed contract on a fixed schedule
  - schedule_version    -- the generated schedule (always exactly one row
                            per facility under S4)
  - scheduled_payment   -- one row per expected business-day instalment
  - inbound_transfer    -- bank statement lines (S2, matched by payment_reference)
  - state_transition    -- append-only audit trail of facility state changes

All money is Numeric(20,0) (T1). Two DB-level guarantees beyond ordinary
constraints:

  - `state_transition` is append-only (BEFORE UPDATE/DELETE trigger),
    mirroring the ledger's ADR-002 pattern.
  - `facility.backstop_day_index` (N_bs) is immutable once set (INV-10):
    a BEFORE UPDATE trigger allows the NULL -> value transition exactly
    once and rejects any further change, without freezing the rest of the
    facility row (status, arrears_balance_vnd, etc. must stay mutable).

Spec: docs/specs/repayment_schedule/facility-data-model.md

Revision ID: 9142fb4c8540
Revises: ca8a6db6183e
Create Date: 2026-09-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "9142fb4c8540"
down_revision: Union[str, None] = "ca8a6db6183e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FACILITY_STATES = (
    "DRAFT", "APPROVED", "DISBURSED", "ACTIVE", "ARREARS_WARNING",
    "ARREARS", "ACCELERATED", "IN_RECOVERY", "SETTLED", "WRITTEN_OFF",
)
SCHEDULED_PAYMENT_STATUSES = ("PENDING", "SATISFIED", "MISSED")
INBOUND_TRANSFER_STATUSES = ("UNMATCHED", "MATCHED", "APPLIED")


def upgrade() -> None:
    # --- facility -----------------------------------------------------
    op.create_table(
        "facility",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contract_id", UUID(as_uuid=True), nullable=False),
        sa.Column("principal_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("annual_rate_pct", sa.Numeric(6, 3), nullable=False),
        sa.Column("contractual_term_months", sa.Integer(), nullable=False),
        sa.Column("interest_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("total_obligation_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("business_day_count", sa.Integer(), nullable=False),
        sa.Column("backstop_day_index", sa.Integer(), nullable=True),
        sa.Column("backstop_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="DRAFT"),
        sa.Column("payment_reference", sa.Text(), nullable=False),
        sa.Column("disbursed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cure_period_ends", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_to_date_vnd", sa.Numeric(20, 0), nullable=False, server_default="0"),
        sa.Column("arrears_balance_vnd", sa.Numeric(20, 0), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint(f"status IN {FACILITY_STATES}", name="ck_facility_status"),
        sa.CheckConstraint("principal_vnd > 0", name="ck_facility_principal_positive"),
        sa.CheckConstraint("interest_vnd >= 0", name="ck_facility_interest_non_negative"),
        sa.CheckConstraint("total_obligation_vnd > 0", name="ck_facility_total_obligation_positive"),
        sa.CheckConstraint("business_day_count > 0", name="ck_facility_business_day_count_positive"),
        sa.CheckConstraint(
            "backstop_day_index IS NULL OR backstop_day_index >= business_day_count",
            name="ck_facility_backstop_at_least_business_days",
        ),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contract_id", name="uq_facility_contract_id"),
        sa.UniqueConstraint("payment_reference", name="uq_facility_payment_reference"),
    )

    # --- schedule_version -----------------------------------------------
    op.create_table(
        "schedule_version",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("facility_id", UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("daily_amount_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("day_count", sa.Integer(), nullable=False),
        sa.Column("remainder_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("final_instalment_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint("daily_amount_vnd > 0", name="ck_schedule_version_daily_amount_positive"),
        sa.CheckConstraint("day_count > 0", name="ck_schedule_version_day_count_positive"),
        sa.CheckConstraint("remainder_vnd >= 0", name="ck_schedule_version_remainder_non_negative"),
        sa.CheckConstraint("final_instalment_vnd > 0", name="ck_schedule_version_final_instalment_positive"),
        sa.ForeignKeyConstraint(["facility_id"], ["facility.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("facility_id", "version_number", name="uq_schedule_version_facility_version"),
    )

    # --- scheduled_payment ------------------------------------------------
    op.create_table(
        "scheduled_payment",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("facility_id", UUID(as_uuid=True), nullable=False),
        sa.Column("schedule_version_id", UUID(as_uuid=True), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("expected_amount_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="PENDING"),
        sa.Column("satisfied_amount_vnd", sa.Numeric(20, 0), nullable=False, server_default="0"),
        sa.Column("satisfied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint(f"status IN {SCHEDULED_PAYMENT_STATUSES}", name="ck_scheduled_payment_status"),
        sa.CheckConstraint("day_index > 0", name="ck_scheduled_payment_day_index_positive"),
        sa.CheckConstraint("expected_amount_vnd > 0", name="ck_scheduled_payment_expected_amount_positive"),
        sa.CheckConstraint("satisfied_amount_vnd >= 0", name="ck_scheduled_payment_satisfied_amount_non_negative"),
        sa.ForeignKeyConstraint(["facility_id"], ["facility.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["schedule_version_id"], ["schedule_version.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # INV-6: no two scheduled payments on the same facility share a date.
        sa.UniqueConstraint("facility_id", "scheduled_date", name="uq_scheduled_payment_facility_date"),
        sa.UniqueConstraint("facility_id", "day_index", name="uq_scheduled_payment_facility_day_index"),
    )

    # --- inbound_transfer -------------------------------------------------
    op.create_table(
        "inbound_transfer",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("facility_id", UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("external_transaction_id", sa.Text(), nullable=False),
        sa.Column("bank_reference", sa.Text(), nullable=False),
        sa.Column("amount_vnd", sa.Numeric(20, 0), nullable=False),
        sa.Column("value_date", sa.Date(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="UNMATCHED"),
        sa.Column("attributed_by", UUID(as_uuid=True), nullable=True),
        sa.Column("attributed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint(f"status IN {INBOUND_TRANSFER_STATUSES}", name="ck_inbound_transfer_status"),
        sa.CheckConstraint("amount_vnd > 0", name="ck_inbound_transfer_amount_positive"),
        sa.ForeignKeyConstraint(["facility_id"], ["facility.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["attributed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        # INV-12/EC-18: DB-level idempotency on the bank's own natural key --
        # re-importing the same statement line must not create a second row.
        sa.UniqueConstraint("external_transaction_id", name="uq_inbound_transfer_external_transaction_id"),
    )

    # --- state_transition (append-only) ------------------------------------
    op.create_table(
        "state_transition",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("facility_id", UUID(as_uuid=True), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=False),
        sa.Column("trigger", sa.Text(), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", JSONB(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint(f"to_status IN {FACILITY_STATES}", name="ck_state_transition_to_status"),
        sa.CheckConstraint(
            f"from_status IS NULL OR from_status IN {FACILITY_STATES}", name="ck_state_transition_from_status"
        ),
        sa.ForeignKeyConstraint(["facility_id"], ["facility.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- append-only guarantee on state_transition (mirrors ADR-002) -------
    # Reuses ledger_immutability_guard() (created by 862160bce972) rather
    # than defining a second, identical trigger function.
    op.execute(
        """
        CREATE TRIGGER trg_state_transition_append_only
        BEFORE UPDATE OR DELETE ON state_transition
        FOR EACH ROW EXECUTE FUNCTION ledger_immutability_guard();
        """
    )

    # --- facility.backstop_day_index immutability (INV-10) -----------------
    # Column-level, not row-level: status, arrears_balance_vnd, etc. must
    # stay mutable, so this cannot reuse the whole-row append-only guard
    # above. Allows NULL -> value exactly once; rejects any further change.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION facility_backstop_day_index_immutable_guard()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.backstop_day_index IS NOT NULL
               AND NEW.backstop_day_index IS DISTINCT FROM OLD.backstop_day_index THEN
                RAISE EXCEPTION
                    'facility.backstop_day_index is immutable once set (INV-10): % -> %',
                    OLD.backstop_day_index, NEW.backstop_day_index;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_facility_backstop_day_index_immutable
        BEFORE UPDATE ON facility
        FOR EACH ROW EXECUTE FUNCTION facility_backstop_day_index_immutable_guard();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_facility_backstop_day_index_immutable ON facility;")
    op.execute("DROP FUNCTION IF EXISTS facility_backstop_day_index_immutable_guard();")
    op.execute("DROP TRIGGER IF EXISTS trg_state_transition_append_only ON state_transition;")

    op.drop_table("state_transition")
    op.drop_table("inbound_transfer")
    op.drop_table("scheduled_payment")
    op.drop_table("schedule_version")
    op.drop_table("facility")
