from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.base import Base  # re-exported for existing `from app.core.database import Base` imports
from app.core.config import settings

# NOTE (HANDOFF-02 Fix A): this is now the ASYNC app URL (postgresql+asyncpg://).
# Alembic keeps its own sync URL (postgresql+psycopg2://) in alembic/env.py --
# two URLs, one for migrations, one for the app, set independently per
# environment/CI job. Do not point this at a psycopg2 URL.
#
# Base lives in app.core.base, not here, specifically so that importing Base
# (which is all Alembic needs) never has the side effect of constructing this
# async engine -- see app/core/base.py docstring.
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

# expire_on_commit=False: without it, attribute access on a committed object
# after the request handler returns (e.g. during response serialization)
# would trigger implicit lazy IO, which is not allowed on an AsyncSession
# outside of an explicit await.
SessionLocal = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as db:
        yield db
