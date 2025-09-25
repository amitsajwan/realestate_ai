"""
SSL Configuration
================
Configuration for SSL verification settings
"""

import os

# SSL Configuration
SSL_VERIFY = os.getenv("SSL_VERIFY", "false").lower() == "true"
DISABLE_SSL_WARNINGS = os.getenv("DISABLE_SSL_WARNINGS", "true").lower() == "true"
HTTP_LOG_LEVEL = os.getenv("HTTP_LOG_LEVEL", "WARNING").upper()

# Print current SSL configuration
print(f"SSL Configuration:")
print(f"  SSL_VERIFY: {SSL_VERIFY}")
print(f"  DISABLE_SSL_WARNINGS: {DISABLE_SSL_WARNINGS}")
print(f"  HTTP_LOG_LEVEL: {HTTP_LOG_LEVEL}")
