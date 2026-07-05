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

RAW_URL="$DATABASE_URL"
BARE_URL=$(printf '%s' "$RAW_URL" | sed -E 's#^postgresql\+(asyncpg|psycopg2)#postgresql#')
SYNC_URL=$(printf '%s' "$BARE_URL" | sed -E 's#^postgresql#postgresql+psycopg2#')
ASYNC_URL=$(printf '%s' "$BARE_URL" | sed -E 's#^postgresql#postgresql+asyncpg#')

echo "[entrypoint] Running database migrations (alembic upgrade head)..."
DATABASE_URL="$SYNC_URL" alembic upgrade head

echo "[entrypoint] Starting API server on port ${PORT:-8080}..."
export DATABASE_URL="$ASYNC_URL"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
