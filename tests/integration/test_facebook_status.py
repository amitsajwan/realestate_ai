import os
import requests

BASE = os.getenv("BASE_URL", "http://127.0.0.1:8004")


def _login():
    r = requests.post(
        f"{BASE}/api/login",
        json={"email": "demo@mumbai.com", "password": "demo123"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_facebook_config_status_default():
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(f"{BASE}/api/facebook/config", headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "connected" in data and isinstance(data["connected"], bool)
    # page fields may be None when not connected
    assert "page_id" in data
    assert "page_name" in data


def test_facebook_pages_requires_connection():
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(f"{BASE}/api/facebook/pages", headers=headers, timeout=10)
    # When not connected, endpoint should reject
    assert r.status_code in (400, 401), r.text
    if r.status_code == 400:
        err = r.json()
        # Optional detail check if present
        if isinstance(err, dict) and "detail" in err:
            assert "not connected" in str(err["detail"]).lower()
