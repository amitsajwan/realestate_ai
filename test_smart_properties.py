# test_smart_properties.py
from fastapi.testclient import TestClient
from api.endpoints.smart_properties import router

from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_create_and_list_property():
    resp = client.post("/smart-properties", json={
        "address": "123 Main St",
        "price": "1,000,000",
        "property_type": "apartment",
        "bedrooms": 3,
        "bathrooms": 2,
        "features": "Pool, Gym",
        "ai_generate": True,
        "template": "just_listed",
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "ai_content" in data
    assert data["ai_content"].startswith("🏡 JUST LISTED:")

    # Check listing
    resp2 = client.get("/smart-properties")
    assert resp2.status_code == 200
    properties = resp2.json()
    assert len(properties) >= 1
    assert properties[0]["address"] == "123 Main St"

def test_fallback_on_ai_error():
    resp = client.post("/smart-properties", json={
        "address": "456 Side Rd",
        "price": "850,000",
        "property_type": "villa",
        "bedrooms": 4,
        "bathrooms": 3,
        "features": "Terrace, Garden",
        "ai_generate": True,
        "template": "price_drop",  # triggers fallback in stub
        "language": "en"
    })
    data = resp.json()
    assert "ai_content" in data
    # Should be fallback style
    assert data["ai_content"].startswith("Villa at 456 Side Rd.")

def test_static_content():
    resp = client.post("/smart-properties", json={
        "address": "789 Another Ave",
        "price": "500,000",
        "property_type": "flat",
        "ai_generate": False,
        "bedrooms": 2,
        "bathrooms": 1
    })
    data = resp.json()
    assert data["ai_content"] is None

if __name__ == "__main__":
    test_create_and_list_property()
    test_fallback_on_ai_error()
    test_static_content()
    print("All tests passed.")
