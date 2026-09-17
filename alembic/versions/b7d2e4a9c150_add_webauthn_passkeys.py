"""add webauthn_credentials and webauthn_challenges

Passkey support. Two tables:

  webauthn_credentials — one row per registered authenticator. Holds only
    public material; a passkey's private half never leaves the device, so
    unlike users.totp_secret beside it there is nothing here to encrypt.

  webauthn_challenges — pending ceremonies. WebAuthn requires a challenge to be
    random, short-lived AND single-use; the third property is why these are
    rows that get consumed rather than stateless signed tokens.

Revision ID: b7d2e4a9c150
Revises: a4f7c2e91b38
Create Date: 2026-09-13

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "b7d2e4a9c150"
down_revision = "a4f7c2e91b38"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "webauthn_credentials",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("credential_id", sa.Text(), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("device_type", sa.Text(), nullable=True),
        sa.Column("backed_up", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("transports", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False, server_default="Passkey"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_webauthn_credentials_user_id", "webauthn_credentials", ["user_id"]
    )
    # Unique, not merely indexed: an authenticator must never be silently
    # re-bound to a second account.
    op.create_index(
        "ix_webauthn_credentials_credential_id",
        "webauthn_credentials",
        ["credential_id"],
        unique=True,
    )

    op.create_table(
        "webauthn_challenges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("challenge", sa.Text(), nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_webauthn_challenges_challenge",
        "webauthn_challenges",
        ["challenge"],
        unique=True,
    )
    op.create_index("ix_webauthn_challenges_user_id", "webauthn_challenges", ["user_id"])


def downgrade() -> None:
    op.drop_table("webauthn_challenges")
    op.drop_table("webauthn_credentials")
