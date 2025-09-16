"""
JWT Debug Test
==============
Test JWT token generation and validation to find the mismatch
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import jwt
from datetime import datetime, timedelta

def test_jwt_debug():
    """Debug JWT token generation and validation"""
    print("🔐 JWT DEBUG TEST")
    print("=" * 40)
    
    try:
        # Import the actual secret keys from the app
        from backend.app.core.config import settings
        from backend.app.core.auth_backend import SECRET_KEY, ALGORITHM, jwt_strategy
        
        print(f"Config secret key: {settings.jwt_secret_key}")
        print(f"Auth backend secret key: {SECRET_KEY}")
        print(f"Algorithm: {ALGORITHM}")
        print(f"JWT strategy secret: {jwt_strategy.secret}")
        print(f"JWT strategy algorithm: {jwt_strategy.algorithm}")
        
        # Check if they match
        if settings.jwt_secret_key == SECRET_KEY:
            print("✅ Secret keys match")
        else:
            print("❌ Secret keys don't match!")
            return False
            
        if settings.jwt_secret_key == jwt_strategy.secret:
            print("✅ Config and strategy secret keys match")
        else:
            print("❌ Config and strategy secret keys don't match!")
            return False
        
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
        
        # Generate token with the same secret key used in registration
        token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
        print(f"Generated token: {token[:50]}...")
        
        # Test token validation (same as /me endpoint)
        print("\nTesting token validation...")
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print("✅ Token decode successful!")
            print(f"User ID: {decoded.get('sub')}")
            print(f"Email: {decoded.get('email')}")
            print(f"Expires: {datetime.fromtimestamp(decoded.get('exp'))}")
        except Exception as e:
            print(f"❌ Token decode failed: {e}")
            return False
        
        # Test with JWT strategy
        print("\nTesting with JWT strategy...")
        try:
            strategy_decoded = jwt.decode(token, jwt_strategy.secret, algorithms=[jwt_strategy.algorithm])
            print("✅ Strategy validation successful!")
            print(f"User ID: {strategy_decoded.get('sub')}")
        except Exception as e:
            print(f"❌ Strategy validation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_jwt_debug()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 JWT validation working!")
        print("The issue might be elsewhere.")
    else:
        print("❌ JWT validation failed!")
        print("This is the root cause of the 401 error.")
