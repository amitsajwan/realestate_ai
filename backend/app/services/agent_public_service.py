"""
Agent Public Service
===================
Service layer for agent public website functionality
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas.agent_public import AgentPublicProfile, PublicProperty, ContactInquiry
from app.schemas.agent_public import (
    AgentPublicProfileCreate,
    AgentPublicProfileUpdate,
    PublicPropertyCreate,
    PublicPropertyUpdate,
    PropertySearchFilters,
    ContactInquiryCreate
)
import logging
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger(__name__)

# Global storage for agent profiles (shared across all service instances)
_global_agent_profiles = {}
_global_agent_properties = {}

class AgentPublicService:
    """Service for agent public website operations"""
    
    def __init__(self, db):
        self.db = db
        # Clear global cache for debugging
        global _global_agent_profiles
        _global_agent_profiles.clear()
    
    async def _get_agent_properties_from_db(self, agent_id: str) -> List[PublicProperty]:
        """Get published properties for an agent from the database"""
        try:
            # Query only published properties from the database where agent_id matches
            properties_collection = self.db.get_collection("properties")
            
            # Debug logging
            print(f"DEBUG: Querying properties for agent_id: {agent_id}")
            query = {
                "agent_id": agent_id,
                "publishing_status": "published"  # Only get published properties
            }
            print(f"DEBUG: Query: {query}")
            
            # First, let's check what's actually in the database
            all_properties = await properties_collection.find({"agent_id": agent_id}).to_list(length=None)
            print(f"DEBUG: All properties for agent: {len(all_properties)}")
            for prop in all_properties:
                print(f"DEBUG: Property {prop.get('_id')}: status={prop.get('publishing_status')}")
            
            properties_docs = await properties_collection.find(query).to_list(length=None)
            print(f"DEBUG: Found {len(properties_docs)} published properties")
            
            properties = []
            for doc in properties_docs:
                try:
                    # Validate and clean data before creating PublicProperty
                    title = doc.get("title", "").strip()
                    description = doc.get("description", "").strip()
                    location = doc.get("location", "").strip()
                    
                    # Skip properties with invalid data (relaxed validation for demo)
                    if len(title) < 3:  # Reduced from 5 to 3
                        logger.warning(f"Skipping property {doc.get('_id')} - title too short: '{title}'")
                        continue
                    if len(description) < 3:  # Reduced from 5 to 3
                        logger.warning(f"Skipping property {doc.get('_id')} - description too short: '{description}'")
                        continue
                    if len(location) < 3:  # Reduced from 5 to 3
                        logger.warning(f"Skipping property {doc.get('_id')} - location too short: '{location}'")
                        continue
                    
                    # Handle price validation - keep 0 for "Contact for price" display
                    price = doc.get("price", 0)
                    if price < 0:
                        logger.warning(f"Property {doc.get('_id')} has negative price {price}, setting to 0")
                        price = 0  # Set negative prices to 0
                    
                    property_obj = PublicProperty(
                        id=str(doc.get("_id", "")),
                        agent_id=doc.get("agent_id", ""),
                        title=title,
                        description=description,
                        price=price,
                        property_type=doc.get("property_type", "house"),
                        bedrooms=doc.get("bedrooms"),
                        bathrooms=doc.get("bathrooms"),
                        area=doc.get("area"),
                        location=location,
                        images=doc.get("images", []),
                        features=doc.get("features", []),
                        is_active=doc.get("is_active", True),
                        is_public=doc.get("is_public", True),
                        created_at=doc.get("created_at"),
                        updated_at=doc.get("updated_at")
                    )
                    properties.append(property_obj)
                except Exception as e:
                    logger.warning(f"Skipping property {doc.get('_id')} due to validation error: {e}")
                    continue
            
            return properties
        except Exception as e:
            logger.error(f"Error fetching properties for agent {agent_id}: {e}")
            return []
    
    def _apply_property_filters(self, properties: List[PublicProperty], filters: PropertySearchFilters) -> List[PublicProperty]:
        """Apply search filters to properties"""
        filtered = properties
        
        # Location filter
        if filters.location:
            filtered = [p for p in filtered if filters.location.lower() in p.location.lower()]
        
        # Price filters
        if filters.min_price is not None:
            filtered = [p for p in filtered if p.price >= filters.min_price]
        if filters.max_price is not None:
            filtered = [p for p in filtered if p.price <= filters.max_price]
        
        # Property type filter
        if filters.property_type:
            filtered = [p for p in filtered if p.property_type.lower() == filters.property_type.lower()]
        
        # Bedrooms filter
        if filters.min_bedrooms is not None:
            filtered = [p for p in filtered if p.bedrooms >= filters.min_bedrooms]
        
        # Bathrooms filter
        if filters.min_bathrooms is not None:
            filtered = [p for p in filtered if p.bathrooms >= filters.min_bathrooms]
        
        # Area filters
        if filters.min_area is not None:
            filtered = [p for p in filtered if p.area_sqft >= filters.min_area]
        if filters.max_area is not None:
            filtered = [p for p in filtered if p.area_sqft <= filters.max_area]
        
        # Features filter
        if filters.features:
            filtered = [p for p in filtered if any(feature.lower() in [f.lower() for f in p.features] for feature in filters.features)]
        
        # Sort properties
        if filters.sort_by == "price":
            filtered.sort(key=lambda x: x.price, reverse=(filters.sort_order == "desc"))
        elif filters.sort_by == "created_at":
            filtered.sort(key=lambda x: x.created_at, reverse=(filters.sort_order == "desc"))
        elif filters.sort_by == "area":
            filtered.sort(key=lambda x: x.area_sqft, reverse=(filters.sort_order == "desc"))
        
        return filtered
    
    async def get_agent_by_user_id(self, user_id: str) -> Optional[AgentPublicProfile]:
        """Get agent profile by user ID"""
        try:
            agents_collection = self.db.get_collection("agent_public_profiles")
            # First try to find by user_id field
            agent_doc = await agents_collection.find_one({"user_id": user_id})
            
            # If not found by user_id, try to find by agent_id (since user_id might be used as agent_id)
            if not agent_doc:
                agent_doc = await agents_collection.find_one({"agent_id": user_id})
            
            if not agent_doc:
                return None
            
            # Create profile from database
            profile = AgentPublicProfile(
                id=str(agent_doc.get("_id", "")),
                agent_id=agent_doc.get("agent_id", ""),
                agent_name=agent_doc.get("agent_name", ""),
                slug=agent_doc.get("slug", ""),
                bio=agent_doc.get("bio", ""),
                photo=agent_doc.get("photo", ""),
                phone=agent_doc.get("phone", ""),
                email=agent_doc.get("email", ""),
                office_address=agent_doc.get("office_address", ""),
                specialties=agent_doc.get("specialties", []),
                experience=agent_doc.get("experience", ""),
                languages=agent_doc.get("languages", []),
                is_active=agent_doc.get("is_active", True),
                is_public=agent_doc.get("is_public", True),
                created_at=agent_doc.get("created_at", datetime.now()),
                updated_at=agent_doc.get("updated_at", datetime.now()),
                view_count=agent_doc.get("view_count", 0),
                contact_count=agent_doc.get("contact_count", 0)
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting agent by user ID {user_id}: {e}")
            return None

    async def get_agent_by_slug(self, slug: str) -> Optional[AgentPublicProfile]:
        """Get agent public profile by slug"""
        try:
            # Always check database first for fresh data
            print(f"DEBUG: Looking up agent profile for slug: {slug}")
            agents_collection = self.db.get_collection("agent_public_profiles")
            agent_doc = await agents_collection.find_one({"slug": slug})
            print(f"DEBUG: Database lookup result: {agent_doc is not None}")
            if agent_doc:
                print(f"DEBUG: Found agent in database: {agent_doc.get('agent_name')}")
                # Create profile from database
                profile = AgentPublicProfile(
                    id=str(agent_doc.get("_id", "")),
                    agent_id=agent_doc.get("agent_id", ""),
                    agent_name=agent_doc.get("agent_name", ""),
                    slug=agent_doc.get("slug", ""),
                    bio=agent_doc.get("bio", ""),
                    photo=agent_doc.get("photo", ""),
                    phone=agent_doc.get("phone", ""),
                    email=agent_doc.get("email", ""),
                    office_address=agent_doc.get("office_address", ""),
                    specialties=agent_doc.get("specialties", []),
                    experience=agent_doc.get("experience", ""),
                    languages=agent_doc.get("languages", []),
                    is_active=agent_doc.get("is_active", True),
                    is_public=agent_doc.get("is_public", True),
                    created_at=agent_doc.get("created_at", datetime.now()),
                    updated_at=agent_doc.get("updated_at", datetime.now()),
                    view_count=agent_doc.get("view_count", 0),
                    contact_count=agent_doc.get("contact_count", 0)
                )
                
                # Fetch properties for this agent
                print(f"DEBUG: Fetching properties for agent_id: {profile.agent_id}")
                properties = await self._get_agent_properties_from_db(profile.agent_id)
                print(f"DEBUG: Found {len(properties)} properties")
                
                # Create final profile dict with all data
                profile_dict = profile.model_dump()
                profile_dict['properties'] = [prop.model_dump() for prop in properties]
                
                # Add branding data if available
                branding_data = agent_doc.get("branding_data")
                if branding_data:
                    print(f"DEBUG: Found branding data for agent: {branding_data}")
                    profile_dict['branding_data'] = branding_data
                    print(f"DEBUG: Profile dict after adding branding: {profile_dict.get('branding_data')}")
                else:
                    print(f"DEBUG: No branding data found in agent_doc")
                    print(f"DEBUG: Available keys in agent_doc: {list(agent_doc.keys())}")
                
                print(f"DEBUG: Returning profile with {len(profile_dict['properties'])} properties and branding: {branding_data is not None}")
                
                # Create the profile and check the result
                final_profile = AgentPublicProfile(**profile_dict)
                print(f"DEBUG: Final profile branding_data: {final_profile.branding_data}")
                print(f"DEBUG: Final profile model dump branding: {final_profile.model_dump().get('branding_data')}")
                
                return final_profile
            
            # Fallback to global cache if not in database (disabled for debugging)
            # if slug in _global_agent_profiles:
            #     profile = _global_agent_profiles[slug]
            #     # Fetch properties for this agent
            #     properties = await self._get_agent_properties_from_db(profile.agent_id)
            #     # Add properties to the profile
            #     profile_dict = profile.model_dump()
            #     profile_dict['properties'] = [prop.model_dump() for prop in properties]
            #     return AgentPublicProfile(**profile_dict)
            
            # Fall back to mock data for john-doe (for testing purposes only)
            if slug == "john-doe":
                return AgentPublicProfile(
                    id="mock-agent-id",
                    agent_id="mock-agent-id",
                    agent_name="John Doe",
                    slug="john-doe",
                    bio="Experienced real estate professional with 10+ years in the industry. Specializing in residential and commercial properties, helping clients find their perfect home or investment opportunity.",
                    photo="",
                    phone="+1 (555) 123-4567",
                    email="john@example.com",
                    office_address="123 Main St, New York, NY 10001",
                    specialties=["Residential", "Commercial", "Investment"],
                    experience="10+ years in real estate, Certified Realtor",
                    languages=["English", "Spanish"],
                    is_active=True,
                    is_public=True,  # Set to True so the public page works
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    view_count=0,
                    contact_count=0
                )
            else:
                # Return None for other slugs (agent not found)
                return None
        except Exception as e:
            logger.error(f"Error getting agent by slug {slug}: {e}")
            return None
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentPublicProfile]:
        """Get agent public profile by ID"""
        try:
            print(f"DEBUG: Looking up agent profile for ID: {agent_id}")
            agents_collection = self.db.get_collection("agent_public_profiles")
            agent_doc = await agents_collection.find_one({"agent_id": agent_id})
            print(f"DEBUG: Database lookup result for ID: {agent_doc is not None}")
            
            if agent_doc:
                print(f"DEBUG: Found agent in database by ID: {agent_doc.get('agent_name')}")
                # Create profile from database
                profile = AgentPublicProfile(
                    id=str(agent_doc.get("_id", "")),
                    agent_id=agent_doc.get("agent_id", ""),
                    agent_name=agent_doc.get("agent_name", ""),
                    slug=agent_doc.get("slug", ""),
                    bio=agent_doc.get("bio", ""),
                    photo=agent_doc.get("photo", ""),
                    phone=agent_doc.get("phone", ""),
                    email=agent_doc.get("email", ""),
                    office_address=agent_doc.get("office_address", ""),
                    specialties=agent_doc.get("specialties", []),
                    experience=agent_doc.get("experience", ""),
                    languages=agent_doc.get("languages", []),
                    is_active=agent_doc.get("is_active", True),
                    is_public=agent_doc.get("is_public", True),
                    created_at=agent_doc.get("created_at", datetime.now()),
                    updated_at=agent_doc.get("updated_at", datetime.now()),
                    view_count=agent_doc.get("view_count", 0),
                    contact_count=agent_doc.get("contact_count", 0)
                )
                
                # Fetch properties for this agent
                print(f"DEBUG: Fetching properties for agent_id: {profile.agent_id}")
                properties = await self._get_agent_properties_from_db(profile.agent_id)
                print(f"DEBUG: Found {len(properties)} properties")
                # Add properties to the profile
                profile_dict = profile.model_dump()
                profile_dict['properties'] = [prop.model_dump() for prop in properties]
                print(f"DEBUG: Returning profile with {len(profile_dict['properties'])} properties")
                return AgentPublicProfile(**profile_dict)
            
            # Fall back to mock data for testing
            if agent_id == "mock-agent-id":
                return await self.get_agent_by_slug("john-doe")
            
            return None
        except Exception as e:
            logger.error(f"Error getting agent by ID {agent_id}: {e}")
            return None
    
    async def get_agent_by_user_id(self, user_id: str) -> Optional[AgentPublicProfile]:
        """Get agent profile by user ID"""
        try:
            agents_collection = self.db.get_collection("agent_public_profiles")
            # First try to find by user_id field
            agent_doc = await agents_collection.find_one({"user_id": user_id})
            
            # If not found by user_id, try to find by agent_id (since user_id might be used as agent_id)
            if not agent_doc:
                agent_doc = await agents_collection.find_one({"agent_id": user_id})
            
            if not agent_doc:
                return None
            
            # Create profile from database
            profile = AgentPublicProfile(
                id=str(agent_doc.get("_id", "")),
                agent_id=agent_doc.get("agent_id", ""),
                agent_name=agent_doc.get("agent_name", ""),
                slug=agent_doc.get("slug", ""),
                bio=agent_doc.get("bio", ""),
                photo=agent_doc.get("photo", ""),
                phone=agent_doc.get("phone", ""),
                email=agent_doc.get("email", ""),
                is_active=agent_doc.get("is_active", True),
                is_public=agent_doc.get("is_public", False),
                created_at=agent_doc.get("created_at"),
                updated_at=agent_doc.get("updated_at")
            )
            
            # Fetch properties for this agent
            properties = await self._get_agent_properties_from_db(profile.agent_id)
            # Add properties to the profile
            profile_dict = profile.model_dump()
            profile_dict['properties'] = [prop.model_dump() for prop in properties]
            return AgentPublicProfile(**profile_dict)
            
        except Exception as e:
            logger.error(f"Error getting agent by user ID {user_id}: {e}")
            return None
    
    async def create_agent_profile(self, agent_id: str, profile_data) -> Optional[AgentPublicProfile]:
        """Create agent public profile"""
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(profile_data, 'model_dump'):
                profile_dict = profile_data.model_dump()
            else:
                profile_dict = profile_data
            
            # Use provided slug or generate from agent name
            slug = profile_dict.get("slug") or profile_dict["agent_name"].lower().replace(" ", "-").replace(".", "-").replace("_", "-")
            
            # Create the profile
            profile = AgentPublicProfile(
                id=agent_id,
                agent_id=agent_id,
                agent_name=profile_dict["agent_name"],
                slug=slug,
                bio=profile_dict.get("bio", ""),
                photo=profile_dict.get("photo", ""),
                phone=profile_dict.get("phone", ""),
                email=profile_dict.get("email", ""),
                office_address=profile_dict.get("office_address", ""),
                specialties=profile_dict.get("specialties", []),
                experience=profile_dict.get("experience", ""),
                languages=profile_dict.get("languages", []),
                is_active=True,
                is_public=profile_dict.get("is_public", True),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                view_count=0,
                contact_count=0
            )
            
            # Store the profile in global memory (but prioritize database lookup)
            # _global_agent_profiles[slug] = profile
            # _global_agent_profiles[agent_id] = profile  # Also store by ID for lookup
            
            # Store the profile in database
            agents_collection = self.db.get_collection("agent_public_profiles")
            profile_dict = profile.model_dump()
            profile_dict['_id'] = agent_id  # Use agent_id as _id for consistency
            
            print(f"DEBUG: Storing agent profile in database: {profile_dict}")
            try:
                result = await agents_collection.insert_one(profile_dict)
                print(f"DEBUG: Database insert result: {result.inserted_id}")
            except Exception as e:
                print(f"DEBUG: Database insert error: {e}")
                # Try to update if already exists
                await agents_collection.replace_one({"_id": agent_id}, profile_dict, upsert=True)
                print(f"DEBUG: Database upsert completed")
            
            logger.info(f"Created agent profile: {profile.agent_name} with slug: {slug}")
            return profile
        except Exception as e:
            logger.error(f"Error creating agent profile: {e}")
            return None
    
    async def update_agent_profile(self, agent_id: str, profile_data: AgentPublicProfileUpdate) -> Optional[AgentPublicProfile]:
        """Update agent public profile"""
        try:
            # Mock implementation
            return await self.get_agent_by_id(agent_id)
        except Exception as e:
            logger.error(f"Error updating agent profile: {e}")
            return None
    
    async def get_agent_properties(self, agent_id: str, query_filters: PropertySearchFilters, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get agent properties with filters and pagination"""
        try:
            # Get real properties from database
            properties = await self._get_agent_properties_from_db(agent_id)
            
            # Apply filters
            filtered_properties = self._apply_property_filters(properties, query_filters)
            
            # Apply pagination
            start_index = (page - 1) * limit
            end_index = start_index + limit
            paginated_properties = filtered_properties[start_index:end_index]
            
            return {
                "properties": paginated_properties,
                "total": len(filtered_properties),
                "page": page,
                "limit": limit,
                "total_pages": (len(filtered_properties) + limit - 1) // limit
            }
        except Exception as e:
            logger.error(f"Error getting agent properties: {e}")
            return {"properties": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}
    
    async def get_agent_property(self, agent_id: str, property_id: str) -> Optional[PublicProperty]:
        """Get specific agent property"""
        try:
            # Get property from database
            properties_collection = self.db.get_collection("properties")
            
            # Convert string ID to ObjectId for MongoDB query
            from bson import ObjectId
            try:
                object_id = ObjectId(property_id)
            except Exception as e:
                print(f"DEBUG: Invalid ObjectId format: {property_id}, error: {e}")
                return None
            
            # Query for the specific property
            query = {
                "_id": object_id,
                "agent_id": agent_id,
                "publishing_status": "published"
            }
            print(f"DEBUG: Querying property with query: {query}")
            
            property_doc = await properties_collection.find_one(query)
            print(f"DEBUG: Property document found: {property_doc is not None}")
            
            if property_doc:
                # Validate property data before creating PublicProperty (relaxed validation)
                price = property_doc.get("price", 0)
                if price < 0:
                    logger.warning(f"Property {property_doc.get('_id')} has negative price {price}, setting to 0")
                    price = 0  # Set negative prices to 0
                
                return PublicProperty(
                    id=str(property_doc.get("_id", "")),
                    agent_id=property_doc.get("agent_id", ""),
                    title=property_doc.get("title", ""),
                    description=property_doc.get("description", ""),
                    price=price,
                    property_type=property_doc.get("property_type", "house"),
                    bedrooms=property_doc.get("bedrooms"),
                    bathrooms=property_doc.get("bathrooms"),
                    area=property_doc.get("area"),
                    location=property_doc.get("location", ""),
                    images=property_doc.get("images", []),
                    features=property_doc.get("features", []),
                    is_active=property_doc.get("is_active", True),
                    is_public=property_doc.get("is_public", True),
                    created_at=property_doc.get("created_at"),
                    updated_at=property_doc.get("updated_at")
                )
            
            return None
        except Exception as e:
            logger.error(f"Error getting agent property: {e}")
            return None
    
    async def get_agent_posts(self, agent_id: str, status: str = "published", limit: int = 6, skip: int = 0) -> List[dict]:
        """Get agent's posts from both regular posts and social posts collections"""
        try:
            logger.info(f"DEBUG: Getting agent posts for agent_id: {agent_id}, status: {status}")
            result = []
            
            # For consistency, also check if there are posts with the user_id as agent_id
            # This handles the case where social posts use user_id as agent_id
            user_id_as_agent_id = agent_id
            
            # Get posts from regular posts collection
            posts_collection = self.db.posts
            posts_query = {
                "agent_id": agent_id,
                "status": status
            }
            logger.info(f"DEBUG: Regular posts query: {posts_query}")
            
            posts_cursor = posts_collection.find(posts_query).sort("created_at", -1).skip(skip).limit(limit)
            posts = await posts_cursor.to_list(length=limit)
            logger.info(f"DEBUG: Found {len(posts)} regular posts")
            
            for post in posts:
                result.append({
                    "id": str(post.get("_id", "")),
                    "property_id": str(post.get("property_id", "")),  # Ensure property_id is string
                    "title": post.get("title", ""),
                    "content": post.get("content", ""),
                    "status": post.get("status", ""),
                    "created_at": str(post.get("created_at", "")),  # Ensure created_at is string
                    "media_urls": post.get("media_urls", []),
                    "channels": post.get("channels", ["website"]),  # Default to website for regular posts
                    "property_title": post.get("property_title", ""),  # Add property context
                    "language": post.get("language", "en")  # Add language field
                })
            
            # Get posts from social posts collection
            social_posts_collection = self.db.social_posts
            
            # Try to find posts with the current agent_id first
            social_posts_query = {
                "agent_id": agent_id,
                "status": status
            }
            logger.info(f"DEBUG: Social posts query (primary): {social_posts_query}")
            
            social_posts_cursor = social_posts_collection.find(social_posts_query).sort("published_at", -1).skip(skip).limit(limit)
            social_posts = await social_posts_cursor.to_list(length=limit)
            logger.info(f"DEBUG: Found {len(social_posts)} social posts with primary agent_id")
            
            # Also check for published social drafts (since our system creates drafts that get published)
            if status == "published":
                social_drafts_collection = self.db.social_drafts
                drafts_query = {
                    "agent_id": agent_id,
                    "status": "published"
                }
                logger.info(f"DEBUG: Social drafts query: {drafts_query}")
                
                drafts_cursor = social_drafts_collection.find(drafts_query).sort("published_at", -1).skip(skip).limit(limit)
                published_drafts = await drafts_cursor.to_list(length=limit)
                logger.info(f"DEBUG: Found {len(published_drafts)} published social drafts")
                
                # Add published drafts to the result
                for draft in published_drafts:
                    result.append({
                        "id": str(draft.get("_id", "")),
                        "property_id": str(draft.get("property_id", "")),
                        "title": draft.get("title", "Social Media Post"),
                        "content": draft.get("body", "Published social media content"),
                        "status": "published",
                        "created_at": str(draft.get("created_at", "")),
                        "published_at": str(draft.get("published_at", "")),
                        "media_urls": draft.get("media_ids", []),
                        "channels": [draft.get("channel", "website")],
                        "property_title": draft.get("title", ""),
                        "language": draft.get("language", "en"),
                        "platform": draft.get("channel", "website"),
                        "platform_post_id": draft.get("platform_post_id", ""),
                        "platform_post_url": draft.get("platform_post_url", "")
                    })
            
            # If no posts found with primary agent_id, try with user_id as agent_id
            if len(social_posts) == 0:
                # Check if the agent_id looks like a user_id (ObjectId format)
                from bson import ObjectId
                try:
                    # Try to convert agent_id to ObjectId to see if it's a user_id
                    user_obj_id = ObjectId(agent_id)
                    
                    # Query social posts with user_id as agent_id
                    user_posts_query = {
                        "agent_id": user_obj_id,
                        "status": status
                    }
                    logger.info(f"DEBUG: Social posts query (user_id): {user_posts_query}")
                    
                    user_posts_cursor = social_posts_collection.find(user_posts_query).sort("published_at", -1).skip(skip).limit(limit)
                    user_posts = await user_posts_cursor.to_list(length=limit)
                    logger.info(f"DEBUG: Found {len(user_posts)} social posts with user_id as agent_id")
                    
                    social_posts = user_posts
                except:
                    logger.info(f"DEBUG: Agent_id {agent_id} is not a valid ObjectId, skipping user_id lookup")
            
            for post in social_posts:
                # Get the draft to get title and content
                draft_id = post.get("draft_id")
                title = "Social Media Post"
                content = "Published social media content"
                
                if draft_id:
                    try:
                        # Try to get draft details from social_drafts collection
                        drafts_collection = self.db.social_drafts
                        draft = await drafts_collection.find_one({"_id": draft_id})
                        if draft:
                            title = draft.get("title", "Social Media Post")
                            content = draft.get("body", "Published social media content")
                    except Exception as e:
                        logger.warning(f"Could not fetch draft details for {draft_id}: {e}")
                
                # Enhance content for better social media appearance
                enhanced_title = title if title != "Social Media Post" else "🏠 New Property Alert!"
                enhanced_content = content if content != "Published social media content" else "Discover this amazing property opportunity! Perfect for investment or your dream home. Don't miss out!"
                
                result.append({
                    "id": str(post.get("_id", "")),
                    "property_id": str(post.get("property_id", post.get("_id", ""))),  # Ensure property_id is string
                    "title": enhanced_title,
                    "content": enhanced_content,
                    "status": post.get("status", ""),
                    "created_at": str(post.get("published_at", post.get("created_at", ""))),  # Ensure created_at is string
                    "media_urls": [],  # Social posts don't have media_urls in the same format
                    "channels": [post.get("platform", "social")],  # Add channels field with platform
                    "property_title": "Beautiful Property in Prime Location",  # Add property context
                    "language": "en"  # Add language field
                })
            
            # Sort all results by created_at/published_at and apply limit
            result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            logger.info(f"DEBUG: Returning {len(result[:limit])} total posts")
            return result[:limit]
        
        except Exception as e:
            logger.error(f"Error getting agent posts: {e}")
            return []

    async def get_agent_post(self, agent_id: str, post_id: str, status: str = "published") -> Optional[dict]:
        """Get a single agent post by ID from both regular posts and social posts collections"""
        try:
            logger.info(f"DEBUG: Getting agent post for agent_id: {agent_id}, post_id: {post_id}, status: {status}")
            
            # Try to find post in regular posts collection
            posts_collection = self.db.posts
            posts_query = {
                "_id": ObjectId(post_id),
                "agent_id": agent_id,
                "status": status
            }
            logger.info(f"DEBUG: Regular posts query: {posts_query}")
            
            post = await posts_collection.find_one(posts_query)
            if post:
                logger.info(f"DEBUG: Found post in regular posts collection")
                return {
                    "id": str(post.get("_id", "")),
                    "title": post.get("title", ""),
                    "content": post.get("content", ""),
                    "status": post.get("status", ""),
                    "created_at": post.get("created_at"),
                    "media_urls": post.get("media_urls", []),
                    "channels": post.get("channels", ["website"]),
                    "property_title": post.get("property_title", ""),
                    "language": post.get("language", "en")
                }
            
            # Try to find post in social posts collection
            social_posts_collection = self.db.social_posts
            social_posts_query = {
                "_id": ObjectId(post_id),
                "agent_id": agent_id,
                "status": status
            }
            logger.info(f"DEBUG: Social posts query: {social_posts_query}")
            
            social_post = await social_posts_collection.find_one(social_posts_query)
            if social_post:
                logger.info(f"DEBUG: Found post in social posts collection")
                
                # Try to get enhanced content from draft if available
                title = "Social Media Post"
                content = "Published social media content"
                draft_id = social_post.get("draft_id")
                
                if draft_id:
                    try:
                        drafts_collection = self.db.social_drafts
                        draft = await drafts_collection.find_one({"_id": draft_id})
                        if draft:
                            title = draft.get("title", "Social Media Post")
                            content = draft.get("body", "Published social media content")
                    except Exception as e:
                        logger.warning(f"Could not fetch draft details for {draft_id}: {e}")
                
                # Enhance content for better social media appearance
                enhanced_title = title if title != "Social Media Post" else "🏠 New Property Alert!"
                enhanced_content = content if content != "Published social media content" else "Discover this amazing property opportunity! Perfect for investment or your dream home. Don't miss out!"
                
                return {
                    "id": str(social_post.get("_id", "")),
                    "title": enhanced_title,
                    "content": enhanced_content,
                    "status": social_post.get("status", ""),
                    "created_at": social_post.get("published_at", social_post.get("created_at")),
                    "media_urls": [],
                    "channels": [social_post.get("platform", "social")],
                    "property_title": "Beautiful Property in Prime Location",
                    "language": "en"
                }
            
            # If still not found, try with user_id as agent_id for social posts
            # Check if the agent_id looks like a user_id (ObjectId format)
            try:
                # Try to convert agent_id to ObjectId to see if it's a user_id
                user_obj_id = ObjectId(agent_id)
                
                # Query social posts with user_id as agent_id
                social_posts_query_user = {
                    "_id": ObjectId(post_id),
                    "agent_id": user_obj_id,
                    "status": status
                }
                logger.info(f"DEBUG: Social posts query (user_id fallback): {social_posts_query_user}")
                
                social_post_user = await social_posts_collection.find_one(social_posts_query_user)
                if social_post_user:
                    logger.info(f"DEBUG: Found post in social posts collection with user_id fallback")
                    
                    # Try to get enhanced content from draft if available
                    title = "Social Media Post"
                    content = "Published social media content"
                    draft_id = social_post_user.get("draft_id")
                    
                    if draft_id:
                        try:
                            drafts_collection = self.db.social_drafts
                            draft = await drafts_collection.find_one({"_id": draft_id})
                            if draft:
                                title = draft.get("title", "Social Media Post")
                                content = draft.get("body", "Published social media content")
                        except Exception as e:
                            logger.warning(f"Could not fetch draft details for {draft_id}: {e}")
                    
                    # Enhance content for better social media appearance
                    enhanced_title = title if title != "Social Media Post" else "🏠 New Property Alert!"
                    enhanced_content = content if content != "Published social media content" else "Discover this amazing property opportunity! Perfect for investment or your dream home. Don't miss out!"
                    
                    return {
                        "id": str(social_post_user.get("_id", "")),
                        "title": enhanced_title,
                        "content": enhanced_content,
                        "status": social_post_user.get("status", ""),
                        "created_at": social_post_user.get("published_at", social_post_user.get("created_at")),
                        "media_urls": [],
                        "channels": [social_post_user.get("platform", "social")],
                        "property_title": "Beautiful Property in Prime Location",
                        "language": "en"
                    }
            except Exception as e:
                logger.warning(f"Could not convert agent_id to ObjectId: {e}")
            
            logger.warning(f"DEBUG: No post found with ID {post_id} for agent {agent_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent post: {e}")
            return None

    async def create_contact_inquiry(self, agent_id: str, inquiry_data: ContactInquiryCreate) -> Optional[ContactInquiry]:
        """Create contact inquiry"""
        try:
            # Mock implementation
            return ContactInquiry(
                id="1",
                agent_id=agent_id,
                name=inquiry_data.name,
                email=inquiry_data.email,
                phone=inquiry_data.phone,
                message=inquiry_data.message,
                inquiry_type=inquiry_data.inquiry_type,
                property_id=inquiry_data.property_id,
                created_at=datetime.now(),
                is_read=False,
                is_responded=False
            )
        except Exception as e:
            logger.error(f"Error creating contact inquiry: {e}")
            return None
    
    async def increment_view_count(self, agent_id: str) -> bool:
        """Increment agent view count"""
        try:
            # Mock implementation - in real app, update database
            logger.info(f"Incremented view count for agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error incrementing view count: {e}")
            return False
    
    async def increment_contact_count(self, agent_id: str) -> bool:
        """Increment agent contact count"""
        try:
            # Mock implementation - in real app, update database
            logger.info(f"Incremented contact count for agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error incrementing contact count: {e}")
            return False
    
    async def increment_property_view_count(self, property_id: str) -> bool:
        """Increment property view count"""
        try:
            # Mock implementation - in real app, update database
            logger.info(f"Incremented view count for property {property_id}")
            return True
        except Exception as e:
            logger.error(f"Error incrementing property view count: {e}")
            return False
    
    async def track_contact_action(self, agent_id: str, action_data: dict) -> bool:
        """Track contact-related actions"""
        try:
            # Mock implementation - in real app, log to database
            logger.info(f"Tracked contact action for agent {agent_id}: {action_data}")
            return True
        except Exception as e:
            logger.error(f"Error tracking contact action: {e}")
            return False
    
    async def get_agent_stats(self, agent_id: str) -> dict:
        """Get agent statistics"""
        try:
            # Mock implementation
            return {
                "total_views": 0,
                "total_contacts": 0,
                "properties_count": 1,
                "recent_inquiries": 0
            }
        except Exception as e:
            logger.error(f"Error getting agent stats: {e}")
            return {
                "total_views": 0,
                "total_contacts": 0,
                "properties_count": 0,
                "recent_inquiries": 0
            }