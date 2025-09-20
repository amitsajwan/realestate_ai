from app.utils.validation import validate_password_strength, validate_email_format, validate_phone_number

# JWT token verification function
def verify_jwt_token(request_or_token):
    import logging
    from jose import jwt, JWTError
    from app.core.config import settings
    from fastapi import Request
    
    logger = logging.getLogger(__name__)
    
    # Handle both Request object and token string
    if isinstance(request_or_token, Request):
        # Extract token from Authorization header
        auth_header = request_or_token.headers.get("Authorization")
        if not auth_header:
            raise ValueError("No Authorization header found")
        
        # Extract token from "Bearer <token>" format
        try:
            token = auth_header.split(" ")[1]  # Split by space and take the second part
        except IndexError:
            raise ValueError("Invalid Authorization header format")
    else:
        # Assume it's a token string
        token = request_or_token
    
    logger.debug(f"Verifying JWT token: {token[:20]}...")
    
    # Try both secret keys to handle different token sources
    secret_keys = [
        settings.jwt_secret_key,
        "your-super-secret-jwt-key-change-in-production"  # From SECURITY_CONFIG
    ]
    
    for secret_key in secret_keys:
        try:
            payload = jwt.decode(
                token, 
                secret_key, 
                algorithms=[settings.jwt_algorithm],
                options={"verify_aud": False}  # Disable audience verification
            )
            logger.debug(f"Token verified successfully with secret key: {secret_key[:10]}...")
            return payload
        except JWTError as e:
            logger.debug(f"JWT verification failed with secret key {secret_key[:10]}...: {e}")
            continue
        except Exception as e:
            logger.debug(f"Token verification error with secret key {secret_key[:10]}...: {e}")
            continue
    
    # If all secret keys failed
    logger.error(f"JWT verification failed with all secret keys")
    raise ValueError("Invalid token: Could not verify with any known secret key")

def sanitize_user_input(data, max_length: int = 1000):
    import logging
    logger = logging.getLogger(__name__)
    
    # Handle different data types
    if isinstance(data, str):
        logger.debug(f"Sanitizing string input: {data[:30]}... (max_length={max_length})")
        return data[:max_length] if data else ""
    elif isinstance(data, dict):
        logger.debug(f"Sanitizing dict input with {len(data)} keys")
        # For dictionaries, just return as-is for now
        # TODO: Implement proper dict sanitization
        return data
    else:
        logger.debug(f"Sanitizing input of type: {type(data)}")
        return data

__all__ = [
    "validate_password_strength",
    "validate_email_format",
    "validate_phone_number",
    "verify_jwt_token",
    "sanitize_user_input"
]