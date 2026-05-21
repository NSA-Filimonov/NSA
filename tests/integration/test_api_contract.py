# tests/integration/test_api_contract.py
# ВАЖНО: интеграционные тесты через реальный HTTP (httpx -> nginx/api),
# НЕ через FastAPI TestClient.
import os
import httpx
import pytest
API_URL = os.getenv("API_URL", "http://nginx").rstrip("/")
USER_OK = "u-prod-smoke"
USER_NO_SECRET = "u-no-secret-smoke"
USER_LOCK = "u-lock-smoke"
def _json(resp: httpx.Response) -> dict:
    assert "application/json" in resp.headers.get("content-type", ""), (
        f"Expected JSON, got {resp.status_code}: {resp.text}"
    )
    return resp.json()
def _setup_start(client: httpx.Client, user_id: str) -> str:
    r = client.post(f"{API_URL}/nsa/setup/start", json={"user_id": user_id})
    assert r.status_code == 200, f"setup/start failed: {r.status_code} {r.text}"
    sid = _json(r).get("setup_session_id")
    assert sid, f"setup_session_id is empty: {r.text}"
    return sid
def _setup_secret(client: httpx.Client, setup_session_id: str, user_id: str) -> None:
    body = {
        "setup_session_id": setup_session_id,
        "user_id": user_id,
        "grid_size": "2x2",
        "steps": [{"cell_a": "A1", "op": "+", "cell_b": "A1"}],
    }
    r = client.post(f"{API_URL}/nsa/setup/secret", json=body)
    assert r.status_code == 200, f"setup/secret failed: {r.status_code} {r.text}"
def _create_challenge(client: httpx.Client, user_id: str) -> dict:
    r = client.post(
        f"{API_URL}/nsa/challenge/create",
        json={"user_id": user_id, "context": "app_login"},
    )
    assert r.status_code == 200, f"challenge/create failed: {r.status_code} {r.text}"
    data = _json(r)
    assert data.get("challenge_id"), f"challenge_id is empty: {data}"
    return data
def _answer_from_grid(ch_data: dict) -> str:
    a1 = ch_data["grid_values"][0][0]
    return str(a1 * 2)
@pytest.fixture(scope="function")
def http_client():
    with httpx.Client(timeout=10.0) as c:
        yield c
@pytest.mark.integration
def test_challenge_create_without_secret_returns_400(http_client: httpx.Client):
    r = http_client.post(
        f"{API_URL}/nsa/challenge/create",
        json={"user_id": USER_NO_SECRET, "context": "app_login"},
    )
    assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text}"
@pytest.mark.integration
def test_challenge_reuse_is_forbidden(http_client: httpx.Client):
    sid = _setup_start(http_client, USER_OK)
    _setup_secret(http_client, sid, USER_OK)
    ch = _create_challenge(http_client, USER_OK)
    cid = ch["challenge_id"]
    answer = _answer_from_grid(ch)
    payload = {"user_id": USER_OK, "challenge_id": cid, "response": answer}
    first = http_client.post(f"{API_URL}/nsa/challenge/verify", json=payload)
    assert first.status_code == 200, f"first verify failed: {first.status_code} {first.text}"
    assert _json(first).get("result") == "success", f"expected success, got: {first.text}"
    second = http_client.post(f"{API_URL}/nsa/challenge/verify", json=payload)
    if second.status_code == 200:
        assert _json(second).get("result") != "success", f"reuse must not be success: {second.text}"
    else:
        assert second.status_code == 400, f"expected 400 or non-success, got {second.status_code}: {second.text}"
@pytest.mark.integration
def test_lockout_after_three_wrong_answers(http_client: httpx.Client):
    sid = _setup_start(http_client, USER_LOCK)
    _setup_secret(http_client, sid, USER_LOCK)
    locked = False
    for wrong in ("101", "202", "303"):
        ch = _create_challenge(http_client, USER_LOCK)
        cid = ch["challenge_id"]
        v = http_client.post(
            f"{API_URL}/nsa/challenge/verify",
            json={"user_id": USER_LOCK, "challenge_id": cid, "response": wrong},
        )
        assert v.status_code == 200, f"verify failed: {v.status_code} {v.text}"
        if _json(v).get("result") == "locked":
            locked = True
            break
    assert locked, "expected lock after 3 fails"
