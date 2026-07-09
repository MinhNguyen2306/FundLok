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

# Cloud SQL unix-socket URLs (staging) carry the real "host" in the query
# string: postgresql://user:pass@/db?host=/cloudsql/PROJECT:REGION:INSTANCE.
# That parameter must survive the rewrite — dropping it leaves an empty host,
# libpq falls back to the container's local socket, and the boot dies with
# "Is the server running locally and accepting connections on that socket?".
SOCKET_HOST=$(printf '%s' "$RAW_URL" | sed -n -E 's#.*[?&]host=(/[^&]+).*#\1#p')

# Rebuild the correct URL for each tool from CONN, with driver-appropriate params.
# We do NOT reuse the secret's full query string, because sslmode/channel_binding
# are libpq-only (psycopg2) and ssl/prepared_statement_cache_size are asyncpg-only —
# feeding one tool the other's params is what breaks the deploy.
#   Alembic → sync psycopg2 (libpq)
#   App     → async asyncpg (pooler-safe prepared_statement_cache_size=0)
# Two connection shapes are supported:
#   TCP + TLS (Neon, prod):        force SSL on both drivers
#   Cloud SQL unix socket (staging): pass host=/cloudsql/... through, no SSL
#                                    (sockets are mounted by --add-cloudsql-instances)
if [ -n "$SOCKET_HOST" ]; then
  SYNC_URL="postgresql+psycopg2://${CONN}?host=${SOCKET_HOST}"
  ASYNC_URL="postgresql+asyncpg://${CONN}?host=${SOCKET_HOST}&prepared_statement_cache_size=0"
else
  SYNC_URL="postgresql+psycopg2://${CONN}?sslmode=require"
  ASYNC_URL="postgresql+asyncpg://${CONN}?ssl=require&prepared_statement_cache_size=0"
fi

echo "[entrypoint] Running database migrations (alembic upgrade head)..."
DATABASE_URL="$SYNC_URL" alembic upgrade head

echo "[entrypoint] Starting API server on port ${PORT:-8080}..."
export DATABASE_URL="$ASYNC_URL"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
