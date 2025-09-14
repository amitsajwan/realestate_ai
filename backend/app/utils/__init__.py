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
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise ValueError(f"Invalid token: {e}")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise ValueError(f"Token verification failed: {e}")

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