"""
Test JWT Token Generation and Validation
========================================
Test to verify JWT tokens are working correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import jwt
from datetime import datetime, timedelta

def test_jwt_generation():
    """Test JWT token generation"""
    print("Testing JWT token generation...")
    
    # Use the same secret key as the app
    SECRET_KEY = "your-secret-key-here-change-in-production"
    ALGORITHM = "HS256"
    
    # Create a test token payload (same as registration)
    token_payload = {
        "sub": "507f1f77bcf86cd799439011",  # Mock user ID
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    
    # Generate token
    token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
    print(f"✓ Token generated: {token[:50]}...")
    
    # Decode token
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✓ Token decoded successfully")
        print(f"✓ User ID: {decoded.get('sub')}")
        print(f"✓ Email: {decoded.get('email')}")
        print(f"✓ Expires: {datetime.fromtimestamp(decoded.get('exp'))}")
        return True
    except Exception as e:
        print(f"✗ Token decode failed: {e}")
        return False

def test_secret_key_consistency():
    """Test that secret keys are consistent"""
    print("\nTesting secret key consistency...")
    
    try:
        from backend.app.core.config import settings
        from backend.app.core.auth_backend import SECRET_KEY
        
        print(f"✓ Config secret key: {settings.jwt_secret_key}")
        print(f"✓ Auth backend secret key: {SECRET_KEY}")
        
        if settings.jwt_secret_key == SECRET_KEY:
            print("✓ Secret keys match")
            return True
        else:
            print("✗ Secret keys don't match!")
            return False
    except Exception as e:
        print(f"✗ Error checking secret keys: {e}")
        return False

if __name__ == "__main__":
    print("🔐 JWT TOKEN TEST")
    print("=" * 40)
    
    tests = [
        test_jwt_generation,
        test_secret_key_consistency
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"✅ Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 JWT token generation and validation working!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
