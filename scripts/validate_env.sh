#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env}"
MODE="${2:-development}" # development | production

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[error] $ENV_FILE not found"
  exit 1
fi

required_keys=(
  APP_ENV
  API_PORT
  DATABASE_URL
  POSTGRES_PASSWORD
)

for key in "${required_keys[@]}"; do
  if ! grep -Eq "^${key}=" "$ENV_FILE"; then
    echo "[error] missing key: $key"
    exit 1
  fi

done

# 값이 비어있지 않은지 검증
for key in "${required_keys[@]}"; do
  value="$(grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d'=' -f2-)"
  if [[ -z "${value// }" ]]; then
    echo "[error] empty value: $key"
    exit 1
  fi
done

if [[ "$MODE" == "production" ]]; then
  placeholders=(
    "POSTGRES_PASSWORD=__REPLACE_WITH_STRONG_PASSWORD__"
    "AI_API_KEY=__SET_LOCALLY__"
  )

  for p in "${placeholders[@]}"; do
    if grep -q "^${p}$" "$ENV_FILE"; then
      echo "[error] placeholder detected in production env: $p"
      exit 1
    fi
  done
fi

echo "[ok] env validation passed ($ENV_FILE, mode=$MODE)"
