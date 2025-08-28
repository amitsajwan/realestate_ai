import re
from typing import Dict, Any
from email_validator import validate_email, EmailNotValidError

# Common weak passwords list
COMMON_PASSWORDS = {
    "password", "123456", "password123", "admin", "qwerty", "letmein",
    "welcome", "monkey", "1234567890", "abc123", "password1", "123123",
    "welcome123", "admin123", "root", "toor", "pass", "test", "guest",
    "user", "login", "changeme", "newpassword", "secret", "default"
}

def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength with comprehensive checks.
    
    Args:
        password: The password to validate
        
    Returns:
        Dict[str, Any]: Validation result with is_valid and details
    """
    result = {
        "is_valid": True,
        "errors": [],
        "strength_score": 0,
        "strength_level": "weak"
    }
    
    # Check minimum length
    if len(password) < 8:
        result["errors"].append("Password must be at least 8 characters long")
        result["is_valid"] = False
    else:
        result["strength_score"] += 1
    
    # Check maximum length
    if len(password) > 128:
        result["errors"].append("Password must not exceed 128 characters")
        result["is_valid"] = False
    
    # Check for uppercase letters
    if not re.search(r'[A-Z]', password):
        result["errors"].append("Password must contain at least one uppercase letter")
        result["is_valid"] = False
    else:
        result["strength_score"] += 1
    
    # Check for lowercase letters
    if not re.search(r'[a-z]', password):
        result["errors"].append("Password must contain at least one lowercase letter")
        result["is_valid"] = False
    else:
        result["strength_score"] += 1
    
    # Check for numbers
    if not re.search(r'\d', password):
        result["errors"].append("Password must contain at least one number")
        result["is_valid"] = False
    else:
        result["strength_score"] += 1
    
    # Check for special characters
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["errors"].append("Password must contain at least one special character")
        result["is_valid"] = False
    else:
        result["strength_score"] += 1
    
    # Check for common passwords
    if password.lower() in COMMON_PASSWORDS:
        result["errors"].append("Password is too common, please choose a more unique password")
        result["is_valid"] = False
    
    # Check for sequential characters
    if has_sequential_chars(password):
        result["errors"].append("Password should not contain sequential characters")
        result["strength_score"] -= 1
    
    # Check for repeated characters
    if has_repeated_chars(password):
        result["errors"].append("Password should not contain too many repeated characters")
        result["strength_score"] -= 1
    
    # Determine strength level
    if result["strength_score"] >= 4:
        result["strength_level"] = "strong"
    elif result["strength_score"] >= 3:
        result["strength_level"] = "medium"
    else:
        result["strength_level"] = "weak"
    
    return result

def has_sequential_chars(password: str, min_length: int = 3) -> bool:
    """
    Check if password contains sequential characters.
    
    Args:
        password: The password to check
        min_length: Minimum length of sequential characters to flag
        
    Returns:
        bool: True if sequential characters found
    """
    sequences = [
        "abcdefghijklmnopqrstuvwxyz",
        "0123456789",
        "qwertyuiopasdfghjklzxcvbnm"
    ]
    
    password_lower = password.lower()
    
    for sequence in sequences:
        for i in range(len(sequence) - min_length + 1):
            if sequence[i:i + min_length] in password_lower:
                return True
            # Check reverse sequence
            if sequence[i:i + min_length][::-1] in password_lower:
                return True
    
    return False

def has_repeated_chars(password: str, max_repeats: int = 3) -> bool:
    """
    Check if password has too many repeated characters.
    
    Args:
        password: The password to check
        max_repeats: Maximum allowed repeated characters
        
    Returns:
        bool: True if too many repeated characters found
    """
    char_count = {}
    for char in password:
        char_count[char] = char_count.get(char, 0) + 1
        if char_count[char] > max_repeats:
            return True
    return False

def validate_email_format(email: str) -> Dict[str, Any]:
    """
    Validate email format with comprehensive checks.
    
    Args:
        email: The email address to validate
        
    Returns:
        Dict[str, Any]: Validation result
    """
    result = {
        "is_valid": True,
        "errors": [],
        "normalized_email": None
    }
    
    try:
        # Use email-validator library for comprehensive validation
        valid = validate_email(email)
        result["normalized_email"] = valid.email
        
        # Additional custom checks
        if len(email) > 254:  # RFC 5321 limit
            result["errors"].append("Email address is too long")
            result["is_valid"] = False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\.\.+',  # Multiple consecutive dots
            r'^\.',    # Starting with dot
            r'\.$',    # Ending with dot
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, email):
                result["errors"].append("Email format is invalid")
                result["is_valid"] = False
                break
                
    except EmailNotValidError as e:
        result["is_valid"] = False
        result["errors"].append(str(e))
    except Exception as e:
        result["is_valid"] = False
        result["errors"].append("Email validation failed")
    
    return result

def validate_phone_number(phone: str) -> Dict[str, Any]:
    """
    Validate phone number format with international support.
    
    Args:
        phone: The phone number to validate
        
    Returns:
        Dict[str, Any]: Validation result
    """
    result = {
        "is_valid": True,
        "errors": [],
        "formatted_phone": None
    }
    
    # Remove all non-digit characters except +
    cleaned_phone = re.sub(r'[^\d+]', '', phone)
    
    # Basic validation patterns
    patterns = [
        r'^\+1[2-9]\d{2}[2-9]\d{2}\d{4}$',  # US/Canada format
        r'^\+\d{1,3}\d{4,14}$',              # International format
        r'^[2-9]\d{2}[2-9]\d{2}\d{4}$',     # US format without country code
        r'^\d{10}$',                         # 10-digit format
    ]
    
    is_valid_format = any(re.match(pattern, cleaned_phone) for pattern in patterns)
    
    if not is_valid_format:
        result["is_valid"] = False
        result["errors"].append("Invalid phone number format")
    else:
        # Format the phone number
        if cleaned_phone.startswith('+'):
            result["formatted_phone"] = cleaned_phone
        elif len(cleaned_phone) == 10:
            result["formatted_phone"] = f"+1{cleaned_phone}"
        else:
            result["formatted_phone"] = cleaned_phone
    
    # Check length constraints
    if len(cleaned_phone) < 10:
        result["is_valid"] = False
        result["errors"].append("Phone number is too short")
    elif len(cleaned_phone) > 15:
        result["is_valid"] = False
        result["errors"].append("Phone number is too long")
    
    return result