from app.utils.validation import validate_password_strength, validate_email_format, validate_phone_number

# JWT token verification function
def verify_jwt_token(token: str):
    import logging
    from jose import jwt, JWTError
    from app.core.config import settings
    
    logger = logging.getLogger(__name__)
    logger.debug(f"Verifying JWT token: {token}")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise ValueError(f"Invalid token: {e}")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise ValueError(f"Token verification failed: {e}")

def sanitize_user_input(data: str, max_length: int = 1000) -> str:
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Sanitizing user input: {data[:30]}... (max_length={max_length})")
    """Placeholder for user input sanitization"""
    # This will be implemented properly when we fix the circular import
    return data[:max_length] if data else ""

__all__ = [
    "validate_password_strength",
    "validate_email_format",
    "validate_phone_number",
    "verify_jwt_token",
    "sanitize_user_input"
]