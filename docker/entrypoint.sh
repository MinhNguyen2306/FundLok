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

# Reduce DATABASE_URL to the bare connection (creds + host + db), discarding BOTH
# the driver and ANY query string. This makes the entrypoint robust to whatever
# format the secret is in — psycopg2, asyncpg, bare, with or without ssl params.
RAW_URL="$DATABASE_URL"
NODRIVER=$(printf '%s' "$RAW_URL" | sed -E 's#^postgresql(\+[a-z0-9_]+)?://#postgresql://#')
BASE_NOQUERY=$(printf '%s' "$NODRIVER" | sed -E 's#\?.*$##')
CONN=$(printf '%s' "$BASE_NOQUERY" | sed -E 's#^postgresql://##')

# Rebuild the correct URL for each tool from CONN, with driver-appropriate params.
# We do NOT reuse the secret's query string, because sslmode/channel_binding are
# libpq-only (psycopg2) and ssl/prepared_statement_cache_size are asyncpg-only —
# feeding one tool the other's params is what breaks the deploy.
#   Alembic → sync psycopg2 (libpq): sslmode=require
#   App     → async asyncpg: ssl=require + pooler-safe prepared_statement_cache_size=0
# (Neon always requires SSL, and this container only ever connects to Neon.)
SYNC_URL="postgresql+psycopg2://${CONN}?sslmode=require"
ASYNC_URL="postgresql+asyncpg://${CONN}?ssl=require&prepared_statement_cache_size=0"

echo "[entrypoint] Running database migrations (alembic upgrade head)..."
DATABASE_URL="$SYNC_URL" alembic upgrade head

echo "[entrypoint] Starting API server on port ${PORT:-8080}..."
export DATABASE_URL="$ASYNC_URL"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
