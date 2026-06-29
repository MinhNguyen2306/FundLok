"""add verifications tables (Didit KYC/KYB integration)

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
        "verifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # "KYC" (investors) or "KYB" (SMEs). One table backs both flows.
        sa.Column(
            "verification_type",
            sa.Text(),
            nullable=False,
            server_default="KYC",
        ),
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
    )
    op.create_index("ix_verifications_user_id", "verifications", ["user_id"])
    op.create_index(
        "ix_verifications_verification_type", "verifications", ["verification_type"]
    )
    # unique=True matches the model's `Column(..., unique=True, index=True)`,
    # which SQLAlchemy expresses as a single unique index (not a separate
    # UniqueConstraint). Keeps `alembic check` clean.
    op.create_index(
        "ix_verifications_session_id",
        "verifications",
        ["session_id"],
        unique=True,
    )

    # Idempotency ledger for Didit webhook deliveries (dedupe on event_id).
    op.create_table(
        "verification_webhook_events",
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
        "ix_verification_webhook_events_session_id",
        "verification_webhook_events",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_verification_webhook_events_session_id",
        table_name="verification_webhook_events",
    )
    op.drop_table("verification_webhook_events")
    op.drop_index("ix_verifications_session_id", table_name="verifications")
    op.drop_index("ix_verifications_verification_type", table_name="verifications")
    op.drop_index("ix_verifications_user_id", table_name="verifications")
    op.drop_table("verifications")
