"""Utility functions for AI-powered features (branding suggestions, etc.).

This module provides a thin wrapper around Groq's LLM so we have a
single place to handle authentication, fall-backs, and prompt design.
"""

from typing import Dict, Any
import logging

# Local modules
from core.config import settings

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


def _fallback_branding(name: str) -> Dict[str, str]:
    """Return deterministic branding suggestions when LLM is unavailable."""
    return {
        "tagline": f"Your Property Partner, {name}",
        "about": f"{name} brings reliability and a modern approach to real estate success.",
        "colors": {
            "primary": "#007bff",  # Bootstrap blue
            "secondary": "#6c757d",  # Bootstrap gray
            "accent": "#28a745",  # Bootstrap green
        },
    }


def generate_branding(name: str) -> Dict[str, Any]:
    """Generate branding suggestions for an agent/company name.

    The returned dict has the following shape (keys MAY vary in the future):

    {
        "tagline": str,
        "about": str,
        "colors": {"primary": str, "secondary": str, "accent": str}
    }
    """

    if not _groq_client:
        return _fallback_branding(name)

    prompt = f"""
You are a world-class real-estate marketing assistant. Create concise branding
suggestions for the following real-estate agent or agency:

    Name: "{name}"

Return STRICTLY a JSON object with these exact keys:

    tagline:      A short catchy tagline (max 10 words)
    about:        A very brief description (1-2 sentences)
    colors:       An object with HEX color strings best matching the brand. Use
                 keys primary, secondary and accent – make sure colors are web-safe
                 and have sufficient contrast.

The response MUST be valid JSON without markdown fences or additional text.
"""

    try:
        response = _groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300,
        )

        raw_content = response.choices[0].message.content if response.choices else ""

        import json  # Local import to avoid global cost when not needed

        branding: Dict[str, Any] = json.loads(raw_content)

        # Basic sanity checks & defaults – make sure required keys exist
        if "tagline" not in branding or "about" not in branding:
            logger.warning("LLM branding response missing mandatory keys – using fallback")
            return _fallback_branding(name)

        # Ensure colors present
        branding.setdefault("colors", _fallback_branding(name)["colors"])

        return branding

    except Exception as e:  # Any failure → fallback
        logger.error(f"Branding generation failed – using fallback. Error: {e}")
        return _fallback_branding(name)
