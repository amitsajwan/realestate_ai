"""
HTTP Client Configuration
========================
Centralized httpx client configuration with SSL control
"""

import httpx
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# SSL configuration from environment
SSL_VERIFY = os.getenv("SSL_VERIFY", "true").lower() == "true"
DISABLE_SSL_WARNINGS = os.getenv("DISABLE_SSL_WARNINGS", "true").lower() == "true"

def get_httpx_client(
    timeout: float = 30.0,
    verify: Optional[bool] = None,
    **kwargs
) -> httpx.AsyncClient:
    """
    Get configured httpx client with SSL settings
    
    Args:
        timeout: Request timeout in seconds
        verify: SSL verification (overrides environment setting)
        **kwargs: Additional httpx client arguments
        
    Returns:
        httpx.AsyncClient: Configured client
    """
    # Use environment setting if verify not explicitly provided
    if verify is None:
        verify = SSL_VERIFY
    
    # Disable SSL warnings if configured
    if DISABLE_SSL_WARNINGS and not verify:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    client_config = {
        "timeout": timeout,
        "verify": verify,
        **kwargs
    }
    
    logger.info(f"Creating httpx client with SSL verification: {verify}")
    
    return httpx.AsyncClient(**client_config)

def get_sync_httpx_client(
    timeout: float = 30.0,
    verify: Optional[bool] = None,
    **kwargs
) -> httpx.Client:
    """
    Get configured synchronous httpx client with SSL settings
    
    Args:
        timeout: Request timeout in seconds
        verify: SSL verification (overrides environment setting)
        **kwargs: Additional httpx client arguments
        
    Returns:
        httpx.Client: Configured client
    """
    # Use environment setting if verify not explicitly provided
    if verify is None:
        verify = SSL_VERIFY
    
    # Disable SSL warnings if configured
    if DISABLE_SSL_WARNINGS and not verify:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    client_config = {
        "timeout": timeout,
        "verify": verify,
        **kwargs
    }
    
    logger.info(f"Creating sync httpx client with SSL verification: {verify}")
    
    return httpx.Client(**client_config)
