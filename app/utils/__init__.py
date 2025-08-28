from app.utils.validation import validate_password_strength, validate_email_format, validate_phone_number

import jwt
from datetime import datetime
from app.core.config import settings

def verify_jwt_token(token: str):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "verify_exp": True,
                "verify_iat": True,
                "verify_signature": True
            }
        )
        
        # Verify token type
        if payload.get("type") != "access":
            return None
            
        # Verify issuer
        if payload.get("iss") != "PropertyAI":
            return None
            
        return payload
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def sanitize_user_input(data: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not data:
        return ""
    
    # Basic sanitization - remove potentially dangerous characters
    import re
    sanitized = re.sub(r'[<>"\']', '', data)
    return sanitized[:max_length]

__all__ = [
    "validate_password_strength",
    "validate_email_format",
    "validate_phone_number",
    "verify_jwt_token",
    "sanitize_user_input"
]