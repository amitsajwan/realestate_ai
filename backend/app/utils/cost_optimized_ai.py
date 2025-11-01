"""
Cost-Optimized AI Service Helper
===============================
Provides cost-effective AI model selection and usage optimization for development.
"""

import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class CostOptimizedAI:
    """Cost-optimized AI service helper for development and production environments"""
    
    @staticmethod
    def get_optimal_model() -> str:
        """Get the optimal model based on environment and cost considerations"""
        if settings.environment == "development":
            return settings.ai_model_development
        else:
            return settings.ai_model_production
    
    @staticmethod
    def get_optimal_max_tokens() -> int:
        """Get optimal max tokens based on environment"""
        if settings.environment == "development":
            return settings.ai_max_tokens_development
        else:
            return settings.ai_max_tokens_production
    
    @staticmethod
    def optimize_prompt_for_cost(prompt: str) -> str:
        """Optimize prompt to reduce token usage while maintaining quality"""
        # Remove excessive whitespace
        prompt = ' '.join(prompt.split())
        
        # Remove redundant instructions for development
        if settings.environment == "development":
            # Keep only essential instructions
            essential_parts = []
            lines = prompt.split('\n')
            
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in [
                    'generate', 'create', 'write', 'language:', 'channel:', 
                    'tone:', 'property details:', 'requirements:'
                ]):
                    essential_parts.append(line)
            
            # Limit to first 50 lines for development
            essential_parts = essential_parts[:50]
            prompt = '\n'.join(essential_parts)
        
        logger.info(f"Optimized prompt length: {len(prompt)} chars (reduced for cost optimization)")
        return prompt
    
    @staticmethod
    def should_use_fallback() -> bool:
        """Determine if fallback should be used"""
        return settings.ai_enable_fallback and settings.environment == "development"
    
    @staticmethod
    def get_model_info() -> Dict[str, Any]:
        """Get information about current model configuration"""
        return {
            "current_model": CostOptimizedAI.get_optimal_model(),
            "max_tokens": CostOptimizedAI.get_optimal_max_tokens(),
            "environment": settings.environment,
            "fallback_enabled": CostOptimizedAI.should_use_fallback(),
            "cost_optimization": "enabled" if settings.environment == "development" else "disabled"
        }

# Cost comparison data for reference
MODEL_COSTS = {
    "llama-3.1-8b-instant": {
        "cost_per_1k_tokens": 0.0002,  # Estimated
        "speed": "very_fast",
        "quality": "good",
        "best_for": "development, simple tasks"
    },
    "llama-3.3-70b-versatile": {
        "cost_per_1k_tokens": 0.002,  # Estimated - 10x more expensive
        "speed": "medium",
        "quality": "excellent", 
        "best_for": "production, complex tasks"
    }
}

def log_cost_info(model_name: str, tokens_used: int):
    """Log cost information for monitoring"""
    if model_name in MODEL_COSTS:
        cost_info = MODEL_COSTS[model_name]
        estimated_cost = (tokens_used / 1000) * cost_info["cost_per_1k_tokens"]
        logger.info(f"AI_COST_INFO: Model={model_name}, Tokens={tokens_used}, Estimated_Cost=${estimated_cost:.6f}")
    else:
        logger.info(f"AI_COST_INFO: Model={model_name}, Tokens={tokens_used}, Cost=unknown")
