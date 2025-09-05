#!/usr/bin/env python3
"""
PropertyAI - Main Application
=============================
FastAPI application for AI-powered real estate platform
"""

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
# Removed FileResponse import to avoid serving UI from backend
import logging
import re
import time
import uuid
import json
from datetime import datetime
from typing import Callable
from app.routers import listings, user_profile
from app.api.v1.endpoints import simple_auth
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.services.agent_profile_service import AgentProfileService
from app.dependencies import get_current_user
from app.logging_config import (
    setup_comprehensive_logging, 
    get_logger, 
    log_api_request, 
    log_api_response,
    log_security_event
)

# Initialize comprehensive logging
setup_comprehensive_logging()
logger = get_logger(__name__)
api_logger = get_logger("api_access")
security_logger = get_logger("security")

# Set specific loggers to DEBUG level
for module in ['app.services.auth_service', 'app.repositories.user_repository', 'app.api.v1.endpoints.auth']:
    logging.getLogger(module).setLevel(logging.DEBUG)

# Create FastAPI app
app = FastAPI(
    title="PropertyAI API",
    description="AI-powered real estate platform API",
    version="2.0.0"
)

# Dynamic CORS origins function
def get_cors_origins():
    """Get allowed CORS origins including dynamic ngrok URLs"""
    import os
    
    # Base origins for development
    base_origins = [
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:3001",  # Next.js frontend (alternative port)
        "http://localhost:8000",  # Backend
    ]
    
    # Add custom origins from environment variable
    custom_origins = os.getenv("CORS_ORIGINS", "")
    if custom_origins:
        base_origins.extend([origin.strip() for origin in custom_origins.split(",")])
    
    return base_origins

def is_allowed_origin(origin: str) -> bool:
    """Check if origin is allowed (including ngrok patterns)"""
    if not origin:
        return False
        
    allowed_patterns = [
        r"^https://[a-zA-Z0-9-]+\.ngrok-free\.app$",
        r"^https://[a-zA-Z0-9-]+\.ngrok\.io$",
        r"^http://localhost:\d+$",
    ]
    
    # Check exact matches first
    if origin in get_cors_origins():
        return True
        
    # Check patterns
    for pattern in allowed_patterns:
        if re.match(pattern, origin):
            return True
            
    return False

# Environment-based CORS configuration
import os
if os.getenv("ENVIRONMENT") == "production":
    # Production: Use strict origin checking
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https://[a-zA-Z0-9-]+\.(ngrok-free\.app|ngrok\.io)$|^http://localhost:\d+$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
else:
    # Development: Allow all origins for easier development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
        "https://776674ff2a3f.ngrok-free.app",
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:3001",  # Next.js frontend (alt port)
        "http://localhost:3002",  # Next.js frontend (alt port)
        "http://localhost:3003",  # Next.js frontend (alt port)
        "http://localhost:3004",  # Next.js frontend (current port)
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://127.0.0.1:3004",  # Alternative localhost (current port)
        "http://localhost:8000",  # Backend self-reference
        "http://127.0.0.1:8000"
    ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Comprehensive Logging Middleware
@app.middleware("http")
async def comprehensive_logging_middleware(request: Request, call_next: Callable) -> Response:
    """Comprehensive logging middleware for all HTTP requests"""
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # Extract client information
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    method = request.method
    url = str(request.url)
    endpoint = request.url.path
    
    # Extract user information if available
    user_id = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            # Try to extract user info from token (simplified)
            token = auth_header.split(" ")[1]
            # In a real implementation, you'd decode the JWT here
            user_id = "authenticated_user"  # Placeholder
        except Exception:
            pass
    
    # Log request details
    request_data = {
        "request_id": request_id,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "content_length": request.headers.get("content-length", 0)
    }
    
    log_api_request(
        api_logger, 
        method, 
        endpoint, 
        user_id=user_id,
        **request_data
    )
    
    # Security logging for sensitive endpoints
    if any(sensitive in endpoint.lower() for sensitive in ['/auth/', '/login', '/register', '/password']):
        log_security_event(
            "auth_attempt",
            user_id=user_id,
            ip_address=client_ip,
            details={
                "endpoint": endpoint,
                "method": method,
                "user_agent": user_agent,
                "request_id": request_id
            }
        )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        response_data = {
            "client_ip": client_ip,
            "response_size": response.headers.get("content-length", 0)
        }
        
        log_api_response(
            api_logger,
            method,
            endpoint,
            response.status_code,
            duration,
            user_id=user_id,
            request_id=request_id,
            **response_data
        )
        
        # Log security events for failed auth attempts
        if response.status_code in [401, 403] and any(sensitive in endpoint.lower() for sensitive in ['/auth/', '/login']):
            log_security_event(
                "auth_failure",
                user_id=user_id,
                ip_address=client_ip,
                details={
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "request_id": request_id
                }
            )
        
        # Add request ID to response headers for tracing
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        # Calculate duration even for errors
        duration = time.time() - start_time
        
        # Log error
        logger.error(
            f"Request failed: {method} {endpoint}",
            extra={
                "request_id": request_id,
                "client_ip": client_ip,
                "user_id": user_id,
                "duration": duration,
                "error_details": str(e),
                "method": method,
                "endpoint": endpoint
            },
            exc_info=True
        )
        
        # Log security event for suspicious errors
        if "sql" in str(e).lower() or "injection" in str(e).lower():
            log_security_event(
                "potential_attack",
                user_id=user_id,
                ip_address=client_ip,
                details={
                    "endpoint": endpoint,
                    "method": method,
                    "error": str(e),
                    "request_id": request_id
                }
            )
        
        # Re-raise the exception
        raise

# MongoDB Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize MongoDB connection on startup"""
    try:
        await connect_to_mongo()
        logger.info("🚀 MongoDB connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    try:
        await close_mongo_connection()
        logger.info("📊 MongoDB connection closed")
    except Exception as e:
        logger.error(f"❌ Error closing MongoDB connection: {e}")

# Include all API V1 routers
app.include_router(api_router, prefix="/api/v1")

# Include simple auth router for demo login
app.include_router(simple_auth.router)

# Add generate-property endpoint directly for frontend compatibility
from app.api.v1.endpoints.smart_properties import SmartPropertyCreate, SmartPropertyResponse, generate_simple_ai_content, get_smart_property_service

@app.post("/api/generate-property", response_model=SmartPropertyResponse)
async def generate_property_direct(
    prop: SmartPropertyCreate,
    current_user: dict = Depends(get_current_user)
):
    """Generate property content - direct endpoint for frontend compatibility"""
    try:
        logger.info(f"Generating property content for user: {current_user.get('username', 'anonymous')}")

        # Get user ID
        user_id = current_user.get("username") or current_user.get("user_id") or str(current_user.get("_id", "anonymous"))

        # Generate AI content if requested
        ai_content = None
        if prop.ai_generate:
            ai_content = generate_simple_ai_content(prop.model_dump(), prop.template, prop.language)

        # Create property data with AI content
        property_data = prop.model_dump()
        property_data["ai_content"] = ai_content

        # Use the proper MongoDB service
        result = await get_smart_property_service().create_smart_property(
            SmartPropertyCreate(**property_data),
            user_id
        )

        logger.info(f"Property generated successfully with ID: {result.id}")
        return result

    except Exception as e:
        logger.error(f"Error generating property: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate property: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "PropertyAI API is running"}

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics from MongoDB"""
    try:
        from app.core.database import get_database
        db = get_database()
        
        # Get real stats from MongoDB
        total_properties = await db.properties.count_documents({})
        active_listings = await db.properties.count_documents({"status": "available"})
        total_leads = await db.leads.count_documents({})
        total_users = await db.users.count_documents({})
        
        stats = {
            "total_properties": total_properties,
            "active_listings": active_listings,
            "total_leads": total_leads,
            "total_users": total_users,
            "total_views": 1247,  # Mock for now
            "monthly_leads": 23,  # Mock for now
            "revenue": "₹45,00,000"  # Mock for now
        }
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        # Fallback to mock data if MongoDB fails
        stats = {
            "total_properties": 12,
            "active_listings": 8,
            "pending_posts": 3,
            "total_views": 1247,
            "monthly_leads": 23,
            "revenue": "₹45,00,000"
        }
        return {
            "success": True,
            "stats": stats
        }

@app.post("/api/v1/property/ai_suggest")
async def ai_property_suggest(request: Request):
    """AI-powered property suggestion endpoint with agent profile integration"""
    try:
        logger.info("Starting AI property suggestion processing")
        
        # Get request body with error handling
        try:
            body = await request.json()
            logger.info(f"Successfully parsed JSON body: {body}")
        except Exception as json_error:
            logger.error(f"Failed to parse JSON body: {json_error}")
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")
        
        if body is None:
            logger.error("Request body is None")
            raise HTTPException(status_code=400, detail="Request body is required")
        
        logger.info("Extracting basic property details")
        property_type = body.get("property_type", "Apartment")
        location = body.get("location", "City Center")
        budget = body.get("budget", "₹50,00,000")
        requirements = body.get("requirements", "Modern amenities")
        logger.info(f"Basic details - Type: {property_type}, Location: {location}, Budget: {budget}, Requirements: {requirements}")
        
        # Get agent profile data for personalized suggestions
        logger.info("Processing agent profile data")
        agent_profile = body.get("agent_profile", {})
        if agent_profile is None:
            agent_profile = {}
        logger.info(f"Agent profile: {agent_profile}")
        
        specialization = agent_profile.get("specialization", "residential") if isinstance(agent_profile, dict) else "residential"
        areas_served = agent_profile.get("areas_served", "") if isinstance(agent_profile, dict) else ""
        brand_name = agent_profile.get("brand_name", "") if isinstance(agent_profile, dict) else ""
        experience_level = agent_profile.get("experience_level", "intermediate") if isinstance(agent_profile, dict) else "intermediate"
        tagline = agent_profile.get("tagline", "") if isinstance(agent_profile, dict) else ""
        bio = agent_profile.get("bio", "") if isinstance(agent_profile, dict) else ""
        languages = agent_profile.get("languages", []) if isinstance(agent_profile, dict) else []
        logger.info(f"Extracted agent profile fields - Specialization: {specialization}, Experience: {experience_level}")
        
        # Parse budget safely
        logger.info("Parsing budget amount")
        try:
            budget_amount = int(budget.replace('₹', '').replace(',', ''))
            logger.info(f"Parsed budget amount: {budget_amount}")
        except Exception as budget_error:
            logger.error(f"Error parsing budget '{budget}': {budget_error}")
            budget_amount = 5000000  # Default to 50 lakhs
            logger.info(f"Using default budget amount: {budget_amount}")
        
        # Generate agent-aware content based on specialization and brand
        logger.info("Generating agent-aware content")
        def get_content_style(spec, exp_level, bio_text):
            """Get content style based on agent profile"""
            logger.info(f"Getting content style for spec: {spec}, exp_level: {exp_level}")
            styles = {
                "luxury": {
                    "description_prefix": "Exquisite luxury",
                    "amenities_focus": "premium amenities, concierge services, high-end finishes",
                    "tone": "sophisticated"
                },
                "commercial": {
                    "description_prefix": "Prime commercial",
                    "amenities_focus": "business facilities, parking, accessibility features",
                    "tone": "professional"
                },
                "investment": {
                    "description_prefix": "High-yield investment",
                    "amenities_focus": "ROI-focused features, rental potential, strategic location",
                    "tone": "analytical"
                },
                "residential": {
                    "description_prefix": "Beautiful family",
                    "amenities_focus": "family-friendly amenities, schools nearby, parks",
                    "tone": "warm"
                }
            }
            
            base_style = styles.get(spec, styles["residential"])
            
            # Adjust based on experience level
            if exp_level == "expert" and "luxury" not in base_style["description_prefix"]:
                base_style["description_prefix"] = f"Premium {base_style['description_prefix'].lower()}"
            
            return base_style
        
        def get_specialized_description(prop_type, spec, location, requirements, exp_level, bio_text):
            content_style = get_content_style(spec, exp_level, bio_text)
            tone = content_style["tone"]
            prefix = content_style["description_prefix"]
            
            # Handle None requirements
            req_text = requirements if requirements else "modern amenities"
            
            if tone == "sophisticated":
                return f"{prefix} {prop_type.lower()} offering unparalleled luxury in {location}. {req_text} with premium finishes and exclusive amenities."
            elif tone == "professional":
                return f"{prefix} {prop_type.lower()} in {location}. Excellent for business with {req_text.lower()} and strategic location."
            elif tone == "analytical":
                return f"{prefix} {prop_type.lower()} in {location}. Great ROI potential with {req_text.lower()} and strong rental demand."
            else:
                return f"{prefix} {prop_type.lower()} in {location} with {req_text.lower()}. Perfect for families seeking comfort and convenience."
        
        def get_specialized_amenities(spec, languages_list):
            base_amenities = {
                "luxury": "Concierge Service, Valet Parking, Private Elevator, Wine Cellar, Spa, Infinity Pool",
                "commercial": "High-Speed Internet, Conference Rooms, Reception Area, Parking, Security, HVAC",
                "investment": "Low Maintenance, High Rental Yield, Strategic Location, Modern Amenities, Security",
                "residential": "Parking, Gym, Swimming Pool, 24/7 Security, Garden, Children's Play Area"
            }
            
            amenities = base_amenities.get(spec, base_amenities["residential"])
            
            # Add multilingual support if agent speaks multiple languages
            if len(languages_list) > 1:
                amenities += ", Multilingual Support"
            
            return amenities
        
        def get_title_prefix(brand, tag, spec):
            """Generate title prefix based on agent branding"""
            if brand:
                return f"{brand} Presents: "
            elif tag:
                return f"{tag} - "
            elif spec == "luxury":
                return "Luxury Collection: "
            elif spec == "commercial":
                return "Commercial Excellence: "
            else:
                return ""
        
        # Generate personalized title with brand consideration
        title_prefix = get_title_prefix(brand_name, tagline, specialization)
        
        logger.info("Generating specialized content")
        specialized_desc = get_specialized_description(property_type, specialization, location, requirements, experience_level, bio)
        logger.info(f"Generated specialized description: {specialized_desc[:100]}...")
        
        specialized_amenities = get_specialized_amenities(specialization, languages)
        logger.info(f"Generated specialized amenities: {specialized_amenities}")
        
        # Add location intelligence based on agent's areas served
        def _get_location_insights(location, areas_served, specialization):
            """Generate location insights based on agent's expertise"""
            score = 8.5  # Default score
            description_suffix = ""
            market_data = {}
            
            if areas_served and location and location.lower() in areas_served.lower():
                score = 9.2
                description_suffix = " Agent has extensive local market knowledge in this area."
                market_data = {
                    "local_expertise": True,
                    "market_trend": "Growing",
                    "price_trend": "Stable"
                }
            else:
                market_data = {
                    "local_expertise": False,
                    "market_trend": "Stable",
                    "price_trend": "Moderate"
                }
            
            return {
                "score": score,
                "description_suffix": description_suffix,
                "market_data": market_data
            }
        
        logger.info("Getting location insights")
        location_insights = _get_location_insights(location, areas_served, specialization)
        logger.info(f"Generated location insights: {location_insights}")
        
        # Ensure location_insights is not None
        if location_insights is None:
            logger.warning("Location insights is None, using defaults")
            location_insights = {
                "score": 8.0,
                "description_suffix": "",
                "market_data": {
                    "local_expertise": False,
                    "market_trend": "Stable",
                    "price_trend": "Moderate"
                }
            }
        
        # Mock AI suggestions with agent profile integration
        logger.info("Building final suggestions response")
        suggestions = {
            "success": True,
            "data": [
                {
                    "title": f"{title_prefix}Beautiful {property_type} in {location}",
                    "price": budget,
                    "description": specialized_desc + location_insights.get('description_suffix', ''),
                    "amenities": specialized_amenities,
                    "location_score": location_insights.get('score', 8.0),
                    "market_insights": location_insights.get('market_data', {}),
                    "highlights": [
                        "Prime location with excellent connectivity",
                        f"Tailored for {specialization} market",
                        "Professional agent-curated listing",
                        "Close to schools, hospitals, and shopping centers"
                    ]
                }
            ]
        }
        
        logger.info("Successfully generated AI property suggestions")
        return suggestions
        
    except Exception as e:
        logger.error(f"Error in AI property suggestion: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/agent/profile")
async def get_agent_profile(current_user: dict = Depends(get_current_user)):
    """Get agent profile for current user"""
    try:
        agent_service = AgentProfileService()
        
        # Try to get profile by user_id first, then by email
        user_id = current_user.get("user_id") or str(current_user.get("_id", ""))
        email = current_user.get("email")
        
        profile = None
        if user_id:
            profile = await agent_service.get_agent_profile_by_user_id(user_id)
        
        if not profile and email:
            profile = await agent_service.get_agent_profile_by_email(email)
        
        if profile:
            formatted_profile = agent_service.format_agent_profile_for_ai(profile)
            return {
                "success": True,
                "data": formatted_profile
            }
        else:
            # Return default profile if no agent profile exists
            default_profile = agent_service.format_agent_profile_for_ai(None)
            return {
                "success": True,
                "data": default_profile,
                "message": "No agent profile found, using defaults"
            }
            
    except Exception as e:
        logger.error(f"Error fetching agent profile: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Removed catch-all route that served the frontend UI to ensure backend remains a pure API

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




