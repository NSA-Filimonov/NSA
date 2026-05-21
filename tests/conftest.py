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
# tests/conftest.py
import os
import time
import pytest
from fastapi.testclient import TestClient
# По умолчанию для docker-compose сети
os.environ.setdefault("REDIS_HOST", "redis")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("API_URL", "http://nginx")
from app.main import app
from app.repositories.redis_repo import repo
@pytest.fixture(scope="session", autouse=True)
def _check_redis() -> None:
    if hasattr(repo, "reconnect"):
        repo.reconnect()
    last_err = None
    for _ in range(30):
        try:
            repo.r.ping()
            return
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    raise RuntimeError(f"Redis is not reachable: {last_err}")
@pytest.fixture(autouse=True)
def _clean_redis():
    repo.r.flushdb()
    yield
    repo.r.flushdb()
@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
