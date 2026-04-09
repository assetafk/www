#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f ".env" ]]; then
  echo "Missing .env. Create it from .env.example:"
  echo "  cp .env.example .env"
  exit 1
fi

docker compose up -d --build
echo "API: http://localhost:8000/health"
