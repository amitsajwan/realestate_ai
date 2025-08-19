from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.services.ai_service import AIService
from app.config import settings
import logging
import json

logger = logging.getLogger(__name__)

class AgentService:
    """Service for managing real estate agents with AI-powered onboarding."""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent with AI-powered onboarding assistance."""
        try:
            # Create agent record
            agent = Agent(**agent_data)
            self.db.add(agent)
            self.db.commit()
            self.db.refresh(agent)
            
            # Generate AI-powered branding suggestions
            branding_suggestions = await self.ai_service.generate_branding_suggestions(agent_data)
            
            # Generate CRM strategy
            crm_strategy = await self.ai_service.optimize_crm_strategy(agent_data)
            
            # Generate content suggestions
            content_suggestions = await self.ai_service.generate_content_suggestions(
                agent_data, "social_media"
            )
            
            return {
                "agent": agent,
                "onboarding_data": {
                    "branding_suggestions": branding_suggestions,
                    "crm_strategy": crm_strategy,
                    "content_suggestions": content_suggestions,
                    "next_steps": self._get_onboarding_next_steps()
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            self.db.rollback()
            raise
    
    async def update_agent_branding(self, agent_id: int, branding_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent branding and regenerate AI suggestions."""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise ValueError("Agent not found")
            
            # Update branding fields
            for field, value in branding_data.items():
                if hasattr(agent, field):
                    setattr(agent, field, value)
            
            # Regenerate AI suggestions based on new branding
            agent_data = {
                "first_name": agent.first_name,
                "last_name": agent.last_name,
                "company_name": agent.company_name,
                "specialties": agent.specialties,
                "service_areas": agent.service_areas,
                "experience_years": agent.experience_years,
                "bio": agent.bio,
                **branding_data
            }
            
            # Get updated AI suggestions
            branding_suggestions = await self.ai_service.generate_branding_suggestions(agent_data)
            crm_strategy = await self.ai_service.optimize_crm_strategy(agent_data)
            
            self.db.commit()
            
            return {
                "agent": agent,
                "updated_suggestions": {
                    "branding_suggestions": branding_suggestions,
                    "crm_strategy": crm_strategy
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating agent branding: {e}")
            self.db.rollback()
            raise
    
    async def complete_onboarding_step(self, agent_id: int, step: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a specific onboarding step with AI assistance."""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise ValueError("Agent not found")
            
            step_handlers = {
                "profile": self._complete_profile_step,
                "branding": self._complete_branding_step,
                "specialties": self._complete_specialties_step,
                "crm_setup": self._complete_crm_setup_step,
                "verification": self._complete_verification_step
            }
            
            if step not in step_handlers:
                raise ValueError(f"Invalid onboarding step: {step}")
            
            result = await step_handlers[step](agent, data)
            self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error completing onboarding step: {e}")
            self.db.rollback()
            raise
    
    async def _complete_profile_step(self, agent: Agent, data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete profile setup step."""
        # Update profile fields
        for field, value in data.items():
            if hasattr(agent, field):
                setattr(agent, field, value)
        
        # Generate initial AI suggestions
        agent_data = {
            "first_name": agent.first_name,
            "last_name": agent.last_name,
            "company_name": agent.company_name,
            "bio": agent.bio,
            "experience_years": agent.experience_years
        }
        
        branding_suggestions = await self.ai_service.generate_branding_suggestions(agent_data)
        
        return {
            "step": "profile",
            "completed": True,
            "next_step": "branding",
            "ai_suggestions": branding_suggestions
        }
    
    async def _complete_branding_step(self, agent: Agent, data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete branding setup step."""
        # Update branding fields
        branding_fields = [
            'logo_url', 'brand_name', 'tagline', 'primary_color', 
            'secondary_color', 'accent_color', 'text_color', 'background_color'
        ]
        
        for field in branding_fields:
            if field in data:
                setattr(agent, field, data[field])
        
        # Generate CRM strategy based on branding
        agent_data = {
            "first_name": agent.first_name,
            "last_name": agent.last_name,
            "company_name": agent.company_name,
            "specialties": agent.specialties,
            "service_areas": agent.service_areas,
            "brand_name": agent.brand_name
        }
        
        crm_strategy = await self.ai_service.optimize_crm_strategy(agent_data)
        
        return {
            "step": "branding",
            "completed": True,
            "next_step": "specialties",
            "crm_strategy": crm_strategy
        }
    
    async def _complete_specialties_step(self, agent: Agent, data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete specialties and service areas step."""
        # Update specialties and service areas
        if 'specialties' in data:
            agent.specialties = data['specialties']
        if 'service_areas' in data:
            agent.service_areas = data['service_areas']
        if 'property_types' in data:
            agent.property_types = data['property_types']
        if 'price_ranges' in data:
            agent.price_ranges = data['price_ranges']
        
        # Generate content suggestions based on specialties
        agent_data = {
            "first_name": agent.first_name,
            "last_name": agent.last_name,
            "specialties": agent.specialties,
            "service_areas": agent.service_areas,
            "brand_name": agent.brand_name
        }
        
        content_suggestions = await self.ai_service.generate_content_suggestions(
            agent_data, "social_media"
        )
        
        return {
            "step": "specialties",
            "completed": True,
            "next_step": "crm_setup",
            "content_suggestions": content_suggestions
        }
    
    async def _complete_crm_setup_step(self, agent: Agent, data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete CRM setup step."""
        # Update CRM settings
        if 'ai_preferences' in data:
            agent.ai_preferences = data['ai_preferences']
        if 'notification_settings' in data:
            agent.notification_settings = data['notification_settings']
        if 'crm_settings' in data:
            agent.crm_settings = data['crm_settings']
        
        return {
            "step": "crm_setup",
            "completed": True,
            "next_step": "verification",
            "crm_configured": True
        }
    
    async def _complete_verification_step(self, agent: Agent, data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete verification step."""
        # Update verification status
        if 'verification_documents' in data:
            agent.verification_documents = data['verification_documents']
        
        # Mark as verified if documents are provided
        if data.get('verification_documents'):
            agent.is_verified = True
        
        return {
            "step": "verification",
            "completed": True,
            "next_step": "onboarding_complete",
            "verification_status": agent.is_verified
        }
    
    def get_agent_branding(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """Get agent's branding configuration."""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None
        
        return agent.get_branding_config()
    
    def get_onboarding_progress(self, agent_id: int) -> Dict[str, Any]:
        """Get agent's onboarding progress."""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return {"error": "Agent not found"}
        
        steps = {
            "profile": bool(agent.first_name and agent.last_name and agent.email),
            "branding": bool(agent.brand_name or agent.logo_url),
            "specialties": bool(agent.specialties and agent.service_areas),
            "crm_setup": bool(agent.ai_preferences),
            "verification": agent.is_verified
        }
        
        completed_steps = sum(steps.values())
        total_steps = len(steps)
        progress_percentage = (completed_steps / total_steps) * 100
        
        return {
            "steps": steps,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "progress_percentage": progress_percentage,
            "next_step": self._get_next_incomplete_step(steps)
        }
    
    def _get_next_incomplete_step(self, steps: Dict[str, bool]) -> str:
        """Get the next incomplete onboarding step."""
        step_order = ["profile", "branding", "specialties", "crm_setup", "verification"]
        
        for step in step_order:
            if not steps[step]:
                return step
        
        return "onboarding_complete"
    
    def _get_onboarding_next_steps(self) -> List[Dict[str, Any]]:
        """Get the list of onboarding steps with descriptions."""
        return [
            {
                "step": "profile",
                "title": "Complete Your Profile",
                "description": "Add your basic information and experience",
                "icon": "user",
                "required": True
            },
            {
                "step": "branding",
                "title": "Set Up Your Brand",
                "description": "Customize your visual identity and colors",
                "icon": "palette",
                "required": True
            },
            {
                "step": "specialties",
                "title": "Define Your Specialties",
                "description": "Select your focus areas and service regions",
                "icon": "target",
                "required": True
            },
            {
                "step": "crm_setup",
                "title": "Configure Your CRM",
                "description": "Set up AI preferences and automation",
                "icon": "settings",
                "required": False
            },
            {
                "step": "verification",
                "title": "Verify Your Account",
                "description": "Upload required documents for verification",
                "icon": "shield-check",
                "required": True
            }
        ]