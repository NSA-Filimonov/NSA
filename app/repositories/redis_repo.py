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
# app/repositories/redis_repo.py
import json
import os
from typing import Any
from redis import Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
class RedisRepo:
    def __init__(self):
        self.r = Redis.from_url(REDIS_URL, decode_responses=True)
        self._load_scripts()
    def _load_scripts(self):
        # consume challenge atomically: missing/used/expired/ok
        self.consume_challenge_lua = self.r.register_script(
            """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            if redis.call('EXISTS', key) == 0 then
              return {0, ''}
            end
            local used = tonumber(redis.call('HGET', key, 'used') or '0')
            if used == 1 then
              return {-1, ''}
            end
            local exp = tonumber(redis.call('HGET', key, 'expires_at') or '0')
            if now > exp then
              redis.call('HSET', key, 'used', '1')
              redis.call('EXPIRE', key, 1)
              return {-2, ''}
            end
            redis.call('HSET', key, 'used', '1')
            redis.call('EXPIRE', key, 60)
            local grid = redis.call('HGET', key, 'grid_json') or ''
            return {1, grid}
            """
        )
        # fail counters atomically + strictest sanction
        self.fail_counter_lua = self.r.register_script(
            """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local resp = ARGV[2]
            local streak = tonumber(redis.call('HGET', key, 'failed_streak') or '0') + 1
            local last = redis.call('HGET', key, 'last_wrong_response') or ''
            local same = 1
            if last == resp then
              same = tonumber(redis.call('HGET', key, 'same_wrong_count') or '0') + 1
            end
            local lock_sec = 0
            if streak >= 5 then lock_sec = 900 end
            if streak >= 3 and lock_sec < 60 then lock_sec = 60 end
            if same >= 3 and lock_sec < 900 then lock_sec = 900 end
            local lock_until = tonumber(redis.call('HGET', key, 'lock_until') or '0')
            if lock_sec > 0 then
              local candidate = now + lock_sec
              if candidate > lock_until then
                lock_until = candidate
              end
            end
            redis.call('HSET', key,
              'failed_streak', tostring(streak),
              'same_wrong_count', tostring(same),
              'last_wrong_response', resp,
              'lock_until', tostring(lock_until)
            )
            redis.call('EXPIRE', key, 86400)
            return {streak, same, lock_until, lock_sec}
            """
        )
        self.success_reset_lua = self.r.register_script(
            """
            local key = KEYS[1]
            redis.call('HSET', key,
              'failed_streak', '0',
              'same_wrong_count', '0',
              'last_wrong_response', '',
              'lock_until', '0'
            )
            redis.call('EXPIRE', key, 86400)
            return 1
            """
        )
    @staticmethod
    def k_setup(sid: str) -> str: return f"nsa:setup:{sid}"
    @staticmethod
    def k_secret(uid: str) -> str: return f"nsa:secret:{uid}"
    @staticmethod
    def k_state(uid: str) -> str: return f"nsa:state:{uid}"
    @staticmethod
    def k_challenge(cid: str) -> str: return f"nsa:challenge:{cid}"
    def json_set(self, key: str, value: Any, ex: int | None = None):
        data = json.dumps(value, ensure_ascii=False)
        self.r.set(key, data, ex=ex)
    def json_get(self, key: str, default: Any):
        raw = self.r.get(key)
        return default if raw is None else json.loads(raw)
repo = RedisRepo()