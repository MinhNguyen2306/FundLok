#!/usr/bin/env sh
# Container entrypoint: apply DB migrations, then start the API server.
#
# Running `alembic upgrade head` here means a deploy to Cloud Run automatically
# brings the database schema up to date. It is idempotent — a no-op when the DB
# is already at head — and Alembic takes a lock so parallel instance starts are
# safe.
#
# Driver split (matches CI): the app runs on async psycopg (postgresql+asyncpg),
# Alembic runs on sync psycopg2 (postgresql+psycopg2). Both read DATABASE_URL,
# but a single deployed value can only name one driver. So we derive both forms
# from whatever driver the secret provides and hand each tool the right one —
# otherwise one of the two crashes at startup and the container never listens
# on $PORT ("failed to start and listen on port 8080").
set -e

# Take whatever DATABASE_URL the deploy provides (any driver, any query) and
# reduce it to the bare connection (creds + host + db, no ?query).
RAW_URL="$DATABASE_URL"
BARE_URL=$(printf '%s' "$RAW_URL" | sed -E 's#^postgresql\+(asyncpg|psycopg2)#postgresql#')
BASE_NOQUERY=$(printf '%s' "$BARE_URL" | sed -E 's#\?.*$##')
CONN=$(printf '%s' "$BASE_NOQUERY" | sed -E 's#^postgresql://##')

# Alembic: sync psycopg2. libpq (psycopg2) understands the original query as-is
# (sslmode, channel_binding, ...), so keep it and just force the sync driver.
SYNC_URL=$(printf '%s' "$BARE_URL" | sed -E 's#^postgresql#postgresql+psycopg2#')

# App: async asyncpg. asyncpg does NOT accept libpq params (sslmode/channel_binding)
# — it uses ssl=... instead — and the Neon pooler (PgBouncer) needs prepared
# statements disabled. Keeping sslmode here is why /health (no DB) passed but real
# DB endpoints 500'd: asyncpg only connects on the first query. Rebuild the query
# with asyncpg-native params.
ASYNC_URL="postgresql+asyncpg://${CONN}?ssl=require&prepared_statement_cache_size=0"

echo "[entrypoint] Running database migrations (alembic upgrade head)..."
DATABASE_URL="$SYNC_URL" alembic upgrade head

echo "[entrypoint] Starting API server on port ${PORT:-8080}..."
export DATABASE_URL="$ASYNC_URL"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
