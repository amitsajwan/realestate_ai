"""
Social Publishing Service
========================
Service for managing social media publishing operations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.social_draft import SocialDraft, DraftStatus, Channel
from app.models.social_post import SocialPost, PostStatus
from app.schemas.social_publishing import (
    GenerateContentRequest, GenerateContentResponse, UpdateDraftRequest,
    PublishRequest, AIDraft
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PublishResponse(BaseModel):
    """Response model for publishing operation"""
    job_id: str
    message: str
    published_count: int = 0
    failed_count: int = 0
    failed_drafts: List[Dict[str, Any]] = []

class SocialPublishingService:
    """Service for social media publishing operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def generate_content(self, request: GenerateContentRequest, agent_id: str) -> List[SocialDraft]:
        """Generate AI content and save as drafts"""
        try:
            logger.info(f"Generating content for property {request.property_id}")
            
            # Get property data
            property_doc = await self._get_property_data(request.property_id)
            if not property_doc:
                raise ValueError(f"Property {request.property_id} not found")
            
            # Log property data for debugging
            logger.info(f"Property data structure: {list(property_doc.keys())}")
            logger.info(f"Property amenities type: {type(property_doc.get('amenities'))}, value: {property_doc.get('amenities')}")
            logger.info(f"Property has description: {'description' in property_doc}")
            
            # Get agent data
            agent_data = await self._get_agent_data(agent_id)
            if not agent_data:
                # Create fallback agent data if none found
                logger.warning(f"No agent data found for {agent_id}, creating fallback agent data")
                agent_data = {
                    "_id": agent_id,
                    "name": "Agent",
                    "email": "",
                    "phone": "",
                    "whatsapp": "",
                    "website": ""
                }
            
            # Import unified AI content generation service
            from app.services.unified_ai_content_service import UnifiedAIContentService, ContentChannel, ContentTone, ContentLength
            
            ai_service = UnifiedAIContentService(self.db)
            drafts = []
            
            for channel in request.channels:
                # Create property context
                # Handle amenities - convert string to list if needed
                amenities = property_doc.get("amenities", [])
                if isinstance(amenities, str):
                    amenities = [item.strip() for item in amenities.split(",") if item.strip()]
                
                property_context = PropertyContext(
                    id=property_doc["_id"],
                    title=property_doc.get("title", "Property"),
                    description=property_doc.get("description", property_doc.get("title", "Beautiful property for sale")),
                    property_type=property_doc.get("property_type", "Apartment"),
                    price=property_doc.get("price", 0),
                    location=property_doc.get("location", "Unknown"),
                    bedrooms=property_doc.get("bedrooms", 0),
                    bathrooms=property_doc.get("bathrooms", 0),
                    area_sqft=property_doc.get("area_sqft", 0),
                    amenities=amenities,
                    features=property_doc.get("features", []),
                    images=property_doc.get("images", [])
                )
                
                # Create agent context
                agent_context = ContactInfo(
                    name=agent_data.get("name", "Agent"),
                    phone=agent_data.get("phone", ""),
                    whatsapp=agent_data.get("whatsapp", ""),
                    email=agent_data.get("email", ""),
                    website=agent_data.get("website", "")
                )
                
                # Create AI generation context
                ai_context = AIGenerationContext(
                    property=property_context,
                    agent=agent_context,
                    language=request.language,
                    channel=channel,
                    tone=request.tone or "friendly",
                    length=request.length or "medium"
                )
                
                # Generate AI content using the new service
                property_data = {
                    "id": request.property_id,
                    "title": property_context.title,
                    "price": property_context.price,
                    "location": property_context.location,
                    "bedrooms": property_context.bedrooms,
                    "bathrooms": property_context.bathrooms,
                    "area_sqft": property_context.area_sqft,
                    "property_type": property_context.property_type,
                    "description": property_context.description,
                    "amenities": property_context.amenities,
                    "features": property_context.features
                }
                
                logger.info(f"=== SOCIAL PUBLISHING AI GENERATION ===")
                logger.info(f"Channel: {channel.value}")
                logger.info(f"Property data: {property_data}")
                logger.info(f"Custom prompt: {request.custom_prompt}")
                logger.info(f"Language: {request.language}")
                
                # Map channel to ContentChannel enum
                content_channel = ContentChannel.WEBSITE  # Default
                if channel.value.lower() == "facebook":
                    content_channel = ContentChannel.FACEBOOK
                elif channel.value.lower() == "instagram":
                    content_channel = ContentChannel.INSTAGRAM
                elif channel.value.lower() == "whatsapp":
                    content_channel = ContentChannel.WHATSAPP
                elif channel.value.lower() == "email":
                    content_channel = ContentChannel.EMAIL
                
                result = await ai_service.generate_content(
                    property_data=property_data,
                    channel=content_channel,
                    tone=ContentTone.FRIENDLY,
                    length=ContentLength.MEDIUM,
                    language=request.language,
                    custom_prompt=request.custom_prompt or f"Generate {channel.value} content",
                    agent_data=agent_data
                )
                
                generated_content = result.get("content", {}).get("body", "")
                
                logger.info(f"Generated content length: {len(generated_content)}")
                logger.info(f"Generated content preview: {generated_content[:200]}...")
                
                # Create social draft
                draft = SocialDraft(
                    property_id=request.property_id,
                    agent_id=agent_id,
                    language=request.language,
                    channel=channel,
                    title=f"AI Generated {channel.value} Content",
                    body=generated_content,
                    hashtags=["#realestate", "#property", f"#{channel.value}"],
                    media_ids=[],
                    contact_included=True,
                    status=DraftStatus.GENERATED
                )
                
                # Save to database
                await draft.insert()
                drafts.append(draft)
                
            logger.info(f"Generated {len(drafts)} drafts successfully")
            return drafts
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise
    
    async def _get_property_data(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get property data from database"""
        try:
            from app.services.unified_property_service import UnifiedPropertyService
            from bson import ObjectId
            
            # Create property service instance
            property_service = UnifiedPropertyService(self.db)
            
            # Get property by ID (we need to find the agent_id first)
            # For now, let's try to get the property directly from the collection
            try:
                obj_id = ObjectId(property_id)
            except:
                return None
            
            # Query the properties collection directly
            property_doc = await self.db.properties.find_one({"_id": obj_id})
            if property_doc:
                # Convert ObjectId to string for JSON serialization
                property_doc["_id"] = str(property_doc["_id"])
                return property_doc
            return None
        except Exception as e:
            logger.error(f"Error getting property data: {e}")
            return None
    
    async def _get_agent_data(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive agent data using unified agent data service"""
        try:
            # Use the new unified agent data service
            from app.services.unified_agent_data_service import UnifiedAgentDataService
            
            unified_service = UnifiedAgentDataService(self.db)
            agent_context = await unified_service.get_agent_context_for_ai(agent_id)
            
            # Convert to the format expected by the existing code
            agent_data = {
                "_id": agent_context.get("user_id", agent_id),
                "name": agent_context.get("agent_name", "Agent"),
                "agent_name": agent_context.get("agent_name", "Agent"),
                "email": agent_context.get("email", ""),
                "phone": agent_context.get("phone", ""),
                "whatsapp": agent_context.get("whatsapp", ""),
                "website": agent_context.get("website", ""),
                
                # Include business context for enhanced AI generation
                "business_type": agent_context.get("business_type", "Residential"),
                "target_audience": agent_context.get("target_audience", "General clients"),
                "company": agent_context.get("company", ""),
                "position": agent_context.get("position", ""),
                "ai_style": agent_context.get("ai_style", "Professional"),
                "ai_tone": agent_context.get("ai_tone", "Friendly"),
                "brand_style": agent_context.get("brand_style", "Professional"),
                "brand_personality": agent_context.get("brand_personality", "Trustworthy"),
                "brand_keywords": agent_context.get("brand_keywords", ""),
                "brand_inspiration": agent_context.get("brand_inspiration", ""),
                "specialties": agent_context.get("specialties", []),
                "experience": agent_context.get("experience", ""),
                "languages": agent_context.get("languages", ["English"]),
                "bio": agent_context.get("bio", ""),
                "tagline": agent_context.get("tagline", ""),
                "brand_theme": agent_context.get("brand_theme", {}),
                "facebook_page": agent_context.get("facebook_page", ""),
                "preferences": agent_context.get("preferences", [])
            }
            
            logger.info(f"Retrieved comprehensive agent data for {agent_id}")
            return agent_data
            
        except Exception as e:
            logger.error(f"Error getting agent data using unified service: {e}")
            
            # Fallback to basic agent data
            return {
                "_id": agent_id,
                "name": "Agent",
                "agent_name": "Agent",
                "email": "",
                "phone": "",
                "whatsapp": "",
                "website": "",
                "business_type": "Residential",
                "target_audience": "General clients",
                "company": "",
                "position": "",
                "ai_style": "Professional",
                "ai_tone": "Friendly",
                "brand_style": "Professional",
                "brand_personality": "Trustworthy",
                "brand_keywords": "",
                "brand_inspiration": "",
                "specialties": [],
                "experience": "",
                "languages": ["English"],
                "bio": "",
                "tagline": "",
                "brand_theme": {},
                "facebook_page": "",
                "preferences": []
            }
    
    async def update_draft(self, draft_id: str, updates: UpdateDraftRequest, agent_id: str) -> Optional[SocialDraft]:
        """Update a draft"""
        try:
            draft = await SocialDraft.get(draft_id)
            if not draft:
                return None
            
            # Update fields
            update_data = updates.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(draft, key, value)
            
            draft.updated_at = datetime.utcnow()
            await draft.save()
            
            logger.info(f"Draft {draft_id} updated successfully")
            return draft
            
        except Exception as e:
            logger.error(f"Error updating draft {draft_id}: {e}")
            raise
    
    async def publish_drafts(self, draft_ids: List[str], agent_id: str) -> PublishResponse:
        """Publish drafts to social media platforms"""
        try:
            logger.info(f"Publishing {len(draft_ids)} drafts")
            
            # Convert string IDs to ObjectId
            object_ids = [ObjectId(draft_id) for draft_id in draft_ids]
            
            # Get drafts that can be published (GENERATED, EDITED, or READY status)
            drafts = await SocialDraft.find(
                {"_id": {"$in": object_ids}, "status": {"$in": [DraftStatus.GENERATED, DraftStatus.EDITED, DraftStatus.READY]}}
            ).to_list()
            
            if not drafts:
                raise ValueError("No publishable drafts found")
            
            published_posts = []
            failed_posts = []
            
            for draft in drafts:
                try:
                    # Update draft status to publishing
                    draft.status = DraftStatus.PUBLISHING
                    await draft.save()
                    
                    # Mock platform publishing (replace with actual platform integration)
                    platform_result = {
                        "success": True,
                        "post_id": f"platform_post_{datetime.utcnow().timestamp()}",
                        "post_url": f"https://{draft.channel}.com/post/platform_post_{datetime.utcnow().timestamp()}"
                    }
                    
                    if platform_result["success"]:
                        # Create social post record
                        social_post = SocialPost(
                            draft_id=draft.id,
                            property_id=draft.property_id,
                            agent_id=draft.agent_id,
                            platform=draft.channel,
                            platform_post_id=platform_result["post_id"],
                            platform_post_url=platform_result["post_url"],
                            status=PostStatus.PUBLISHED,
                            published_at=datetime.utcnow()
                        )
                        await social_post.insert()
                        
                        # Update draft with published info
                        draft.status = DraftStatus.PUBLISHED
                        draft.published_at = datetime.utcnow()
                        draft.platform_post_id = platform_result["post_id"]
                        draft.platform_post_url = platform_result["post_url"]
                        await draft.save()
                        
                        # Update property publishing status
                        await self._update_property_publishing_status(draft.property_id)
                        
                        published_posts.append(social_post)
                        
                    else:
                        # Handle publishing failure
                        draft.status = DraftStatus.FAILED
                        await draft.save()
                        
                        failed_posts.append({
                            "draft_id": str(draft.id),
                            "error": platform_result.get("error", "Unknown error")
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to publish draft {draft.id}: {e}")
                    draft.status = DraftStatus.FAILED
                    await draft.save()
                    
                    failed_posts.append({
                        "draft_id": str(draft.id),
                        "error": str(e)
                    })
            
            logger.info(f"Published {len(published_posts)} drafts successfully")
            
            return PublishResponse(
                job_id=f"publish_job_{datetime.utcnow().timestamp()}",
                message=f"Published {len(published_posts)} drafts successfully",
                published_count=len(published_posts),
                failed_count=len(failed_posts),
                failed_drafts=failed_posts
            )
            
        except Exception as e:
            logger.error(f"Error publishing drafts: {e}")
            raise
    
    async def get_published_posts(self, property_id: str) -> List[SocialPost]:
        """Get all published posts for a property"""
        try:
            posts = await SocialPost.find({"property_id": property_id}).to_list()
            return posts
        except Exception as e:
            logger.error(f"Error getting published posts: {e}")
            raise
    
    async def _update_property_publishing_status(self, property_id: str):
        """Update property publishing status to published"""
        try:
            from bson import ObjectId
            
            # Update property status to published
            result = await self.db.properties.update_one(
                {"_id": ObjectId(property_id)},
                {
                    "$set": {
                        "publishing_status": "published",
                        "published_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated property {property_id} status to published")
            else:
                logger.warning(f"Property {property_id} not found or already published")
                
        except Exception as e:
            logger.error(f"Error updating property publishing status: {e}")
            # Don't raise the error to avoid failing the entire publishing process
