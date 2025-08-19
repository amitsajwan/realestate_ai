# app/config.py - Original configuration file (reconstructed from usage patterns)

import os
from typing import Optional

# Database Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "real_estate_crm")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# Facebook OAuth Configuration
FB_APP_ID = os.getenv("FB_APP_ID", "")
FB_APP_SECRET = os.getenv("FB_APP_SECRET", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
FB_REDIRECT_URI = f"{BASE_URL}/api/facebook/callback"

# Application Settings
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "app.log")

# WhatsApp Integration (if used)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")

# AI/ML Services (if used)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Email Configuration (if used)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

# File Upload Settings
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "pdf", "doc", "docx"}
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")

# Security Settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"

# Database connection helper (legacy pattern found in your code)
def get_db_config():
    """Return database configuration dict"""
    return {
        "url": MONGODB_URL,
        "db_name": MONGODB_DB_NAME,
    }

# JWT configuration helper
def get_jwt_config():
    """Return JWT configuration dict"""
    return {
        "secret_key": JWT_SECRET_KEY,
        "algorithm": JWT_ALGORITHM,
        "expire_hours": JWT_EXPIRE_HOURS,
    }

# Facebook configuration helper  
def get_facebook_config():
    """Return Facebook OAuth configuration dict"""
    return {
        "app_id": FB_APP_ID,
        "app_secret": FB_APP_SECRET,
        "redirect_uri": FB_REDIRECT_URI,
    }

# Validation function
def validate_config():
    """Validate required configuration values"""
    required_vars = []
    
    if not JWT_SECRET_KEY or JWT_SECRET_KEY == "fallback-secret-key-change-in-production":
        required_vars.append("JWT_SECRET_KEY")
    
    if not MONGODB_URL:
        required_vars.append("MONGODB_URL")
    
    # Facebook is optional but warn if partially configured
    if FB_APP_ID and not FB_APP_SECRET:
        required_vars.append("FB_APP_SECRET")
    elif FB_APP_SECRET and not FB_APP_ID:
        required_vars.append("FB_APP_ID")
    
    if required_vars:
        print(f"⚠️  Warning: Missing or invalid environment variables: {', '.join(required_vars)}")
        if not DEBUG:
            raise ValueError(f"Required configuration missing: {', '.join(required_vars)}")

# Initialize validation on import
validate_config()