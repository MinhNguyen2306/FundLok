"""Initial FundLok schema (aligned with DDL + refresh_tokens + idempotency).

Revision ID: 0001
Revises:
Create Date: 2025-03-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint("role IN ('SME', 'INVESTOR', 'ADMIN')", name="users_role_check"),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'PENDING_KYC', 'SUSPENDED', 'REJECTED')", name="users_status_check"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("legal_name", sa.Text(), nullable=False),
        sa.Column("tax_id", sa.Text(), nullable=True),
        sa.Column("industry", sa.Text(), nullable=True),
        sa.Column("address", JSONB(), nullable=True),
        sa.Column("incorporation_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Text(), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'ARCHIVED', 'SUSPENDED', 'CLOSED')", name="projects_status_check"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tax_id"),
    )

    op.create_table(
        "project_ownerships",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Text(), server_default="OWNER", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint(
            "role IN ('OWNER', 'FINANCE', 'VIEWER', 'AUDITOR')", name="project_ownerships_role_check"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_ownership_project_user"),
    )

    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), server_default="PENDING", nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("checksum_sha256", sa.Text(), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("metadata", JSONB(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint(
            "entity_type IN ('USER', 'PROJECT')", name="documents_entity_type_check"
        ),
        sa.CheckConstraint(
            "purpose IN ('KYC_ID', 'KYC_ADDRESS', 'KYC_BUSINESS_REG', 'BANK_STATEMENT', 'INVOICE', 'OTHER')",
            name="documents_purpose_check",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'UPLOADED', 'SCANNING', 'APPROVED', 'REJECTED', 'FAILED')",
            name="documents_status_check",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_documents_entity", "documents", ["entity_type", "entity_id"], unique=False)
    op.create_index("idx_documents_purpose", "documents", ["purpose", "status"], unique=False)

    op.create_table(
        "loan_applications",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("requested_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("repayment_preference", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), server_default="DRAFT", nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint("requested_amount > 0", name="loan_applications_amount_check"),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED')",
            name="loan_applications_status_check",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "application_documents",
        sa.Column("application_id", UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["loan_applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("application_id", "document_id"),
    )

    op.create_table(
        "score_runs",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Text(), server_default="RUNNING", nullable=False),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("risk_grade", sa.Text(), nullable=True),
        sa.Column("recommended_terms", JSONB(), nullable=True),
        sa.Column("factor_results", JSONB(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint(
            "status IN ('RUNNING', 'READY', 'LOCKED', 'FAILED')", name="score_runs_status_check"
        ),
        sa.ForeignKeyConstraint(["application_id"], ["loan_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "contracts",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", UUID(as_uuid=True), nullable=True),
        sa.Column("score_run_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text(), server_default="DRAFT", nullable=False),
        sa.Column("final_terms", JSONB(), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("funded_amount", sa.Numeric(15, 2), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint("target_amount > 0", name="contracts_target_check"),
        sa.CheckConstraint("funded_amount >= 0", name="contracts_funded_check"),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SIGNED', 'ACTIVE_PENDING_FUNDING', 'ACTIVE_FUNDED', 'CLOSED', 'DEFAULTED')",
            name="contracts_status_check",
        ),
        sa.ForeignKeyConstraint(["application_id"], ["loan_applications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["score_run_id"], ["score_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "listings",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contract_id", UUID(as_uuid=True), nullable=False),
        sa.Column("target_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("min_ticket", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.Text(), server_default="DRAFT", nullable=False),
        sa.Column("funded_amount", sa.Numeric(15, 2), server_default="0", nullable=False),
        sa.Column("open_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("close_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'OPEN', 'FUNDED', 'CLOSED', 'CANCELLED')", name="listings_status_check"
        ),
        sa.CheckConstraint("min_ticket IS NULL OR min_ticket > 0", name="listings_min_ticket_check"),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contract_id"),
    )

    op.create_table(
        "orders",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("listing_id", UUID(as_uuid=True), nullable=False),
        sa.Column("investor_id", UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("status", sa.Text(), server_default="PENDING_PAYMENT", nullable=False),
        sa.Column("payment_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint("amount > 0", name="orders_amount_check"),
        sa.CheckConstraint(
            "status IN ('PENDING_PAYMENT', 'FILLED', 'CANCELLED', 'EXPIRED')", name="orders_status_check"
        ),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["investor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )

    op.create_table(
        "holdings",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contract_id", UUID(as_uuid=True), nullable=False),
        sa.Column("investor_id", UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", UUID(as_uuid=True), nullable=True),
        sa.Column("principal", sa.Numeric(15, 2), nullable=False),
        sa.Column("share_ratio", sa.Numeric(10, 8), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint("principal > 0", name="holdings_principal_check"),
        sa.CheckConstraint(
            "share_ratio IS NULL OR (share_ratio >= 0 AND share_ratio <= 1)", name="holdings_share_ratio_check"
        ),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["investor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contract_id", "investor_id", name="uq_holding_contract_investor"),
    )

    op.create_table(
        "ledger_entries",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contract_id", UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("reference", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "type IN ('DISBURSEMENT', 'REPAYMENT', 'DISTRIBUTION', 'FEE', 'PENALTY')",
            name="ledger_entries_type_check",
        ),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), nullable=True),
        sa.Column("before_state", JSONB(), nullable=True),
        sa.Column("after_state", JSONB(), nullable=True),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("ledger_entries")
    op.drop_table("holdings")
    op.drop_table("orders")
    op.drop_table("listings")
    op.drop_table("contracts")
    op.drop_table("score_runs")
    op.drop_table("application_documents")
    op.drop_table("loan_applications")
    op.drop_index("idx_documents_purpose", table_name="documents")
    op.drop_index("idx_documents_entity", table_name="documents")
    op.drop_table("documents")
    op.drop_table("project_ownerships")
    op.drop_table("projects")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
