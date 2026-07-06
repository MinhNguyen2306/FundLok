"""spec §8: `alembic upgrade head` then `downgrade` runs clean; `alembic
check` passes.

Runs against its own throwaway database (never the shared `test_db` the
rest of the suite uses via conftest's session-scoped `_migrate_schema`
fixture) so a downgrade here can't leave any other test without a schema.
"""
import os

import psycopg2
import pytest
from sqlalchemy.engine import make_url

from conftest import ALEMBIC_DATABASE_URL, ROOT

MIGRATION_CHECK_DB = "test_db_migration_check"


def _admin_connect_kwargs():
    url = make_url(ALEMBIC_DATABASE_URL)
    kwargs = {"dbname": "postgres"}
    if url.username:
        kwargs["user"] = url.username
    if url.password:
        kwargs["password"] = url.password
    if url.host:
        kwargs["host"] = url.host
    if url.port:
        kwargs["port"] = url.port
    # Unix-socket-style DSNs (`postgresql+psycopg2://user:pass@/db?host=/tmp/x&port=1`)
    # carry host/port in the query string instead of the URL's host/port fields.
    kwargs.update(url.query or {})
    return kwargs


def test_migration_upgrade_and_downgrade_clean():
    import subprocess

    admin_conn = psycopg2.connect(**_admin_connect_kwargs())
    admin_conn.autocommit = True
    try:
        with admin_conn.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{MIGRATION_CHECK_DB}"')
            cur.execute(f'CREATE DATABASE "{MIGRATION_CHECK_DB}"')

        # Plain string substitution of the database name -- NOT
        # make_url(...).set(database=...), which round-trips through
        # sqlalchemy's URL serializer and percent-encodes query-string
        # values (e.g. a unix-socket `host=/tmp/...` param), which then
        # trips ConfigParser's interpolation syntax in
        # Config.set_main_option (alembic/env.py). A plain TCP DSN would
        # never hit this, but this keeps the test agnostic to which style
        # of DATABASE_URL it's given.
        base_url = make_url(ALEMBIC_DATABASE_URL)
        migration_url = ALEMBIC_DATABASE_URL.replace(f"/{base_url.database}", f"/{MIGRATION_CHECK_DB}", 1)
        env = {**os.environ, "DATABASE_URL": migration_url}

        def run(*args):
            result = subprocess.run(["alembic", *args], cwd=str(ROOT), env=env, capture_output=True, text=True)
            assert result.returncode == 0, f"alembic {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}"
            return result

        run("upgrade", "head")
        run("check")
        # Downgrade *this* migration (-1), not all the way to `base`: an
        # unrelated, already-merged, frozen migration
        # (5ed837b145f0_add_full_name_to_users.py) has a pre-existing
        # `op.drop_constraint(None, "refresh_tokens", type_="unique")` in
        # its downgrade() -- an unnamed constraint alembic can't compile a
        # DROP for -- so a *full* chain downgrade to base already fails
        # today, independent of anything in this PR. Per CLAUDE.md, the
        # migration history is frozen (never alter existing migrations);
        # flagged in the PR description for separate triage. "downgrade"
        # in the spec/task means this migration's own revert, which is
        # what's exercised here.
        run("downgrade", "-1")
        run("upgrade", "head")
        run("check")
    finally:
        with admin_conn.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{MIGRATION_CHECK_DB}"')
        admin_conn.close()
