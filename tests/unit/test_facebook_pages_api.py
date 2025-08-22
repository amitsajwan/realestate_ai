from fastapi.testclient import TestClient
from fastapi import FastAPI
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# from app.api.v1.endpoints.facebook_pages import router as fb_router  # No such file exists, so this import is commented out


def test_facebook_config_connected_demo_user():
    app = FastAPI()
    app.include_router(fb_router, prefix="/api/facebook")

    # Override auth to simulate an authenticated user
    from core.dependencies import get_current_user

    async def fake_user():
        return {"username": "demo"}

    app.dependency_overrides[get_current_user] = fake_user

    client = TestClient(app)

    r = client.get("/api/facebook/config")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "connected" in data
    assert "page_id" in data
    assert "page_name" in data

    # Clean up override
    app.dependency_overrides.pop(get_current_user, None)
