"""add SYSTEM_ADMIN role and system_settings table

Revision ID: e1a2b3c4d5e6
Revises: b7e3f1a2c9d4
Create Date: 2026-06-22 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, None] = "b7e3f1a2c9d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Allow the new SYSTEM_ADMIN role.
    op.drop_constraint("users_role_check", "users", type_="check")
    op.create_check_constraint(
        "users_role_check",
        "users",
        "role IN ('SME', 'INVESTOR', 'ADMIN', 'SYSTEM_ADMIN')",
    )

    # 2. Global key-value settings store (maintenance mode, etc.).
    op.create_table(
        "system_settings",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_constraint("users_role_check", "users", type_="check")
    op.create_check_constraint(
        "users_role_check",
        "users",
        "role IN ('SME', 'INVESTOR', 'ADMIN')",
    )
