#!/usr/bin/env sh
# Container entrypoint: apply DB migrations, then start the API server.
#
# Running `alembic upgrade head` here means a deploy to Cloud Run automatically
# brings the database schema up to date. It is idempotent — a no-op when the DB
# is already at head — and Alembic takes a lock so parallel instance starts are
# safe. Migrations use settings.DATABASE_URL (see alembic/env.py), the same
# connection the app uses, so the Cloud SQL socket works without extra setup.
set -e

echo "[entrypoint] Running database migrations (alembic upgrade head)..."
alembic upgrade head

echo "[entrypoint] Starting API server on port ${PORT:-8080}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
