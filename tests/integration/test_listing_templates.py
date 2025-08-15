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


def test_templates_and_generate():
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}

    # templates
    r = requests.get(f"{BASE}/api/listings/templates", headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "templates" in data and isinstance(data["templates"], list)

    # generate
    payload = {
        "template": "just_listed",
        "address": "123 Main St",
        "city": "Mumbai",
        "state": "MH",
        "price": "₹85,00,000",
        "bedrooms": 2,
        "bathrooms": 2,
        "features": ["Near Metro", "Sea view"],
    }
    r2 = requests.post(f"{BASE}/api/listings/generate", json=payload, headers=headers, timeout=20)
    assert r2.status_code == 200, r2.text
    g = r2.json()
    for key in ("caption", "hashtags", "suggested_cta", "fair_housing_disclaimer"):
        assert key in g
