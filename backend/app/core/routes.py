"""
Application Routes
=================
All route definitions and endpoint setup
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
# Removed duplicate smart_properties import - using unified_properties now
from app.dependencies import get_current_user


class AIPropertySuggestRequest(BaseModel):
    """Request model for AI property suggestions"""
    address: Optional[str] = None
    location: Optional[str] = None
    property_type: Optional[str] = "Apartment"
    bedrooms: Optional[int] = 2
    bathrooms: Optional[int] = 2
    area: Optional[int] = 1000
    price: Optional[str] = None
    budget: Optional[str] = None
    requirements: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None
    agent_profile: Optional[Dict[str, Any]] = None


def setup_routes(app: FastAPI):
    """Setup all application routes"""

    # Include all API V1 routers
    from app.api.v1.router import api_router
    from app.api.v1.endpoints import simple_auth

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(simple_auth.router)

    # Mount static files for uploads
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


def setup_additional_endpoints(app: FastAPI):
    """Setup additional endpoints that don't fit in the main API router"""
    
    # Removed duplicate generate-property endpoint - using unified properties now

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "message": "PropertyAI API is running"}

    @app.get("/api/v1/dashboard/stats")
    async def get_dashboard_stats():
        """Get dashboard statistics from MongoDB"""
        try:
            from app.core.database import get_database
            db = await get_database()

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
                "data": stats
            }

        except Exception as e:
            from app.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error getting dashboard stats: {e}")
            # Fallback to mock data if MongoDB fails
            stats = {
                "total_properties": 12,
                "active_listings": 8,
                "total_leads": 0,
                "total_users": 1,
                "total_views": 1247,
                "monthly_leads": 23,
                "revenue": "₹45,00,000"
            }
            return {
                "success": True,
                "data": stats
            }

    @app.post("/api/v1/property/ai_suggest")
    async def ai_property_suggest(request_data: AIPropertySuggestRequest):
        """AI-powered property suggestion endpoint with agent profile integration"""
        try:
            from app.logging_config import get_logger
            logger = get_logger(__name__)

            logger.info("Starting AI property suggestion processing")

            # Get request data
            logger.info(f"Request data: {request_data}")

            logger.info("Extracting basic property details")
            # Extract property details from the request model
            property_type = request_data.property_type or "Apartment"
            location = request_data.location or request_data.address or "City Center"
            requirements = request_data.requirements or "Modern amenities"
            
            # Extract additional property details
            bedrooms = request_data.bedrooms or 2
            bathrooms = request_data.bathrooms or 2
            area = request_data.area or 1000
            
            # Improved price/budget handling
            budget = request_data.budget or request_data.price
            logger.info(f"Raw budget/price input: {budget}")
            
            # Parse budget/price with better logic
            budget_amount = None
            if budget:
                try:
                    # Handle different price formats
                    if isinstance(budget, (int, float)):
                        budget_amount = float(budget)
                    elif isinstance(budget, str):
                        # Remove currency symbols and commas
                        clean_budget = budget.replace('₹', '').replace(',', '').replace(' ', '').strip()
                        # Handle 'L' or 'Cr' suffixes
                        if clean_budget.lower().endswith('l'):
                            budget_amount = float(clean_budget[:-1]) * 100000  # Convert lakhs to rupees
                        elif clean_budget.lower().endswith('cr'):
                            budget_amount = float(clean_budget[:-2]) * 10000000  # Convert crores to rupees
                        else:
                            budget_amount = float(clean_budget)
                    logger.info(f"Successfully parsed budget amount: {budget_amount}")
                except Exception as budget_error:
                    logger.error(f"Error parsing budget '{budget}': {budget_error}")
                    budget_amount = None
            
            # Only use default if no valid price was provided
            if budget_amount is None:
                # Calculate a reasonable default based on property type and area
                base_price_per_sqft = {
                    "Apartment": 5000,
                    "House": 4000,
                    "Villa": 8000,
                    "Commercial": 6000,
                    "Plot": 2000
                }
                price_per_sqft = base_price_per_sqft.get(property_type, 5000)
                budget_amount = area * price_per_sqft
                logger.info(f"No valid price provided, calculated default based on {property_type} and {area} sqft: {budget_amount}")
            
            logger.info(f"Basic details - Type: {property_type}, Location: {location}, Budget: {budget_amount}, Requirements: {requirements}")
            logger.info(f"Property details - Bedrooms: {bedrooms}, Bathrooms: {bathrooms}, Area: {area}")

            # Get agent profile data for personalized suggestions
            logger.info("Processing agent profile data")
            agent_profile = request_data.agent_profile or {}
            logger.info(f"Agent profile: {agent_profile}")

            specialization = agent_profile.get("specialization", "residential") if isinstance(agent_profile, dict) else "residential"
            areas_served = agent_profile.get("areas_served", "") if isinstance(agent_profile, dict) else ""
            brand_name = agent_profile.get("brand_name", "") if isinstance(agent_profile, dict) else ""
            experience_level = agent_profile.get("experience_level", "intermediate") if isinstance(agent_profile, dict) else "intermediate"
            tagline = agent_profile.get("tagline", "") if isinstance(agent_profile, dict) else ""
            bio = agent_profile.get("bio", "") if isinstance(agent_profile, dict) else ""
            languages = agent_profile.get("languages", []) if isinstance(agent_profile, dict) else []
            logger.info(f"Extracted agent profile fields - Specialization: {specialization}, Experience: {experience_level}")

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
                        "title": f"{title_prefix}Beautiful {bedrooms}BHK {property_type} in {location}",
                        "price": budget_amount,
                        "description": specialized_desc + location_insights.get('description_suffix', ''),
                        "amenities": specialized_amenities,
                        "location_score": location_insights.get('score', 8.0),
                        "market_insights": location_insights.get('market_data', {}),
                        "property_details": {
                            "bedrooms": bedrooms,
                            "bathrooms": bathrooms,
                            "area": area,
                            "property_type": property_type,
                            "location": location
                        },
                        "highlights": [
                            f"Spacious {bedrooms}BHK with {bathrooms} bathrooms",
                            f"Area: {area} sq ft",
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
            from app.logging_config import get_logger
            logger = get_logger(__name__)
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
            from app.services.agent_profile_service import AgentProfileService
            agent_service = AgentProfileService()

            # Try to get profile by user_id first, then by email
            user_id = getattr(current_user, "id", None) or str(getattr(current_user, "_id", ""))
            email = getattr(current_user, "email", None)

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
            from app.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error fetching agent profile: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
