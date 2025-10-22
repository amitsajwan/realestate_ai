"""Utility functions for AI-powered features (branding suggestions, etc.).

This module provides a thin wrapper around Groq's LLM so we have a
single place to handle authentication, fall-backs, and prompt design.
"""

from typing import Dict, Any
import logging

# Local modules
from app.core.config import settings
from app.utils.cost_optimized_ai import CostOptimizedAI, log_cost_info

# groq is an optional dependency across the codebase – we always import it
# behind a try/except so local development keeps working even if the API key
# is missing.


logger = logging.getLogger(__name__)

# Lazy import so unit-tests without the dependency or key don't break.
try:
    if settings.GROQ_API_KEY:
        from groq import Groq  # type: ignore
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    else:
        _groq_client = None
        logger.info("GROQ_API_KEY not set – using fallback branding generator")
except Exception as import_exc:  # pragma: no cover – best-effort import guard
    logger.warning(f"Groq SDK not available: {import_exc}")
    _groq_client = None


def _fallback_branding(profile_data) -> Dict[str, str]:
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Fallback branding for profile: {profile_data}")
    """Return deterministic branding suggestions when LLM is unavailable."""
    name = getattr(profile_data, 'company_name', 'Your Company') if hasattr(profile_data, 'company_name') else profile_data if isinstance(profile_data, str) else 'Your Company'
    return {
        "tagline": "Your Trusted Real Estate Partner",
        "about": f"{name} brings reliability and a modern approach to real estate success. We specialize in connecting clients with their perfect properties through personalized service and market expertise.",
        "colors": {
            "primary": "#2563eb",  # Modern blue
            "secondary": "#64748b",  # Slate gray
            "accent": "#059669",  # Emerald green
        },
    }


def generate_branding(profile_data) -> Dict[str, Any]:
    import logging
    import time
    import uuid
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Log branding generation start
    logger.info(
        "AI_BRANDING_GENERATION_START",
        extra={
            "operation": "branding_generation",
            "request_id": request_id,
            "profile_type": type(profile_data).__name__,
            "has_groq_client": _groq_client is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    """Generate branding suggestions for an agent/company profile.

    The returned dict has the following shape (keys MAY vary in the future):

    {
        "tagline": str,
        "about": str,
        "colors": {"primary": str, "secondary": str, "accent": str}
    }
    """

    if not _groq_client:
        logger.warning(
            "AI_BRANDING_FALLBACK_USED",
            extra={
                "operation": "branding_generation",
                "request_id": request_id,
                "reason": "groq_client_not_available",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        return _fallback_branding(profile_data)

    # Handle both string (legacy) and object inputs
    if isinstance(profile_data, str):
        company_name = profile_data
        agent_name = None
        specialization = None
        experience = None
        location = None
    else:
        company_name = getattr(profile_data, 'company_name', 'Unknown Company')
        agent_name = getattr(profile_data, 'agent_name', None)
        specialization = getattr(profile_data, 'specialization_areas', None)
        experience = getattr(profile_data, 'experience_years', None)
        location = getattr(profile_data, 'location', None)

    # Build context for the prompt
    context_parts = [f"Company/Agency Name: {company_name}"]
    if agent_name:
        context_parts.append(f"Agent Name: {agent_name}")
    if specialization:
        context_parts.append(f"Specialization: {specialization}")
    if experience:
        context_parts.append(f"Experience: {experience} years")
    if location:
        context_parts.append(f"Location: {location}")
    
    context = "\n    ".join(context_parts)

    prompt = f"""
You are a world-class real-estate marketing assistant. Create concise branding
suggestions for the following real-estate agent or agency:

    {context}

Return STRICTLY a JSON object with these exact keys:

    tagline:      A short catchy tagline (max 10 words) that reflects their specialization and experience
    about:        A very brief description (1-2 sentences) highlighting their expertise and value proposition
    colors:       An object with HEX color strings best matching the brand. Use
                 keys primary, secondary and accent – make sure colors are web-safe
                 and have sufficient contrast.

The response MUST be valid JSON without markdown fences or additional text.
"""

    try:
        # Log API call details
        logger.debug(
            "AI_BRANDING_API_REQUEST",
            extra={
                "operation": "branding_generation",
                "request_id": request_id,
                "model": "llama-3.3-70b-versatile",
                "prompt_length": len(prompt),
                "temperature": 0.2,
                "max_tokens": 300,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        api_start_time = time.time()
        # Use cost-optimized model selection
        model_name = CostOptimizedAI.get_optimal_model()
        max_tokens = CostOptimizedAI.get_optimal_max_tokens()
        
        # Optimize prompt for cost in development
        optimized_prompt = CostOptimizedAI.optimize_prompt_for_cost(prompt)
        
        response = _groq_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": optimized_prompt}],
            temperature=0.2,
            max_tokens=max_tokens,
        )
        api_time = time.time() - api_start_time

        raw_content = response.choices[0].message.content if response.choices else ""

        import json  # Local import to avoid global cost when not needed

        branding: Dict[str, Any] = json.loads(raw_content)

        # Log successful API response and cost info
        tokens_used = getattr(response, 'usage', {}).get('total_tokens', 0)
        log_cost_info(model_name, tokens_used)
        
        logger.info(
            "AI_BRANDING_API_SUCCESS",
            extra={
                "operation": "branding_generation",
                "request_id": request_id,
                "response_length": len(raw_content),
                "api_time_ms": round(api_time * 1000, 2),
                "tokens_used": tokens_used,
                "model_used": model_name,
                "cost_optimized": settings.environment == "development",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Basic sanity checks & defaults – make sure required keys exist
        if "tagline" not in branding or "about" not in branding:
            logger.warning(
                "AI_BRANDING_VALIDATION_FAILED",
                extra={
                    "operation": "branding_generation",
                    "request_id": request_id,
                    "reason": "missing_mandatory_keys",
                    "available_keys": list(branding.keys()),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return _fallback_branding(profile_data)

        # Ensure colors present
        branding.setdefault("colors", _fallback_branding(profile_data)["colors"])

        # Log successful branding generation
        total_time = time.time() - start_time
        logger.info(
            "AI_BRANDING_GENERATION_SUCCESS",
            extra={
                "operation": "branding_generation",
                "request_id": request_id,
                "tagline_length": len(branding.get("tagline", "")),
                "about_length": len(branding.get("about", "")),
                "has_colors": "colors" in branding,
                "total_time_ms": round(total_time * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return branding

    except Exception as e:  # Any failure → fallback
        total_time = time.time() - start_time
        logger.error(
            "AI_BRANDING_GENERATION_ERROR",
            extra={
                "operation": "branding_generation",
                "request_id": request_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "total_time_ms": round(total_time * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        return _fallback_branding(profile_data)
