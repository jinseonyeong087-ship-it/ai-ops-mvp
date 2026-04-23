#!/usr/bin/env bash
# 핵심 API 스모크 테스트 스크립트
# 목적: 배포/변경 직후 "서비스가 기본적으로 살아있는지" 빠르게 확인

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:18080}"
START_SERVER="${START_SERVER:-1}"

WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="/tmp/aiops_smoke_uvicorn.log"

SERVER_PID=""
cleanup() {
  # 스크립트 종료 시 백그라운드 서버 정리
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" || true
  fi
}
trap cleanup EXIT

if [[ "${START_SERVER}" == "1" ]]; then
  cd "$WORKDIR"
  # 로컬 venv 우선 사용, 없으면 시스템 uvicorn 사용
  if [[ -x ".venv/bin/uvicorn" ]]; then
    .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 18080 >"$LOG_FILE" 2>&1 &
  else
    uvicorn app.main:app --host 127.0.0.1 --port 18080 >"$LOG_FILE" 2>&1 &
  fi
  SERVER_PID=$!
  sleep 2
fi

request() {
  # 단일 HTTP 요청 유틸: "status code + body" 반환
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
  # 응답 본문에 기대 문자열이 포함되는지 단순 검증
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
