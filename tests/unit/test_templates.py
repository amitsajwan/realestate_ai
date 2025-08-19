from fastapi.testclient import TestClient
from app.main import app
import os

def test_login_template_renders():
	os.environ["SKIP_DB"] = "1"
	client = TestClient(app)
	r = client.get("/")
	assert r.status_code == 200
	assert "Real Estate CRM - Login" in r.text

def test_onboarding_template_renders():
	os.environ["SKIP_DB"] = "1"
	client = TestClient(app)
	r = client.get("/onboarding")
	assert r.status_code == 200
	assert "Agent Onboarding" in r.text

