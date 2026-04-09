#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f ".env" ]]; then
  echo "Missing .env. Create it from .env.example:"
  echo "  cp .env.example .env"
  exit 1
fi

set -a
source .env
set +a

TEST_DB="${TEST_DATABASE_NAME:-flashsale_test}"

docker compose up -d db redis

# Create test database inside the Postgres container (idempotent)
docker exec -i "$(docker compose ps -q db)" psql -U "${POSTGRES_USER:-flashsale}" -d postgres -tc \
  "SELECT 1 FROM pg_database WHERE datname = '${TEST_DB}'" | grep -q 1 || \
  docker exec -i "$(docker compose ps -q db)" psql -U "${POSTGRES_USER:-flashsale}" -d postgres -c \
  "CREATE DATABASE ${TEST_DB} OWNER ${POSTGRES_USER:-flashsale}"

docker run --rm \
  --network "$(basename "$(pwd)")_default" \
  -v "$(pwd)":/app \
  -w /app \
  -e DATABASE_URL="postgresql+psycopg2://${POSTGRES_USER:-flashsale}:${POSTGRES_PASSWORD:-flashsale}@db:5432/${TEST_DB}" \
  python:3.12-slim \
  bash -lc "apt-get update -qq && apt-get install -y -qq libpq-dev gcc >/dev/null && pip install -q -r requirements.txt && pytest -q"
