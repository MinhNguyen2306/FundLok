"""Declarative base, split out from app.core.database (HANDOFF-02 Fix A).

Alembic only ever needs `Base.metadata` for autogenerate/check, and must stay
on a sync driver (see alembic/env.py). Keeping Base in its own module means
importing it doesn't also trigger `create_async_engine(...)` against
whatever DATABASE_URL alembic is given -- which would blow up immediately
since alembic's URL uses the sync psycopg2 driver.
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
