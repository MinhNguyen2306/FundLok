"""Regression test for a bug in 5ed837b145f0_add_full_name_to_users.py's
downgrade(): it called `op.drop_constraint(None, 'refresh_tokens',
type_='unique')`, which can't compile (DROP CONSTRAINT needs a real name --
unlike CREATE CONSTRAINT, where None lets Postgres auto-name it). That made
a *full* `alembic downgrade base` fail every time, independent of any other
migration in the chain.

Fixed by naming the actual constraint Postgres auto-generated in upgrade()
('refresh_tokens_token_hash_key'). This test proves the whole chain now
reverses cleanly from head all the way down to nothing, and back up again.

Runs against its own throwaway database (never the shared `test_db` the
rest of the suite uses via conftest's session-scoped `_migrate_schema`
fixture) so it can't affect their state.
"""
import os
import subprocess

import psycopg2
from sqlalchemy.engine import make_url

from conftest import ALEMBIC_DATABASE_URL, ROOT

FULL_DOWNGRADE_CHECK_DB = "test_db_full_downgrade_check"


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


def test_migration_full_downgrade_to_base_and_back_up_is_clean():
    admin_conn = psycopg2.connect(**_admin_connect_kwargs())
    admin_conn.autocommit = True
    try:
        with admin_conn.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{FULL_DOWNGRADE_CHECK_DB}"')
            cur.execute(f'CREATE DATABASE "{FULL_DOWNGRADE_CHECK_DB}"')

        base_url = make_url(ALEMBIC_DATABASE_URL)
        # Plain string substitution of the database name, not
        # make_url(...).set(database=...): the latter round-trips through
        # sqlalchemy's URL serializer and percent-encodes query-string
        # values (e.g. a unix-socket `host=/tmp/...` param), which then
        # trips ConfigParser's interpolation syntax in
        # Config.set_main_option (alembic/env.py).
        migration_url = ALEMBIC_DATABASE_URL.replace(f"/{base_url.database}", f"/{FULL_DOWNGRADE_CHECK_DB}", 1)
        env = {**os.environ, "DATABASE_URL": migration_url}

        def run(*args):
            result = subprocess.run(["alembic", *args], cwd=str(ROOT), env=env, capture_output=True, text=True)
            assert result.returncode == 0, f"alembic {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}"
            return result

        run("upgrade", "head")
        run("check")
        # The actual regression: this used to fail partway through on
        # 5ed837b145f0's downgrade(), independent of anything else.
        run("downgrade", "base")
        run("upgrade", "head")
        run("check")
    finally:
        with admin_conn.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{FULL_DOWNGRADE_CHECK_DB}"')
        admin_conn.close()
