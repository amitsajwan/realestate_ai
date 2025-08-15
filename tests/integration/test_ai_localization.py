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


def test_languages_and_translate():
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}

    # languages
    r = requests.get(f"{BASE}/api/ai-localization/languages", headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("success") is True
    assert isinstance(data.get("languages"), list) and len(data["languages"]) > 0

    # translate (using query params as endpoint expects scalars)
    params = {
        "text": "Beautiful apartment for sale",
        "target_language": "hi",
        "context": "real estate",
    }
    r2 = requests.post(
        f"{BASE}/api/ai-localization/translate", params=params, headers=headers, timeout=15
    )
    assert r2.status_code == 200, r2.text
    t = r2.json()
    assert "success" in t and "translated_text" in t
