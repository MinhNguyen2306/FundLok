"""spec §8: `alembic upgrade head` then `downgrade` runs clean; `alembic
check` passes.

Runs against its own throwaway database (never the shared `test_db` the
rest of the suite uses via conftest's session-scoped `_migrate_schema`
fixture) so a downgrade here can't leave any other test without a schema.
"""
import os

import psycopg2
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.engine import make_url

from conftest import ALEMBIC_COMMAND, ALEMBIC_DATABASE_URL, ROOT


def _one_step_back_from_head() -> str:
    """The explicit downgrade target equivalent to "-1" from whatever the
    current head happens to be.

    Plain `alembic downgrade -1` only works when the head has a single
    parent. The moment the head is a *merge* revision (down_revision is a
    tuple of two-or-more parents -- e.g. after reconciling two branches that
    each added migrations, as HANDOFF-03's ledger/scoring chain and main's
    auth/lite-grading chain did), "one step back" is structurally ambiguous
    -- which parent's branch would it even mean? -- and alembic refuses with
    "Ambiguous walk" rather than guess. This resolves the real target
    directly from the script graph instead of hardcoding today's specific
    revision id, so the test keeps working the same way after the next
    ordinary (non-merge) migration lands, and after any future merge too.
    """
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    script = ScriptDirectory.from_config(config)
    (head,) = script.get_heads()
    down_revision = script.get_revision(head).down_revision
    if isinstance(down_revision, tuple):
        # A merge revision: land on one parent specifically, not "both at
        # once" (alembic_version holding two rows) -- the point of this test
        # is a clean, ordinary upgrade/downgrade/upgrade cycle, not exercising
        # the separate multi-head-tracking machinery.
        return down_revision[0]
    return down_revision

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
            result = subprocess.run([*ALEMBIC_COMMAND, *args], cwd=str(ROOT), env=env, capture_output=True, text=True)
            assert result.returncode == 0, f"{' '.join(ALEMBIC_COMMAND + list(args))} failed:\n{result.stdout}\n{result.stderr}"
            return result

        run("upgrade", "head")
        run("check")
        # Downgrade *this* migration (one step back from head), not all the
        # way to `base`: an unrelated, already-merged, frozen migration
        # (5ed837b145f0_add_full_name_to_users.py) has a pre-existing
        # `op.drop_constraint(None, "refresh_tokens", type_="unique")` in
        # its downgrade() -- an unnamed constraint alembic can't compile a
        # DROP for -- so a *full* chain downgrade to base already fails
        # today, independent of anything in this PR. Per CLAUDE.md, the
        # migration history is frozen (never alter existing migrations);
        # flagged in the PR description for separate triage. "downgrade"
        # in the spec/task means this migration's own revert, which is
        # what's exercised here.
        #
        # Plain relative "-1" only works when head has a single parent; see
        # _one_step_back_from_head's docstring for why an explicit target is
        # required once head is a merge revision (as it is right now, after
        # reconciling two independently-extended migration chains).
        run("downgrade", _one_step_back_from_head())
        run("upgrade", "head")
        run("check")
    finally:
        with admin_conn.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{MIGRATION_CHECK_DB}"')
        admin_conn.close()
