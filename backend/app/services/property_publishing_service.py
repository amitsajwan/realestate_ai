"""
Property Publishing Service
==========================
Service for managing property publishing workflow with multi-language support
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.schemas.agent_language_preferences import (
    PublishingRequest, PublishingStatus, FacebookPageInfo
)
from app.schemas.unified_property import PropertyResponse
from app.core.database import get_database

logger = logging.getLogger(__name__)


class PropertyPublishingService:
    """Service for property publishing operations"""
    
    def __init__(self, db):
        self.db = db
        self.properties_collection = db.get_collection("properties")
        self.publishing_history_collection = db.get_collection("publishing_history")
    
    def _get_property_query(self, property_id: str):
        """Get the correct query for property ID (handle both ObjectId and string)"""
        from bson import ObjectId
        try:
            # Try to convert to ObjectId if it's a valid ObjectId string
            if len(property_id) == 24:
                return {"_id": ObjectId(property_id)}
            else:
                return {"_id": property_id}
        except:
            return {"_id": property_id}
    
    async def publish_property(
        self, 
        property_id: str, 
        agent_id: str, 
        publishing_request: PublishingRequest
    ) -> PublishingStatus:
        """Publish a property to selected channels and languages"""
        try:
            # Get property
            property_query = self._get_property_query(property_id)
            property_query["agent_id"] = agent_id
            property_doc = await self.properties_collection.find_one(property_query)
            if not property_doc:
                raise ValueError(f"Property {property_id} not found or access denied")
            
            # Update property status
            update_query = self._get_property_query(property_id)
            await self.properties_collection.update_one(
                update_query,
                {
                    "$set": {
                        "publishing_status": "published",
                        "published_at": datetime.now(),
                        "target_languages": publishing_request.target_languages,
                        "publishing_channels": publishing_request.publishing_channels,
                        "facebook_page_mappings": publishing_request.facebook_page_mappings or {},
                        "updated_at": datetime.now()
                    }
                }
            )
            
            # Publish to each channel and language
            published_channels = []
            language_status = {}
            facebook_posts = {}
            
            for channel in publishing_request.publishing_channels:
                for language in publishing_request.target_languages:
                    try:
                        if channel == "website":
                            # Website publishing (always successful for now)
                            published_channels.append(f"{channel}_{language}")
                            language_status[language] = "published"
                            
                        elif channel == "facebook":
                            # Facebook publishing
                            page_id = publishing_request.facebook_page_mappings.get(language)
                            if page_id:
                                post_id = await self._publish_to_facebook(
                                    property_doc, language, page_id, agent_id
                                )
                                if post_id:
                                    published_channels.append(f"{channel}_{language}")
                                    language_status[language] = "published"
                                    facebook_posts[language] = post_id
                                else:
                                    language_status[language] = "failed"
                            else:
                                language_status[language] = "no_page_configured"
                        
                        # Record publishing history
                        await self._record_publishing_history(
                            property_id, channel, language, "published", agent_id
                        )
                        
                    except Exception as e:
                        logger.error(f"Error publishing {property_id} to {channel}_{language}: {e}")
                        language_status[language] = "failed"
                        await self._record_publishing_history(
                            property_id, channel, language, "failed", agent_id, str(e)
                        )
            
            # Return publishing status
            return PublishingStatus(
                property_id=property_id,
                publishing_status="published",
                published_at=datetime.now(),
                published_channels=published_channels,
                language_status=language_status,
                facebook_posts=facebook_posts,
                analytics_data={}
            )
            
        except Exception as e:
            logger.error(f"Error publishing property {property_id}: {e}")
            raise
    
    async def get_publishing_status(self, property_id: str, agent_id: str) -> PublishingStatus:
        """Get publishing status for a property"""
        try:
            # Get property
            property_query = self._get_property_query(property_id)
            property_query["agent_id"] = agent_id
            property_doc = await self.properties_collection.find_one(property_query)
            if not property_doc:
                raise ValueError(f"Property {property_id} not found or access denied")
            
            # Get publishing history
            history = await self.publishing_history_collection.find(
                {"property_id": property_id}
            ).to_list(length=None)
            
            # Build status
            published_channels = []
            language_status = {}
            facebook_posts = {}
            
            for record in history:
                if record.get("status") == "published":
                    channel_lang = f"{record['channel']}_{record['language']}"
                    published_channels.append(channel_lang)
                    language_status[record['language']] = "published"
                    
                    if record['channel'] == 'facebook' and record.get('post_id'):
                        facebook_posts[record['language']] = record['post_id']
            
            return PublishingStatus(
                property_id=property_id,
                publishing_status=property_doc.get("publishing_status", "draft"),
                published_at=property_doc.get("published_at"),
                published_channels=published_channels,
                language_status=language_status,
                facebook_posts=facebook_posts,
                analytics_data={}
            )
            
        except Exception as e:
            logger.error(f"Error getting publishing status for {property_id}: {e}")
            raise
    
    async def unpublish_property(self, property_id: str, agent_id: str):
        """Unpublish a property (set status back to draft)"""
        try:
            # Update property status
            update_query = self._get_property_query(property_id)
            update_query["agent_id"] = agent_id
            await self.properties_collection.update_one(
                update_query,
                {
                    "$set": {
                        "publishing_status": "draft",
                        "published_at": None,
                        "updated_at": datetime.now()
                    }
                }
            )
            
            # Record unpublishing
            await self._record_publishing_history(
                property_id, "system", "all", "unpublished", agent_id
            )
            
        except Exception as e:
            logger.error(f"Error unpublishing property {property_id}: {e}")
            raise
    
    async def get_facebook_pages(self, agent_id: str) -> List[FacebookPageInfo]:
        """Get connected Facebook pages for an agent"""
        try:
            # For now, return mock data
            # In real implementation, this would query Facebook API
            return [
                FacebookPageInfo(
                    page_id="mock_page_1",
                    page_name="Real Estate Agent - English",
                    language="en",
                    is_connected=True,
                    last_sync=datetime.now()
                ),
                FacebookPageInfo(
                    page_id="mock_page_2", 
                    page_name="Real Estate Agent - Marathi",
                    language="mr",
                    is_connected=True,
                    last_sync=datetime.now()
                )
            ]
            
        except Exception as e:
            logger.error(f"Error getting Facebook pages for agent {agent_id}: {e}")
            raise
    
    async def connect_facebook_page(self, agent_id: str, page_id: str, language: str):
        """Connect a Facebook page for a specific language"""
        try:
            # In real implementation, this would:
            # 1. Verify page access with Facebook API
            # 2. Store page connection in database
            # 3. Update agent language preferences
            
            logger.info(f"Connecting Facebook page {page_id} for agent {agent_id} in language {language}")
            return {"success": True, "page_id": page_id, "language": language}
            
        except Exception as e:
            logger.error(f"Error connecting Facebook page {page_id}: {e}")
            raise
    
    async def _publish_to_facebook(
        self, 
        property_doc: Dict, 
        language: str, 
        page_id: str, 
        agent_id: str
    ) -> Optional[str]:
        """Publish property to Facebook page"""
        try:
            # Generate content in target language
            content = await self._generate_facebook_content(property_doc, language)
            
            # Mock Facebook API call
            # In real implementation, this would call Facebook Graph API
            post_id = f"fb_post_{property_doc['_id']}_{language}_{int(datetime.now().timestamp())}"
            
            logger.info(f"Published to Facebook page {page_id} in {language}: {post_id}")
            return post_id
            
        except Exception as e:
            logger.error(f"Error publishing to Facebook: {e}")
            return None
    
    async def _generate_facebook_content(self, property_doc: Dict, language: str) -> str:
        """Generate Facebook post content in target language"""
        # Mock content generation
        # In real implementation, this would use AI translation/localization
        
        if language == "en":
            return f"🏠 New Property Listing: {property_doc.get('title', 'Beautiful Property')} - ₹{property_doc.get('price', 0):,}"
        elif language == "mr":
            return f"🏠 नवीन मालमत्ता: {property_doc.get('title', 'सुंदर मालमत्ता')} - ₹{property_doc.get('price', 0):,}"
        elif language == "hi":
            return f"🏠 नई प्रॉपर्टी: {property_doc.get('title', 'सुंदर प्रॉपर्टी')} - ₹{property_doc.get('price', 0):,}"
        else:
            return f"🏠 New Property: {property_doc.get('title', 'Beautiful Property')} - ₹{property_doc.get('price', 0):,}"
    
    async def _record_publishing_history(
        self, 
        property_id: str, 
        channel: str, 
        language: str, 
        status: str, 
        agent_id: str,
        error_message: Optional[str] = None
    ):
        """Record publishing history"""
        try:
            history_record = {
                "property_id": property_id,
                "channel": channel,
                "language": language,
                "status": status,
                "agent_id": agent_id,
                "timestamp": datetime.now(),
                "error_message": error_message
            }
            
            await self.publishing_history_collection.insert_one(history_record)
            
        except Exception as e:
            logger.error(f"Error recording publishing history: {e}")