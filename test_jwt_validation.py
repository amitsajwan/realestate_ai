"""
Test JWT Token Validation
=========================
Test JWT token generation and validation with the actual secret keys
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import jwt
from datetime import datetime, timedelta

def test_jwt_with_actual_secret():
    """Test JWT with the actual secret key from the app"""
    print("Testing JWT with actual secret key...")
    
    try:
        from backend.app.core.config import settings
        from backend.app.core.auth_backend import SECRET_KEY, ALGORITHM
        
        print(f"Config secret key: {settings.jwt_secret_key}")
        print(f"Auth backend secret key: {SECRET_KEY}")
        print(f"Algorithm: {ALGORITHM}")
        
        # Test token generation
        token_payload = {
            "sub": "68c97c13513df8981b1a3adf",  # Use the actual user ID from logs
            "email": "test@example.com",
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        # Generate token with the same secret key used in registration
        token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
        print(f"Generated token: {token[:50]}...")
        
        # Try to decode with the same secret key
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("✅ Token decode successful!")
        print(f"User ID: {decoded.get('sub')}")
        print(f"Email: {decoded.get('email')}")
        
        # Test with the JWT strategy from auth backend
        from backend.app.core.auth_backend import jwt_strategy
        
        # Try to validate the token using the strategy
        print("\nTesting with JWT strategy...")
        print(f"Strategy secret: {jwt_strategy.secret}")
        print(f"Strategy algorithm: {jwt_strategy.algorithm}")
        
        # Decode with strategy secret
        strategy_decoded = jwt.decode(token, jwt_strategy.secret, algorithms=[jwt_strategy.algorithm])
        print("✅ Strategy validation successful!")
        print(f"User ID: {strategy_decoded.get('sub')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔐 JWT VALIDATION TEST")
    print("=" * 40)
    
    success = test_jwt_with_actual_secret()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 JWT validation working!")
    else:
        print("❌ JWT validation failed!")
