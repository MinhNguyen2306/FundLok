"""add session metadata to refresh_tokens

Powers the "signed-in devices" panel on /dashboard/security. A refresh token
row is already one live sign-in, but it rotates on every refresh (the old row
is revoked and a new one inserted), so a device needs an identifier that
survives rotation -- hence session_id, carried forward by the rotation.

user_agent / ip_address / last_used_at are what makes the row legible to a
human deciding whether to revoke it.

Revision ID: a3f7c92e1b48
Revises: d5a8c31f6b02
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a3f7c92e1b48'
down_revision: Union[str, None] = 'd5a8c31f6b02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # All nullable: existing rows predate the columns, and a session issued
    # before this migration has no metadata to backfill. The API reports those
    # as an unknown device rather than inventing one.
    op.add_column(
        'refresh_tokens',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column('refresh_tokens', sa.Column('user_agent', sa.Text(), nullable=True))
    op.add_column('refresh_tokens', sa.Column('ip_address', sa.Text(), nullable=True))
    op.add_column(
        'refresh_tokens',
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    )
    # The sessions list filters by user and orders by recency; the session
    # lookup goes straight to session_id.
    op.create_index(
        'ix_refresh_tokens_session_id', 'refresh_tokens', ['session_id']
    )


def downgrade() -> None:
    op.drop_index('ix_refresh_tokens_session_id', table_name='refresh_tokens')
    op.drop_column('refresh_tokens', 'last_used_at')
    op.drop_column('refresh_tokens', 'ip_address')
    op.drop_column('refresh_tokens', 'user_agent')
    op.drop_column('refresh_tokens', 'session_id')
