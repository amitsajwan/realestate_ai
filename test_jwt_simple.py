"""
Simple JWT Test
===============
Test JWT token generation and validation without loading the full app configuration
"""

import jwt
from datetime import datetime, timedelta

def test_jwt_simple():
    """Test JWT with hardcoded values"""
    print("🔐 SIMPLE JWT TEST")
    print("=" * 30)
    
    # Use the same secret key as in the app
    SECRET_KEY = "your-secret-key-here"
    ALGORITHM = "HS256"
    
    print(f"Secret key: {SECRET_KEY}")
    print(f"Algorithm: {ALGORITHM}")
    
    # Test token generation (same as registration)
    print("\nTesting token generation...")
    token_payload = {
        "sub": "68c97e49bb393289fc2559b9",  # Use the actual user ID from logs
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    
    # Generate token
    token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
    print(f"Generated token: {token[:50]}...")
    
    # Test token validation
    print("\nTesting token validation...")
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("✅ Token decode successful!")
        print(f"User ID: {decoded.get('sub')}")
        print(f"Email: {decoded.get('email')}")
        print(f"Expires: {datetime.fromtimestamp(decoded.get('exp'))}")
        return True
    except Exception as e:
        print(f"❌ Token decode failed: {e}")
        return False

if __name__ == "__main__":
    success = test_jwt_simple()
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 JWT validation working!")
        print("The issue is likely in the app configuration loading.")
    else:
        print("❌ JWT validation failed!")
