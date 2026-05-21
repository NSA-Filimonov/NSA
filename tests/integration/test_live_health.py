import os
import httpx
import pytest
@pytest.mark.integration
def test_live_health() -> None:
    base_url = os.getenv("API_URL", "http://127.0.0.1")
    r = httpx.get(f"{base_url}/health", timeout=5.0)
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"