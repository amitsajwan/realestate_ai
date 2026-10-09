"""Branding suggestions for an agent profile, through the shared AI gateway (app.platform.llm) with a fixed fallback."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a real-estate marketing assistant. Create concise branding for the agent or agency described. "
    "Return one JSON object with keys: tagline (max 10 words), about (1-2 sentences on their expertise and value), "
    "colors (object with HEX strings primary, secondary, accent that have enough contrast)."
)


def _fallback_branding(profile_data) -> Dict[str, Any]:
    """Fixed branding when the LLM is unavailable."""
    if isinstance(profile_data, str):
        name = profile_data
    elif isinstance(profile_data, dict):
        name = profile_data.get("company_name") or profile_data.get("name") or "Your Company"
    else:
        name = getattr(profile_data, "company_name", None) or "Your Company"
    return {
        "tagline": "Your Trusted Real Estate Partner",
        "about": f"{name} brings reliability and a modern approach to real estate success. We specialize in connecting "
                 "clients with their perfect properties through personalized service and market expertise.",
        "colors": {"primary": "#2563eb", "secondary": "#64748b", "accent": "#059669"},
    }


def _describe(profile_data) -> str:
    if isinstance(profile_data, str):
        return f"Company/Agency Name: {profile_data}"
    get = profile_data.get if isinstance(profile_data, dict) else (lambda k: getattr(profile_data, k, None))
    fields = (("Company/Agency Name", "company_name"), ("Agent Name", "agent_name"), ("Agent Name", "name"),
              ("Specialization", "specialization_areas"), ("Experience (years)", "experience_years"), ("Location", "location"))
    return "\n".join(f"{label}: {get(key)}" for label, key in fields if get(key))


async def generate_branding(profile_data) -> Dict[str, Any]:
    """{"tagline", "about", "colors": {primary, secondary, accent}}; the fallback on any LLM failure."""
    from app.platform.llm import default_llm

    llm = default_llm()
    out = await llm.json(_SYSTEM, _describe(profile_data)) if llm else None
    if not (isinstance(out, dict) and out.get("tagline") and out.get("about")):
        logger.info("AI branding unavailable, using fallback")
        return _fallback_branding(profile_data)
    if not isinstance(out.get("colors"), dict):
        out["colors"] = _fallback_branding(profile_data)["colors"]
    return out
