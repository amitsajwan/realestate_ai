import requests
import json

BASE_URL = "http://localhost:8003"

def test_all_endpoints():
    print("🧪 Testing All Endpoints...")
    
    endpoints_to_test = [
        ("GET", "/health"),
        ("GET", "/api/leads"),
        ("GET", "/api/properties"),
        ("GET", "/api/facebook/config"),
        ("GET", "/api/smart-properties"),
        ("POST", "/api/listings/generate", {
            "address": "123 Test St",
            "city": "Mumbai",
            "state": "Maharashtra",
            "price": "50,00,000",
            "property_type": "apartment",
            "bedrooms": 2,
            "bathrooms": 2,
            "features": ["parking", "balcony"],
            "template": "just_listed",
            "language": "en"
        }),
        ("POST", "/api/smart-properties", {
            "address": "456 Smart Ave",
            "price": "75,00,000",
            "property_type": "apartment",
            "bedrooms": 3,
            "bathrooms": 2,
            "ai_generate": True,
            "template": "just_listed"
        })
    ]
    
    for test in endpoints_to_test:
        method, path = test[0], test[1]
        payload = test[1] if len(test) > 2 else None
        
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{path}")
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{path}", json=payload)
            
            status = "✅" if response.status_code < 400 else "❌"
            print(f"{status} {method} {path}: {response.status_code}")
            
            if response.status_code >= 400:
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ {method} {path}: Connection Error - {e}")

if __name__ == "__main__":
    test_all_endpoints()
