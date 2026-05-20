# Copyright 2024 Egor Filimonov, filimoneg@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://apache.org
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#!/usr/bin/env bash
set -euo pipefail
API_URL="${API_URL:-http://127.0.0.1}"
USER_OK="u-prod-smoke"
USER_NO_SECRET="u-no-secret-smoke"
USER_LOCK="u-lock-smoke"
pass() { echo "✅ $1"; }
fail() { echo "❌ $1"; exit 1; }
json_get() {
  local json="$1"
  local path="$2"
  python3 -c '
import json,sys
raw=sys.argv[1]
path=sys.argv[2]
data=json.loads(raw)
cur=data
for p in path.split("."):
    cur = cur[int(p)] if p.isdigit() else cur[p]
print(cur)
' "$json" "$path"
}
request() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  if [[ -n "$body" ]]; then
    curl -sS -X "$method" "$API_URL$path" -H 'Content-Type: application/json' -d "$body"
  else
    curl -sS -X "$method" "$API_URL$path"
  fi
}
request_code() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  if [[ -n "$body" ]]; then
    curl -sS -o /dev/null -w '%{http_code}' -X "$method" "$API_URL$path" -H 'Content-Type: application/json' -d "$body"
  else
    curl -sS -o /dev/null -w '%{http_code}' -X "$method" "$API_URL$path"
  fi
}
echo "== Smoke check: $API_URL =="
HEALTH_CODE=$(request_code GET "/health")
[[ "$HEALTH_CODE" == "200" ]] || fail "/health returned $HEALTH_CODE"
pass "health 200"
SETUP_RESP=$(request POST "/nsa/setup/start" '{"user_id":"'"$USER_OK"'"}')
SETUP_SESSION_ID=$(json_get "$SETUP_RESP" "setup_session_id") || { echo "$SETUP_RESP"; fail "setup/start invalid JSON"; }
[[ -n "$SETUP_SESSION_ID" ]] || fail "setup_session_id is empty"
pass "setup/start"
SECRET_BODY='{"setup_session_id":"'"$SETUP_SESSION_ID"'","user_id":"'"$USER_OK"'","grid_size":"2x2","steps":[{"cell_a":"A1","op":"+","cell_b":"A1"}]}'
SECRET_CODE=$(request_code POST "/nsa/setup/secret" "$SECRET_BODY")
[[ "$SECRET_CODE" == "200" ]] || fail "setup/secret returned $SECRET_CODE"
pass "setup/secret"
CH_RESP=$(request POST "/nsa/challenge/create" '{"user_id":"'"$USER_OK"'","context":"app_login"}')
CH_ID=$(json_get "$CH_RESP" "challenge_id") || { echo "$CH_RESP"; fail "challenge/create invalid JSON"; }
A1=$(json_get "$CH_RESP" "grid_values.0.0") || fail "grid parse failed"
ANSWER=$((A1 * 2))
[[ -n "$CH_ID" ]] || fail "challenge_id is empty"
pass "challenge/create"
VERIFY_OK_BODY='{"user_id":"'"$USER_OK"'","challenge_id":"'"$CH_ID"'","response":"'"$ANSWER"'"}'
VERIFY_OK_RESP=$(request POST "/nsa/challenge/verify" "$VERIFY_OK_BODY")
VERIFY_OK_RESULT=$(json_get "$VERIFY_OK_RESP" "result")
[[ "$VERIFY_OK_RESULT" == "success" ]] || fail "verify expected success, got: $VERIFY_OK_RESP"
pass "challenge/verify success"
STATUS_RESP=$(request GET "/nsa/status?user_id=$USER_OK")
IS_LOCKED=$(json_get "$STATUS_RESP" "is_locked")
[[ "$IS_LOCKED" == "False" || "$IS_LOCKED" == "false" ]] || fail "status expected unlocked, got: $STATUS_RESP"
pass "status unlocked"
BAD_CODE=$(request_code POST "/nsa/challenge/verify" '{"user_id":"'"$USER_OK"'","challenge_id":"bad-id","response":"12ab"}')
[[ "$BAD_CODE" == "400" ]] || fail "non-digit response expected 400, got $BAD_CODE"
pass "negative non-digit response"
NO_SECRET_CODE=$(request_code POST "/nsa/challenge/create" '{"user_id":"'"$USER_NO_SECRET"'","context":"app_login"}')
[[ "$NO_SECRET_CODE" == "400" ]] || fail "create without secret expected 400, got $NO_SECRET_CODE"
pass "negative create without secret"
CH2_RESP=$(request POST "/nsa/challenge/create" '{"user_id":"'"$USER_OK"'","context":"app_login"}')
CH2_ID=$(json_get "$CH2_RESP" "challenge_id")
A1_2=$(json_get "$CH2_RESP" "grid_values.0.0")
ANS2=$((A1_2 * 2))
REQ2='{"user_id":"'"$USER_OK"'","challenge_id":"'"$CH2_ID"'","response":"'"$ANS2"'"}'
_=$(request POST "/nsa/challenge/verify" "$REQ2")
REUSE_RESP=$(request POST "/nsa/challenge/verify" "$REQ2")
REUSE_RESULT=$(json_get "$REUSE_RESP" "result")
[[ "$REUSE_RESULT" != "success" ]] || fail "reuse challenge should not be success"
pass "negative challenge reuse"
SETUP_LOCK=$(request POST "/nsa/setup/start" '{"user_id":"'"$USER_LOCK"'"}')
SETUP_LOCK_ID=$(json_get "$SETUP_LOCK" "setup_session_id")
LOCK_SECRET='{"setup_session_id":"'"$SETUP_LOCK_ID"'","user_id":"'"$USER_LOCK"'","grid_size":"2x2","steps":[{"cell_a":"A1","op":"+","cell_b":"A1"}]}'
LOCK_SECRET_CODE=$(request_code POST "/nsa/setup/secret" "$LOCK_SECRET")
[[ "$LOCK_SECRET_CODE" == "200" ]] || fail "lock user setup/secret failed"
LOCKED="false"
for wrong in 101 202 303; do
  C=$(request POST "/nsa/challenge/create" '{"user_id":"'"$USER_LOCK"'","context":"app_login"}')
  CID=$(json_get "$C" "challenge_id")
  V=$(request POST "/nsa/challenge/verify" '{"user_id":"'"$USER_LOCK"'","challenge_id":"'"$CID"'","response":"'"$wrong"'"}')
  RES=$(json_get "$V" "result")
  if [[ "$RES" == "locked" ]]; then
    LOCKED="true"
    break
  fi
done
[[ "$LOCKED" == "true" ]] || fail "expected lock after 3 fails"
pass "lockout policy"
echo
echo "🎉 Smoke checks passed"
