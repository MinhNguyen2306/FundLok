"""Ledger double-entry foundation (ADR-002, ADR-003).

Introduces custodial_accounts + ledger_accounts (ADR-003 omnibus/escrow
seam) and ledger_transactions (idempotent event header), and turns
ledger_entries into the postings table of a double-entry system:
  - adds ledger_transaction_id, debit_account_id, credit_account_id
    (NOT NULL -- no ledger rows exist yet, see spec Open Question #4)
  - drops idempotency_key (moved to ledger_transactions, event-level)
  - adds amount > 0 / debit <> credit CHECK constraints
  - extends the type CHECK with FUNDING and REFUND

Also adds the DB-level append-only guarantee (ADR-002): a BEFORE
UPDATE/DELETE trigger on ledger_entries and ledger_transactions that raises
an exception. Corrections are made by posting a new, reversing transaction,
never by mutating a row.

Seeds exactly one scope='PLATFORM' custodial account (the omnibus account).
Provisions the SUSPENSE ledger_accounts.account_type value only -- no
suspense handling/sweep logic (deferred per spec Open Question #2).

Spec: docs/specs/ledger/ledger-foundation.md (ACCEPTED v1.0)
ADRs: docs/adr/002-omnibus-brankas-architecture.md,
      docs/adr/003-omnibus-first-escrow-compatible-ledger.md

Revision ID: 862160bce972
Revises: a7c4f1e2d3b5
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "862160bce972"
down_revision: Union[str, None] = "a7c4f1e2d3b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LEDGER_ENTRIES_OLD_TYPE_CHECK = "ledger_entries_type_check"


def upgrade() -> None:
    # --- custodial_accounts (ADR-003) ------------------------------------
    op.create_table(
        "custodial_accounts",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("contract_id", UUID(as_uuid=True), nullable=True),
        sa.Column("bank_account_ref", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint("scope IN ('PLATFORM', 'CONTRACT')", name="ck_custodial_accounts_scope"),
        sa.CheckConstraint(
            "(scope = 'PLATFORM' AND contract_id IS NULL) OR (scope = 'CONTRACT' AND contract_id IS NOT NULL)",
            name="ck_custodial_accounts_scope_contract",
        ),
        sa.CheckConstraint("status IN ('ACTIVE', 'CLOSED')", name="ck_custodial_accounts_status"),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Partial unique indexes: at most one PLATFORM row; one row per CONTRACT.
    op.create_index(
        "uq_single_platform_custodial",
        "custodial_accounts",
        ["scope"],
        unique=True,
        postgresql_where=sa.text("scope = 'PLATFORM'"),
    )
    op.create_index(
        "uq_custodial_accounts_contract_id",
        "custodial_accounts",
        ["contract_id"],
        unique=True,
        postgresql_where=sa.text("scope = 'CONTRACT'"),
    )

    # --- ledger_accounts (chart of accounts) ------------------------------
    op.create_table(
        "ledger_accounts",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("account_type", sa.Text(), nullable=False),
        sa.Column("custodial_account_id", UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("contract_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint(
            "account_type IN ('OMNIBUS_CASH', 'LENDER', 'BORROWER', 'FL_REVENUE', 'SUSPENSE')",
            name="ck_ledger_accounts_type",
        ),
        sa.ForeignKeyConstraint(["custodial_account_id"], ["custodial_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_type",
            "custodial_account_id",
            "owner_user_id",
            "contract_id",
            name="uq_ledger_accounts_role_party_contract",
        ),
    )

    # --- ledger_transactions (idempotent event header) --------------------
    op.create_table(
        "ledger_transactions",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("contract_id", UUID(as_uuid=True), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=True),
        sa.Column("reference", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )

    # --- ledger_entries: flat log -> double-entry postings table ----------
    op.add_column("ledger_entries", sa.Column("ledger_transaction_id", UUID(as_uuid=True), nullable=False))
    op.add_column("ledger_entries", sa.Column("debit_account_id", UUID(as_uuid=True), nullable=False))
    op.add_column("ledger_entries", sa.Column("credit_account_id", UUID(as_uuid=True), nullable=False))
    op.create_foreign_key(
        "fk_ledger_entries_ledger_transaction_id",
        "ledger_entries",
        "ledger_transactions",
        ["ledger_transaction_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_ledger_entries_debit_account_id",
        "ledger_entries",
        "ledger_accounts",
        ["debit_account_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_ledger_entries_credit_account_id",
        "ledger_entries",
        "ledger_accounts",
        ["credit_account_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # idempotency_key moves to ledger_transactions (event level); dropping
    # the column also drops its (unnamed, single-column) UNIQUE constraint.
    op.drop_column("ledger_entries", "idempotency_key")

    op.create_check_constraint("ck_ledger_entries_amount_positive", "ledger_entries", "amount > 0")
    op.create_check_constraint(
        "ck_ledger_entries_debit_ne_credit", "ledger_entries", "debit_account_id <> credit_account_id"
    )

    # type CHECK: add FUNDING and REFUND (regression: FUNDING wasn't even
    # representable before this migration).
    op.drop_constraint(LEDGER_ENTRIES_OLD_TYPE_CHECK, "ledger_entries", type_="check")
    op.create_check_constraint(
        LEDGER_ENTRIES_OLD_TYPE_CHECK,
        "ledger_entries",
        "type IN ('FUNDING', 'DISBURSEMENT', 'REPAYMENT', 'DISTRIBUTION', 'FEE', 'PENALTY', 'REFUND')",
    )

    # --- seed exactly one PLATFORM custodial account (omnibus, ADR-003) ---
    op.execute(
        "INSERT INTO custodial_accounts (id, scope, status) "
        "VALUES (gen_random_uuid(), 'PLATFORM', 'ACTIVE')"
    )

    # --- append-only guarantee (ADR-002): DB-level trigger -----------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION ledger_immutability_guard()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                '% on % is not allowed: the ledger is append-only. Post a reversing transaction instead.',
                TG_OP, TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_ledger_entries_append_only
        BEFORE UPDATE OR DELETE ON ledger_entries
        FOR EACH ROW EXECUTE FUNCTION ledger_immutability_guard();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_ledger_transactions_append_only
        BEFORE UPDATE OR DELETE ON ledger_transactions
        FOR EACH ROW EXECUTE FUNCTION ledger_immutability_guard();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_ledger_transactions_append_only ON ledger_transactions;")
    op.execute("DROP TRIGGER IF EXISTS trg_ledger_entries_append_only ON ledger_entries;")
    op.execute("DROP FUNCTION IF EXISTS ledger_immutability_guard();")

    op.drop_constraint(LEDGER_ENTRIES_OLD_TYPE_CHECK, "ledger_entries", type_="check")
    op.create_check_constraint(
        LEDGER_ENTRIES_OLD_TYPE_CHECK,
        "ledger_entries",
        "type IN ('DISBURSEMENT', 'REPAYMENT', 'DISTRIBUTION', 'FEE', 'PENALTY')",
    )

    op.drop_constraint("ck_ledger_entries_debit_ne_credit", "ledger_entries", type_="check")
    op.drop_constraint("ck_ledger_entries_amount_positive", "ledger_entries", type_="check")

    op.add_column("ledger_entries", sa.Column("idempotency_key", sa.Text(), nullable=True))
    op.create_unique_constraint("ledger_entries_idempotency_key_key", "ledger_entries", ["idempotency_key"])

    op.drop_constraint("fk_ledger_entries_credit_account_id", "ledger_entries", type_="foreignkey")
    op.drop_constraint("fk_ledger_entries_debit_account_id", "ledger_entries", type_="foreignkey")
    op.drop_constraint("fk_ledger_entries_ledger_transaction_id", "ledger_entries", type_="foreignkey")
    op.drop_column("ledger_entries", "credit_account_id")
    op.drop_column("ledger_entries", "debit_account_id")
    op.drop_column("ledger_entries", "ledger_transaction_id")

    op.drop_table("ledger_transactions")
    op.drop_table("ledger_accounts")

    op.drop_index("uq_custodial_accounts_contract_id", table_name="custodial_accounts")
    op.drop_index("uq_single_platform_custodial", table_name="custodial_accounts")
    op.drop_table("custodial_accounts")
