"""
Agent Language Service
=====================
Service for managing agent language preferences and Facebook page mappings
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
from app.schemas.agent_language_preferences import (
    AgentLanguagePreferences,
    LanguagePreferenceUpdate,
    LanguagePreference
)
from app.core.database import get_database

logger = logging.getLogger(__name__)


class AgentLanguageService:
    """Service for agent language preference operations"""
    
    def __init__(self, db):
        self.db = db
        self.preferences_collection = db.get_collection("agent_language_preferences")
    
    async def get_agent_preferences(self, agent_id: str) -> AgentLanguagePreferences:
        """Get agent language preferences"""
        try:
            # Try to get existing preferences
            prefs_doc = await self.preferences_collection.find_one({"agent_id": agent_id})
            
            if prefs_doc:
                # Convert document to preferences object
                return AgentLanguagePreferences(
                    agent_id=prefs_doc["agent_id"],
                    primary_language=prefs_doc.get("primary_language", "en"),
                    secondary_languages=prefs_doc.get("secondary_languages", []),
                    language_mappings=prefs_doc.get("language_mappings", {}),
                    facebook_page_mappings=prefs_doc.get("facebook_page_mappings", {}),
                    auto_translate_enabled=prefs_doc.get("auto_translate_enabled", True),
                    created_at=prefs_doc.get("created_at", datetime.now()),
                    updated_at=prefs_doc.get("updated_at", datetime.now())
                )
            else:
                # Create default preferences
                default_prefs = AgentLanguagePreferences(
                    agent_id=agent_id,
                    primary_language="en",
                    secondary_languages=[],
                    language_mappings={},
                    facebook_page_mappings={},
                    auto_translate_enabled=True
                )
                
                # Save default preferences
                await self._save_preferences(default_prefs)
                return default_prefs
                
        except Exception as e:
            logger.error(f"Error getting agent preferences for {agent_id}: {e}")
            raise
    
    async def update_agent_preferences(
        self, 
        agent_id: str, 
        preferences_update: LanguagePreferenceUpdate
    ) -> AgentLanguagePreferences:
        """Update agent language preferences"""
        try:
            # Get current preferences
            current_prefs = await self.get_agent_preferences(agent_id)
            
            # Update fields
            update_data = {}
            if preferences_update.primary_language is not None:
                update_data["primary_language"] = preferences_update.primary_language
            if preferences_update.secondary_languages is not None:
                update_data["secondary_languages"] = preferences_update.secondary_languages
            if preferences_update.facebook_page_mappings is not None:
                update_data["facebook_page_mappings"] = preferences_update.facebook_page_mappings
            if preferences_update.auto_translate_enabled is not None:
                update_data["auto_translate_enabled"] = preferences_update.auto_translate_enabled
            
            update_data["updated_at"] = datetime.now()
            
            # Update in database
            await self.preferences_collection.update_one(
                {"agent_id": agent_id},
                {"$set": update_data},
                upsert=True
            )
            
            # Return updated preferences
            return await self.get_agent_preferences(agent_id)
            
        except Exception as e:
            logger.error(f"Error updating agent preferences for {agent_id}: {e}")
            raise
    
    async def add_language_preference(
        self, 
        agent_id: str, 
        language_code: str, 
        language_name: str,
        is_primary: bool = False,
        facebook_page_id: Optional[str] = None
    ) -> AgentLanguagePreferences:
        """Add a new language preference for an agent"""
        try:
            current_prefs = await self.get_agent_preferences(agent_id)
            
            # Create language preference
            lang_pref = LanguagePreference(
                language_code=language_code,
                language_name=language_name,
                is_primary=is_primary,
                facebook_page_id=facebook_page_id,
                auto_translate=True,
                is_active=True
            )
            
            # Update preferences
            current_prefs.language_mappings[language_code] = lang_pref
            
            if is_primary:
                current_prefs.primary_language = language_code
            
            if facebook_page_id:
                current_prefs.facebook_page_mappings[language_code] = facebook_page_id
            
            # Save updated preferences
            await self._save_preferences(current_prefs)
            return current_prefs
            
        except Exception as e:
            logger.error(f"Error adding language preference for {agent_id}: {e}")
            raise
    
    async def remove_language_preference(
        self, 
        agent_id: str, 
        language_code: str
    ) -> AgentLanguagePreferences:
        """Remove a language preference for an agent"""
        try:
            current_prefs = await self.get_agent_preferences(agent_id)
            
            # Remove from mappings
            if language_code in current_prefs.language_mappings:
                del current_prefs.language_mappings[language_code]
            
            if language_code in current_prefs.facebook_page_mappings:
                del current_prefs.facebook_page_mappings[language_code]
            
            # Remove from secondary languages
            if language_code in current_prefs.secondary_languages:
                current_prefs.secondary_languages.remove(language_code)
            
            # If removing primary language, set a new primary
            if current_prefs.primary_language == language_code:
                if current_prefs.secondary_languages:
                    current_prefs.primary_language = current_prefs.secondary_languages[0]
                    current_prefs.secondary_languages = current_prefs.secondary_languages[1:]
                else:
                    current_prefs.primary_language = "en"  # Default fallback
            
            # Save updated preferences
            await self._save_preferences(current_prefs)
            return current_prefs
            
        except Exception as e:
            logger.error(f"Error removing language preference for {agent_id}: {e}")
            raise
    
    async def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        return [
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "mr", "name": "Marathi", "native_name": "मराठी"},
            {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
            {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"},
            {"code": "bn", "name": "Bengali", "native_name": "বাংলা"},
            {"code": "te", "name": "Telugu", "native_name": "తెలుగు"},
            {"code": "gu", "name": "Gujarati", "native_name": "ગુજરાતી"},
            {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ"},
            {"code": "ml", "name": "Malayalam", "native_name": "മലയാളം"},
            {"code": "pa", "name": "Punjabi", "native_name": "ਪੰਜਾਬੀ"}
        ]
    
    async def _save_preferences(self, preferences: AgentLanguagePreferences):
        """Save preferences to database"""
        try:
            prefs_dict = preferences.model_dump()
            prefs_dict["updated_at"] = datetime.now()
            
            await self.preferences_collection.update_one(
                {"agent_id": preferences.agent_id},
                {"$set": prefs_dict},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
            raise