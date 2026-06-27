"""add kyc_verifications table (Didit KYC integration)

Revision ID: a7c4f1e2d3b5
Revises: f2b3c4d5e6f7
Create Date: 2026-06-26 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a7c4f1e2d3b5"
down_revision: Union[str, None] = "f2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kyc_verifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("session_number", sa.Integer(), nullable=True),
        sa.Column("vendor_data", sa.Text(), nullable=True),
        sa.Column("workflow_id", sa.Text(), nullable=True),
        sa.Column("verification_url", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.Text(), nullable=False, server_default="Not Started"
        ),
        sa.Column("decision", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("session_id", name="uq_kyc_verifications_session_id"),
    )
    op.create_index(
        "ix_kyc_verifications_user_id", "kyc_verifications", ["user_id"]
    )
    op.create_index(
        "ix_kyc_verifications_session_id", "kyc_verifications", ["session_id"]
    )

    # Idempotency ledger for Didit webhook deliveries (dedupe on event_id).
    op.create_table(
        "kyc_webhook_events",
        sa.Column("event_id", sa.Text(), primary_key=True),
        sa.Column("session_id", sa.Text(), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_kyc_webhook_events_session_id", "kyc_webhook_events", ["session_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_kyc_webhook_events_session_id", table_name="kyc_webhook_events"
    )
    op.drop_table("kyc_webhook_events")
    op.drop_index("ix_kyc_verifications_session_id", table_name="kyc_verifications")
    op.drop_index("ix_kyc_verifications_user_id", table_name="kyc_verifications")
    op.drop_table("kyc_verifications")
