from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserSecureResponse
from app.models.user import User
from app.core.database import get_database
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-public", tags=["agent-public"])

@router.get("/profile")
async def get_public_profile():
    try:
        # Get the database connection
        db = get_database()
        users_collection = db.users
        
        # Get the most recently updated user (likely the one who just completed onboarding)
        # TODO: This should be configurable or based on a specific agent ID
        logger.info("Searching for users in database...")
        user = await users_collection.find_one(
            {"is_active": True, "onboardingCompleted": True},
            sort=[("updated_at", -1)]  # Get most recently updated
        )
        
        if not user:
            # Let's check what users exist
            all_users = await users_collection.find({}).limit(5).to_list(5)
            logger.warning(f"No active user found. Available users: {[str(u.get('_id')) + ' - ' + str(u.get('is_active', 'no_is_active_field')) for u in all_users]}")
            
            # Try to get any user as fallback
            user = await users_collection.find_one({})
            if not user:
                logger.error("No users found in database at all!")
                return UserSecureResponse(
                    id="dummy_id",
                    first_name="John",
                    last_name="Doe",
                    is_active=True
                )
            else:
                logger.info(f"Using fallback user: {str(user.get('_id'))}")
        else:
            logger.info(f"Found active user: {str(user.get('_id'))}")
        
        # Debug: Log the user data structure
        logger.info(f"User data fields: {list(user.keys())}")
        logger.info(f"User first_name: {user.get('first_name', 'NOT_FOUND')}")
        logger.info(f"User last_name: {user.get('last_name', 'NOT_FOUND')}")
        logger.info(f"User is_active: {user.get('is_active', 'NOT_FOUND')}")
        
        # Convert MongoDB user to response format
        # Handle None values by providing defaults
        first_name = user.get("first_name") or ""
        last_name = user.get("last_name") or ""
        
        # Return comprehensive profile data for public website
        return {
            "id": str(user["_id"]),
            "first_name": first_name,
            "last_name": last_name,
            "is_active": user.get("is_active", False),
            "email": user.get("email", ""),
            "phone": user.get("phone", ""),
            "company": user.get("company", ""),
            "office_address": user.get("address", ""),
            "experience": str(user.get("experience_years", "0")),
            "professional_bio": user.get("about", ""),
            "specialization_areas": user.get("specialization_areas", ""),
            "tagline": user.get("tagline", ""),
            "city": user.get("city", ""),
            "state": user.get("state", ""),
            "pincode": user.get("pincode", "")
        }
        
    except Exception as e:
        logger.error(f"Error getting public profile: {str(e)}")
        # Fallback to dummy data on error
        return {
            "id": "dummy_id",
            "first_name": "John",
            "last_name": "Doe",
            "is_active": True,
            "email": "john.doe@example.com",
            "phone": "+1 (555) 123-4567",
            "company": "Example Real Estate",
            "office_address": "123 Main St, City, State 12345",
            "experience": "5",
            "professional_bio": "Experienced real estate professional with 5+ years in the industry.",
            "specialization_areas": "Residential, Commercial",
            "tagline": "Your Dream Home Awaits",
            "city": "City",
            "state": "State",
            "pincode": "12345"
        }

@router.put("/profile")
async def update_public_profile(profile_data: dict):
    """Update public profile data"""
    try:
        # Get the database connection
        db = get_database()
        users_collection = db.users
        
        # Get the most recently updated user (likely the one who just completed onboarding)
        user = await users_collection.find_one(
            {"is_active": True, "onboardingCompleted": True},
            sort=[("updated_at", -1)]
        )
        
        if not user:
            logger.error("No user found to update profile")
            return {"success": False, "message": "No user found"}
        
        # Map frontend data to database fields
        update_data = {
            "first_name": profile_data.get("agent_name", "").split(" ")[0] if profile_data.get("agent_name") else "",
            "last_name": " ".join(profile_data.get("agent_name", "").split(" ")[1:]) if profile_data.get("agent_name") and len(profile_data.get("agent_name", "").split(" ")) > 1 else "",
            "email": profile_data.get("email", ""),
            "phone": profile_data.get("phone", ""),
            "company": profile_data.get("company", ""),
            "address": profile_data.get("office_address", ""),
            "experience_years": profile_data.get("experience", "0"),
            "about": profile_data.get("bio", ""),
            "specialization_areas": ", ".join(profile_data.get("specialties", [])),
            "tagline": profile_data.get("tagline", ""),
            "is_public": profile_data.get("is_public", False),
            "updated_at": datetime.utcnow()
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Update the user
        result = await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Successfully updated public profile for user {user['_id']}")
            return {"success": True, "message": "Profile updated successfully"}
        else:
            logger.warning(f"No changes made to profile for user {user['_id']}")
            return {"success": True, "message": "No changes made"}
            
    except Exception as e:
        logger.error(f"Error updating public profile: {str(e)}")
        return {"success": False, "message": f"Error updating profile: {str(e)}"}

@router.get("/stats")
async def get_public_stats():
    try:
        # Get the database connection
        db = get_database()
        properties_collection = db.properties
        users_collection = db.users
        
        # Get real stats from database
        total_properties = await properties_collection.count_documents({})
        active_listings = await properties_collection.count_documents({"status": "active"})
        
        # Get user experience (assuming years_experience field exists)
        user = await users_collection.find_one({"is_active": True})
        years_experience = user.get("years_experience", 5) if user else 5
        
        return {
            "total_properties": total_properties,
            "active_listings": active_listings,
            "years_experience": years_experience
        }
        
    except Exception as e:
        logger.error(f"Error getting public stats: {str(e)}")
        # Fallback to dummy data on error
        return {
            "total_properties": 10,
            "active_listings": 5,
            "years_experience": 5
        }
