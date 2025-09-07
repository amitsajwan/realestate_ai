"""
Application Routes
=================
All route definitions and endpoint setup
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
# Removed duplicate smart_properties import - using unified_properties now
from app.dependencies import get_current_user


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
            from app.logging_config import get_logger
            logger = get_logger(__name__)
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
    async def ai_property_suggest(request):
        """AI-powered property suggestion endpoint with agent profile integration"""
        try:
            from app.logging_config import get_logger
            logger = get_logger(__name__)

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
            property_type = body.get("property_type", "Apartment") if body else "Apartment"
            location = body.get("location", "City Center") if body else "City Center"
            budget = body.get("budget", "₹50,00,000") if body else "₹50,00,000"
            requirements = body.get("requirements", "Modern amenities") if body else "Modern amenities"
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
            from app.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error fetching agent profile: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
