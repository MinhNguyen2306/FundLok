#!/usr/bin/env bash
# Run the test suite entirely in Docker, mirroring the CI "Run Test Suite" job
# (.github/workflows/ci.yml): a throwaway postgres:15 + python:3.11 that runs
# `alembic upgrade head` (psycopg2) then pytest (asyncpg). No local venv and no
# published ports, so it never conflicts with the dev compose stack on :5433.
#
# Usage:
#   bun run docker:test                    # whole suite (tests/ -q)
#   bun run docker:test tests/auth -q     # any pytest args pass through
set -euo pipefail
cd "$(dirname "$0")/.."

NETWORK=fundlok-test
PG_CONTAINER=fundlok-test-pg
PIP_CACHE_VOLUME=fundlok-test-pip-cache
PG_URL_SYNC="postgresql+psycopg2://test_user:test_password@${PG_CONTAINER}:5432/test_db"
PG_URL_ASYNC="postgresql+asyncpg://test_user:test_password@${PG_CONTAINER}:5432/test_db"

PYTEST_ARGS=("$@")
if [ ${#PYTEST_ARGS[@]} -eq 0 ]; then
  PYTEST_ARGS=(tests/ -q)
fi

cleanup() {
  docker rm -f "$PG_CONTAINER" >/dev/null 2>&1 || true
  docker network rm "$NETWORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT
cleanup  # clear leftovers from an interrupted previous run

docker network create "$NETWORK" >/dev/null
docker run -d --name "$PG_CONTAINER" --network "$NETWORK" \
  -e POSTGRES_USER=test_user \
  -e POSTGRES_PASSWORD=test_password \
  -e POSTGRES_DB=test_db \
  postgres:15 >/dev/null

echo "Waiting for postgres..."
for _ in $(seq 1 30); do
  if docker exec "$PG_CONTAINER" pg_isready -U test_user -d test_db >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

# The named volume caches pip downloads so reruns skip the ~2 min install.
docker run --rm --network "$NETWORK" \
  -v "$PWD":/work -w /work \
  -v "$PIP_CACHE_VOLUME":/root/.cache/pip \
  -e SECRET_KEY=dummy_secret_key_for_testing \
  -e DEBUG=True \
  python:3.11 bash -c "
    pip install -q -r requirements.txt &&
    DATABASE_URL='$PG_URL_SYNC' alembic upgrade head &&
    DATABASE_URL='$PG_URL_ASYNC' python -m pytest ${PYTEST_ARGS[*]}
  "
