"""
Input Sanitization Utilities
============================
Functions for sanitizing and cleaning user input
"""

import re
import html
from typing import Any, Union
import logging

logger = logging.getLogger(__name__)

def sanitize_user_input(value: Any) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if value is None:
        return ""
    
    # Convert to string
    if not isinstance(value, str):
        value = str(value)
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # HTML escape
    value = html.escape(value)
    
    # Remove potentially dangerous characters
    value = re.sub(r'[<>"\']', '', value)
    
    # Trim whitespace
    value = value.strip()
    
    return value

def sanitize_email(email: str) -> str:
    """Sanitize email address"""
    if not email:
        return ""
    
    # Convert to lowercase and trim
    email = email.lower().strip()
    
    # Remove any HTML or script tags
    email = re.sub(r'<[^>]*>', '', email)
    
    # Remove null bytes
    email = email.replace('\x00', '')
    
    return email

def sanitize_phone(phone: str) -> str:
    """Sanitize phone number"""
    if not phone:
        return ""
    
    # Remove all non-digit characters except +, -, (, ), and space
    phone = re.sub(r'[^\d\+\-\(\)\s]', '', phone)
    
    # Remove null bytes
    phone = phone.replace('\x00', '')
    
    # Trim whitespace
    phone = phone.strip()
    
    return phone

def sanitize_name(name: str) -> str:
    """Sanitize name fields"""
    if not name:
        return ""
    
    # Remove HTML tags
    name = re.sub(r'<[^>]*>', '', name)
    
    # Remove null bytes
    name = name.replace('\x00', '')
    
    # Remove potentially dangerous characters
    name = re.sub(r'[<>"\']', '', name)
    
    # Trim whitespace
    name = name.strip()
    
    # Title case
    name = name.title()
    
    return name

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize general text input"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # HTML escape
    text = html.escape(text)
    
    # Trim whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text