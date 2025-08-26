import secrets
import logging
from typing import Dict, Optional
import json
import os

logger = logging.getLogger(__name__)

class FacebookAuthService:
    """Simple service for managing Facebook OAuth state and authentication"""
    
    _state_storage: Dict[str, dict] = {}
    _auth_storage: Dict[str, dict] = {}
    
    @classmethod
    def save_state(cls, state: str, user_id: str = None) -> None:
        """Save OAuth state for validation"""
        cls._state_storage[state] = {
            "user_id": user_id,
            "created_at": str(secrets.token_urlsafe(16))
        }
        logger.info(f"State saved: {state}")
    
    @classmethod
    def validate_state(cls, state: str) -> bool:
        """Validate OAuth state"""
        is_valid = state in cls._state_storage
        if is_valid:
            logger.info(f"State validated: {state}")
            # Optionally remove state after validation
            # cls._state_storage.pop(state, None)
        else:
            logger.warning(f"Invalid state: {state}")
        return is_valid
    
    @classmethod
    def save_auth(cls, user_id: str, access_token: str, user_info: Dict = None) -> None:
        """Save Facebook authentication data"""
        cls._auth_storage[user_id] = {
            "access_token": access_token,
            "user_info": user_info or {},
            "created_at": str(secrets.token_urlsafe(16))
        }
        logger.info(f"Auth saved for user: {user_id}")
    
    @classmethod
    def get_auth(cls, user_id: str) -> Optional[Dict]:
        """Get Facebook authentication data for user"""
        return cls._auth_storage.get(user_id)
    
    @classmethod
    def clear_state(cls, state: str) -> None:
        """Clear OAuth state"""
        cls._state_storage.pop(state, None)
    
    @classmethod
    def clear_auth(cls, user_id: str) -> None:
        """Clear Facebook authentication data"""
        cls._auth_storage.pop(user_id, None)