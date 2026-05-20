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
# tests/test_api_flow.py
def _setup_secret(client, user_id="u1"):
    s = client.post("/nsa/setup/start", json={"user_id": user_id}).json()["setup_session_id"]
    body = {
        "setup_session_id": s,
        "user_id": user_id,
        "grid_size": "2x2",
        "steps": [{"cell_a": "A1", "op": "+", "cell_b": "A1"}],
    }
    r = client.post("/nsa/setup/secret", json=body)
    assert r.status_code == 200
def test_happy_path(client):
    _setup_secret(client, "u-ok")
    ch = client.post("/nsa/challenge/create", json={"user_id": "u-ok", "context": "app_login"}).json()
    expected = str(ch["grid_values"][0][0] * 2)
    v = client.post("/nsa/challenge/verify", json={"user_id": "u-ok", "challenge_id": ch["challenge_id"], "response": expected})
    assert v.status_code == 200
    assert v.json()["result"] == "success"
def test_lock_60_after_three_fails(client):
    _setup_secret(client, "u-lock60")
    for wrong in ["101", "202", "303"]:
        ch = client.post("/nsa/challenge/create", json={"user_id": "u-lock60", "context": "app_login"}).json()
        res = client.post("/nsa/challenge/verify", json={"user_id": "u-lock60", "challenge_id": ch["challenge_id"], "response": wrong}).json()
    assert res["result"] == "locked"
    assert res["lock_remaining_sec"] >= 60
def test_lock_900_after_same_wrong_x3(client):
    _setup_secret(client, "u-lock900")
    for _ in range(3):
        ch = client.post("/nsa/challenge/create", json={"user_id": "u-lock900", "context": "app_login"}).json()
        res = client.post("/nsa/challenge/verify", json={"user_id": "u-lock900", "challenge_id": ch["challenge_id"], "response": "7777"}).json()
    assert res["result"] == "locked"
    assert res["lock_remaining_sec"] >= 900