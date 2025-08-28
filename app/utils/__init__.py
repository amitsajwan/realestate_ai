from app.utils.validation import validate_password_strength, validate_email_format, validate_phone_number

# For now, let's create placeholder functions to avoid circular imports
def verify_jwt_token(token: str):
    """Placeholder for JWT token verification"""
    # This will be implemented properly when we fix the circular import
    pass

def sanitize_user_input(data: str, max_length: int = 1000) -> str:
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