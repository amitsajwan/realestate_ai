from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.services.ai_service import AIService
from app.config import branding
import hashlib
import secrets
import logging
from datetime import datetime
from app.models.property import Property

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent with AI-powered onboarding"""
        try:
            # Check if email already exists
            existing_agent = self.db.query(Agent).filter(Agent.email == agent_data['email']).first()
            if existing_agent:
                raise ValueError("Email already registered")
            
            # Hash password
            password_hash = self._hash_password(agent_data['password'])
            
            # Create agent object
            agent = Agent(
                email=agent_data['email'],
                password_hash=password_hash,
                first_name=agent_data['first_name'],
                last_name=agent_data['last_name'],
                phone=agent_data.get('phone'),
                license_number=agent_data.get('license_number'),
                years_experience=agent_data.get('years_experience', 0),
                specializations=agent_data.get('specializations', []),
                service_areas=agent_data.get('service_areas', []),
                company_name=agent_data.get('company_name'),
                company_description=agent_data.get('company_description')
            )
            
            # Save to database
            self.db.add(agent)
            self.db.commit()
            self.db.refresh(agent)
            
            # Get AI recommendations
            ai_recommendations = await self.ai_service.analyze_agent_profile(agent_data)
            
            # Update branding based on AI recommendations
            self._update_agent_branding(agent, ai_recommendations)
            
            # Save branding updates
            self.db.commit()
            
            logger.info(f"Agent created successfully: {agent.email}")
            
            return {
                "success": True,
                "agent_id": agent.id,
                "message": "Agent created successfully",
                "ai_recommendations": ai_recommendations,
                "next_steps": self._get_onboarding_next_steps(agent)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating agent: {str(e)}")
            raise
    
    async def update_agent_profile(self, agent_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent profile and branding"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise ValueError("Agent not found")
            
            # Update basic information
            for field, value in update_data.items():
                if hasattr(agent, field) and field not in ['id', 'email', 'password_hash']:
                    setattr(agent, field, value)
            
            # Update branding if colors are provided
            if 'primary_color' in update_data or 'secondary_color' in update_data:
                self._update_agent_branding(agent, update_data)
            
            # Update timestamp
            agent.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Agent profile updated: {agent.email}")
            
            return {
                "success": True,
                "message": "Profile updated successfully",
                "agent": self._format_agent_response(agent)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating agent profile: {str(e)}")
            raise
    
    async def get_agent_profile(self, agent_id: int) -> Dict[str, Any]:
        """Get agent profile with branding information"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise ValueError("Agent not found")
            
            return self._format_agent_response(agent)
            
        except Exception as e:
            logger.error(f"Error getting agent profile: {str(e)}")
            raise
    
    async def update_agent_branding(self, agent_id: int, branding_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent branding preferences"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise ValueError("Agent not found")
            
            # Update branding colors
            if 'primary_color' in branding_data:
                agent.primary_color = branding_data['primary_color']
            if 'secondary_color' in branding_data:
                agent.secondary_color = branding_data['secondary_color']
            if 'accent_color' in branding_data:
                agent.accent_color = branding_data['accent_color']
            if 'text_color' in branding_data:
                agent.text_color = branding_data['text_color']
            if 'background_color' in branding_data:
                agent.background_color = branding_data['background_color']
            
            # Update logo and company info
            if 'logo_url' in branding_data:
                agent.logo_url = branding_data['logo_url']
            if 'company_name' in branding_data:
                agent.company_name = branding_data['company_name']
            if 'company_description' in branding_data:
                agent.company_description = branding_data['company_description']
            if 'tagline' in branding_data:
                agent.tagline = branding_data['tagline']
            
            # Update global branding
            branding.update_from_agent(agent.branding_config)
            
            agent.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Agent branding updated: {agent.email}")
            
            return {
                "success": True,
                "message": "Branding updated successfully",
                "branding": agent.branding_config
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating agent branding: {str(e)}")
            raise
    
    async def get_agent_dashboard_data(self, agent_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard data for agent"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise ValueError("Agent not found")
            
            # Get property count
            property_count = self.db.query(Property).filter(Property.agent_id == agent_id).count()
            
            # Get recent activity (placeholder for now)
            recent_activity = []
            
            return {
                "agent": self._format_agent_response(agent),
                "dashboard_stats": {
                    "total_properties": property_count,
                    "active_listings": property_count,  # Placeholder
                    "total_leads": 0,  # Placeholder
                    "monthly_revenue": 0  # Placeholder
                },
                "recent_activity": recent_activity,
                "branding": agent.branding_config
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _update_agent_branding(self, agent: Agent, branding_data: Dict[str, Any]):
        """Update agent branding from data"""
        if 'branding_colors' in branding_data:
            colors = branding_data['branding_colors']
            if 'primary' in colors:
                agent.primary_color = colors['primary']
            if 'secondary' in colors:
                agent.secondary_color = colors['secondary']
            if 'accent' in colors:
                agent.accent_color = colors['accent']
        
        if 'suggested_tagline' in branding_data:
            agent.tagline = branding_data['suggested_tagline']
    
    def _format_agent_response(self, agent: Agent) -> Dict[str, Any]:
        """Format agent data for API response"""
        return {
            "id": agent.id,
            "email": agent.email,
            "first_name": agent.first_name,
            "last_name": agent.last_name,
            "full_name": agent.full_name,
            "phone": agent.phone,
            "profile_picture_url": agent.profile_picture_url,
            "license_number": agent.license_number,
            "years_experience": agent.years_experience,
            "specializations": agent.specializations,
            "certifications": agent.certifications,
            "company_name": agent.company_name,
            "company_description": agent.company_description,
            "logo_url": agent.logo_url,
            "favicon_url": agent.favicon_url,
            "branding": agent.branding_config,
            "office_address": agent.office_address,
            "office_phone": agent.office_phone,
            "website_url": agent.website_url,
            "social_media": agent.social_media,
            "commission_rate": agent.commission_rate,
            "service_areas": agent.service_areas,
            "languages_spoken": agent.languages_spoken,
            "is_active": agent.is_active,
            "is_verified": agent.is_verified,
            "subscription_tier": agent.subscription_tier,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
            "last_login": agent.last_login.isoformat() if agent.last_login else None
        }
    
    def _get_onboarding_next_steps(self, agent: Agent) -> List[Dict[str, str]]:
        """Get next steps for agent onboarding"""
        steps = [
            {
                "step": 1,
                "title": "Complete Profile",
                "description": "Add your photo, license details, and professional information",
                "status": "completed" if agent.profile_picture_url else "pending"
            },
            {
                "step": 2,
                "title": "Customize Branding",
                "description": "Upload your logo and customize colors to match your brand",
                "status": "completed" if agent.logo_url else "pending"
            },
            {
                "step": 3,
                "title": "Add Properties",
                "description": "Start listing your properties with AI-powered descriptions",
                "status": "pending"
            },
            {
                "step": 4,
                "title": "Connect Leads",
                "description": "Import your leads and start managing relationships",
                "status": "pending"
            },
            {
                "step": 5,
                "title": "Launch Marketing",
                "description": "Use AI-generated marketing content for your properties",
                "status": "pending"
            }
        ]
        return steps