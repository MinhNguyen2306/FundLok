#!/usr/bin/env bash
# Reset the LOCAL dev database and reseed it.
#
#   - drops & recreates the `fundlok_dev` database (DESTROYS local data)
#   - re-enables the pgcrypto extension
#   - runs Alembic migrations to head (builds the full schema, incl. KYC tables)
#   - loads scripts/seed_data.sql (all users password: Password123!)
#
# Leaves minio/mailpit and their data untouched. Local dev only — never point
# DATABASE_URL at a remote DB and run this.
set -euo pipefail
cd "$(dirname "$0")/.."

DB_NAME="fundlok_dev"
DB_USER="fundlok"
ALEMBIC="alembic"
[ -x ./venv/bin/alembic ] && ALEMBIC="./venv/bin/alembic"

echo "[reset_db] Ensuring Postgres is up…"
docker compose up -d postgres >/dev/null

echo "[reset_db] Waiting for Postgres to be healthy…"
until [ "$(docker compose ps -q postgres | xargs docker inspect -f '{{.State.Health.Status}}' 2>/dev/null || true)" = "healthy" ]; do
  sleep 1
done

echo "[reset_db] Dropping & recreating database '$DB_NAME' (destroys local data)…"
docker compose exec -T postgres psql -U "$DB_USER" -d postgres \
  -c "DROP DATABASE IF EXISTS $DB_NAME WITH (FORCE);" \
  -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
docker compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" \
  -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"

echo "[reset_db] Applying migrations (alembic upgrade head)…"
"$ALEMBIC" upgrade head

echo "[reset_db] Seeding data…"
docker compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 < scripts/seed_data.sql

echo "[reset_db] Done. Schema at head + seeded. Login password: Password123!"
