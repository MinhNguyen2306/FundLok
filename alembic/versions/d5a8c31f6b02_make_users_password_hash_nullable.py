"""make users.password_hash nullable (OAuth accounts have no password)

Revision ID: d5a8c31f6b02
Revises: c9f2a71b83e4
Create Date: 2026-08-09 09:45:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5a8c31f6b02"
down_revision: Union[str, None] = "c9f2a71b83e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # An account created through OAuth sign-in has no password, so the column
    # has to be able to say so. Until this, "passwordless user" was not a state
    # the database could represent at all, which made POST /users/me/password
    # (set a first password) permanently unreachable.
    #
    # Anything that reads password_hash must now handle NULL --
    # app.auth.service.authenticate_user rejects a password login outright when
    # there is no hash, rather than handing None to passlib.
    op.alter_column("users", "password_hash", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    # Rows with no password can't satisfy NOT NULL and there is no sensible
    # backfill -- inventing a hash would create an account nobody can log into
    # but which also can't be recovered. Deleting real users to satisfy a
    # downgrade is worse. Fail loudly and let an operator decide.
    conn = op.get_bind()
    passwordless = conn.execute(
        sa.text("SELECT count(*) FROM users WHERE password_hash IS NULL")
    ).scalar_one()
    if passwordless:
        raise RuntimeError(
            f"{passwordless} user(s) have no password_hash. Downgrading would "
            "require inventing or deleting credentials -- resolve those rows "
            "manually first."
        )
    op.alter_column("users", "password_hash", existing_type=sa.String(), nullable=False)
