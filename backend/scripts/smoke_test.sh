#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:18080}"
START_SERVER="${START_SERVER:-1}"

WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="/tmp/aiops_smoke_uvicorn.log"

SERVER_PID=""
cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" || true
  fi
}
trap cleanup EXIT

if [[ "${START_SERVER}" == "1" ]]; then
  cd "$WORKDIR"
  if [[ -x ".venv/bin/uvicorn" ]]; then
    .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 18080 >"$LOG_FILE" 2>&1 &
  else
    uvicorn app.main:app --host 127.0.0.1 --port 18080 >"$LOG_FILE" 2>&1 &
  fi
  SERVER_PID=$!
  sleep 2
fi

request() {
  local method=$1
  local path=$2
  local body=${3:-}

  local tmp
  tmp=$(mktemp)
  local code
  if [[ -n "$body" ]]; then
    code=$(curl -sS -o "$tmp" -w "%{http_code}" -X "$method" "$BASE_URL$path" -H "content-type: application/json" -d "$body")
  else
    code=$(curl -sS -o "$tmp" -w "%{http_code}" -X "$method" "$BASE_URL$path")
  fi

  local content
  content=$(cat "$tmp")
  rm -f "$tmp"

  printf "%s\n%s" "$code" "$content"
}

assert_contains() {
  local haystack=$1
  local needle=$2
  if [[ "$haystack" != *"$needle"* ]]; then
    echo "[FAIL] expected to contain: $needle"
    echo "[BODY] $haystack"
    exit 1
  fi
}

# 1) health
resp=$(request GET /health)
code=$(echo "$resp" | head -n1)
body=$(echo "$resp" | tail -n +2)
[[ "$code" == "200" ]] || { echo "[FAIL] /health expected 200 got $code"; exit 1; }
assert_contains "$body" '"status":"ok"'
echo "[PASS] GET /health"

# 2) ops ask (mock)
resp=$(request POST /api/ops/ask '{"question":"테스트 질문"}')
code=$(echo "$resp" | head -n1)
body=$(echo "$resp" | tail -n +2)
[[ "$code" == "200" ]] || { echo "[FAIL] /api/ops/ask expected 200 got $code"; exit 1; }
assert_contains "$body" '"answer"'
echo "[PASS] POST /api/ops/ask"

# 3) validation error format
resp=$(request POST /api/purchase-orders '{}')
code=$(echo "$resp" | head -n1)
body=$(echo "$resp" | tail -n +2)
[[ "$code" == "400" ]] || { echo "[FAIL] /api/purchase-orders validation expected 400 got $code"; exit 1; }
assert_contains "$body" '"code":"VALIDATION_ERROR"'
echo "[PASS] validation error format"

# 4) not found format
resp=$(request GET /__not_found__)
code=$(echo "$resp" | head -n1)
body=$(echo "$resp" | tail -n +2)
[[ "$code" == "404" ]] || { echo "[FAIL] /__not_found__ expected 404 got $code"; exit 1; }
assert_contains "$body" '"code":"NOT_FOUND"'
echo "[PASS] not found format"

echo "[DONE] smoke tests passed"
