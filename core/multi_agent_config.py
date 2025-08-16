import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field

class AgentSettings(BaseSettings):
    """Agent-specific settings that can be loaded dynamically"""
    
    # Agent Identity
    agent_id: str
    agent_name: str
    agent_brand: str
    
    # Agent's Facebook App Credentials
    fb_app_id: str = ""
    fb_app_secret: str = ""
    fb_page_id: str = ""
    
    # Agent-specific customization
    agent_tagline: str = "Trusted Real Estate Professional"
    agent_bio: str = "Helping clients achieve their real estate dreams"
    agent_phone: str = ""
    agent_email: str = ""
    agent_website: str = ""
    
    class Config:
        env_file_encoding = 'utf-8'

class MultiAgentSettings(BaseSettings):
    """Enhanced settings class supporting multiple agents"""
    
    # Core application settings (shared across all agents)
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # URLs
    BASE_URL: str = "http://localhost:8003"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Database settings
    MONGO_URI: str = "mongodb://localhost:27017/"

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Shared Facebook settings
    FB_GRAPH_API_VERSION: str = "v19.0"
    FACEBOOK_WEBHOOK_SECRET: str = ""
    FACEBOOK_WEBHOOK_VERIFY_TOKEN: str = "realestate_ai_webhook_verify"

    # API keys (shared)
    GROQ_API_KEY: str
    AI_DISABLE_IMAGE_GENERATION: bool = True
    
    # Feature flags
    FEATURE_FACEBOOK_PERSIST: bool = False
    FEATURE_MULTI_AGENT: bool = True
    
    # Optional external API keys
    STABILITY_API_KEY: str = ""
    HUGGINGFACE_API_TOKEN: str = ""
    
    # Current agent configuration (loaded dynamically)
    current_agent: Optional[AgentSettings] = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

    def load_agent_config(self, agent_id: str) -> Optional[AgentSettings]:
        """Load configuration for a specific agent"""
        
        # Try to load from agent-specific env file
        agent_env_file = f".env.{agent_id}"
        if os.path.exists(agent_env_file):
            try:
                agent_settings = AgentSettings(_env_file=agent_env_file)
                self.current_agent = agent_settings
                return agent_settings
            except Exception as e:
                print(f"Error loading agent config for {agent_id}: {e}")
                return None
        
        # Try to load from database (if implemented)
        # agent_config = self.load_agent_from_database(agent_id)
        # if agent_config:
        #     return agent_config
        
        return None
    
    def get_facebook_config_for_agent(self, agent_id: str) -> Dict[str, str]:
        """Get Facebook configuration for a specific agent"""
        
        agent_config = self.load_agent_config(agent_id)
        if agent_config:
            return {
                "fb_app_id": agent_config.fb_app_id,
                "fb_app_secret": agent_config.fb_app_secret,
                "fb_page_id": agent_config.fb_page_id,
                "fb_graph_api_version": self.FB_GRAPH_API_VERSION
            }
        
        # Fallback to default/global Facebook config (if any)
        return {
            "fb_app_id": "",
            "fb_app_secret": "",
            "fb_page_id": "",
            "fb_graph_api_version": self.FB_GRAPH_API_VERSION
        }

# Global settings instance
settings = MultiAgentSettings()

# Convenience function to get agent-specific settings
def get_agent_settings(agent_id: str) -> Optional[AgentSettings]:
    """Get settings for a specific agent"""
    return settings.load_agent_config(agent_id)

def get_facebook_config(agent_id: str) -> Dict[str, str]:
    """Get Facebook configuration for an agent"""
    return settings.get_facebook_config_for_agent(agent_id)
