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
# app/services/nsa_service.py
import json
import time
import uuid
import random
import secrets
from app.schemas.nsa import SetupSecretRequest
from app.repositories.redis_repo import repo
class NSAService:
    def now_ts(self) -> int:
        return int(time.time())
    def setup_start(self, user_id: str):
        sid = str(uuid.uuid4())
        repo.json_set(repo.k_setup(sid), {"user_id": user_id}, ex=3600)
        return {
            "setup_session_id": sid,
            "allowed_grid_sizes": ["2x2", "3x2", "3x3", "4x3", "4x4"],
        }
    def setup_secret(self, req: SetupSecretRequest):
        sess = repo.json_get(repo.k_setup(req.setup_session_id), None)
        if not sess or sess.get("user_id") != req.user_id:
            raise ValueError("invalid_setup_session")
        if len(req.steps) == 0:
            raise ValueError("steps_required")
        steps = [s.model_dump() for s in req.steps]
        profile = {"grid_size": req.grid_size, "steps": steps}
        repo.json_set(repo.k_secret(req.user_id), profile)
        return {"secret_profile_id": f"sp-{req.user_id}", "warnings": []}
    def _grid_shape(self, grid_size: str):
        c, r = grid_size.split("x")
        return int(c), int(r)
    def _generate_grid(self, grid_size: str):
        cols, rows = self._grid_shape(grid_size)
        return [[random.randint(0, 9) for _ in range(rows)] for __ in range(cols)]
    def challenge_create(self, user_id: str, context: str):
        secret = repo.json_get(repo.k_secret(user_id), None)
        if not secret:
            raise ValueError("secret_not_configured")
        state = repo.r.hgetall(repo.k_state(user_id))
        lock_until = int(state.get("lock_until", "0") or 0)
        now = self.now_ts()
        if lock_until > now:
            return {
                "result": "locked",
                "lock_remaining_sec": lock_until - now,
                "message_code": "locked_active",
            }
        cid = str(uuid.uuid4())
        grid = self._generate_grid(secret["grid_size"])
        expires_at = now + 45
        repo.r.hset(
            repo.k_challenge(cid),
            mapping={
                "user_id": user_id,
                "context": context,
                "used": "0",
                "expires_at": str(expires_at),
                "grid_json": json.dumps(grid, ensure_ascii=False),
            },
        )
        repo.r.expire(repo.k_challenge(cid), 45)
        return {
            "challenge_id": cid,
            "grid_size": secret["grid_size"],
            "grid_values": grid,
            "expires_in_sec": 45,
            "input_masking": True,
        }
    def _cell(self, grid, cell: str):
        cell = cell.upper()
        r = ord(cell[0]) - ord("A")
        c = int(cell[1:]) - 1
        return grid[r][c]
    def _evaluate(self, steps, grid) -> str:
        parts = []
        for st in steps:
            a = self._cell(grid, st["cell_a"])
            b = self._cell(grid, st["cell_b"])
            if st["op"] == "+":
                v = a + b
            elif st["op"] == "-":
                v = abs(a - b)
            else:
                v = a * b
            parts.append(str(v))
        return "".join(parts)
    def challenge_verify(self, req):
        if not req.response.isdigit():
            raise ValueError("response_digits_only")
        secret = repo.json_get(repo.k_secret(req.user_id), None)
        if not secret:
            raise ValueError("secret_not_configured")
        now = self.now_ts()
        st = repo.r.hgetall(repo.k_state(req.user_id))
        lock_until = int(st.get("lock_until", "0") or 0)
        if lock_until > now:
            return {
                "result": "locked",
                "lock_remaining_sec": lock_until - now,
                "message_code": "locked_active",
            }
        rc, grid_json = repo.consume_challenge_lua(keys=[repo.k_challenge(req.challenge_id)], args=[now])
        rc = int(rc)
        if rc == 0:
            return {"result": "expired", "message_code": "challenge_missing_or_expired", "lock_remaining_sec": 0}
        if rc == -1:
            return {"result": "fail", "message_code": "challenge_already_used", "lock_remaining_sec": 0}
        if rc == -2:
            return {"result": "expired", "message_code": "challenge_expired", "lock_remaining_sec": 0}
        grid = json.loads(grid_json)
        expected = self._evaluate(secret["steps"], grid)
        if secrets.compare_digest(req.response, expected):
            repo.success_reset_lua(keys=[repo.k_state(req.user_id)], args=[])
            return {"result": "success", "message_code": "ok", "lock_remaining_sec": 0}
        streak, same, lock_until, lock_sec = repo.fail_counter_lua(
            keys=[repo.k_state(req.user_id)],
            args=[now, req.response],
        )
        lock_sec = int(lock_sec)
        if lock_sec > 0:
            return {"result": "locked", "message_code": "lockout_triggered", "lock_remaining_sec": lock_sec}
        if int(same) == 2:
            return {"result": "fail", "message_code": "warning_static_wrong_repeat", "lock_remaining_sec": 0}
        return {"result": "fail", "message_code": "invalid_or_expired", "lock_remaining_sec": 0}
    def status(self, user_id: str):
        st = repo.r.hgetall(repo.k_state(user_id))
        now = self.now_ts()
        lock_until = int(st.get("lock_until", "0") or 0)
        return {
            "is_locked": lock_until > now,
            "lock_remaining_sec": max(0, lock_until - now),
            "failed_attempts": int(st.get("failed_streak", "0") or 0),
            "static_repeat_counter": int(st.get("same_wrong_count", "0") or 0),
        }