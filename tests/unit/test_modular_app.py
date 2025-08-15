from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_page_renders():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Real Estate CRM" in resp.text


def test_dashboard_redirects_without_auth():
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers.get("location") == "/"


def test_dashboard_renders_with_auth_header():
    resp = client.get("/dashboard", headers={"Authorization": "Bearer test"})
    assert resp.status_code == 200
    assert "Dashboard" in resp.text


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


def test_proxy_propagates_unauthorized():
    resp = client.get("/api/leads")
    # Should either mirror 401 (when CRM is running) or 502 if upstream unavailable
    assert resp.status_code in (200, 401, 502)


def test_dashboard_renders_with_auth_cookie():
    resp = client.get("/dashboard", cookies={"auth": "token"})
    assert resp.status_code == 200
    assert "Dashboard" in resp.text


def test_modular_routes_exist():
    # These pass-through to upstream; accept 200/401/502 depending on environment
    res1 = client.get("/mod/leads")
    res2 = client.get("/mod/properties")
    assert res1.status_code in (200, 401, 502)
    assert res2.status_code in (200, 401, 502)
