from fastapi import APIRouter, Depends, Body, Request
from app.core.rate_limiting import limiter
from groq import Groq
from fastapi import HTTPException
import os
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/branding-suggest")
@limiter.limit("3/minute")
async def suggest_branding(
    request: Request,
    data: dict = Body(...)
):
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")
        
        client = Groq(api_key=api_key)

        prompt = f"Generate branding suggestions for a real estate company: Name: {data.get('companyName')}, Type: {data.get('businessType')}, Audience: {data.get('targetAudience')}. Suggest primary/secondary colors (hex), tone (e.g., professional), tagline, and 3 logo ideas."

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768",  # Fast model
            temperature=0.7,
            max_tokens=300
        )

        # Parse response (assume JSON-like output)
        suggestions = json.loads(response.choices[0].message.content)
        return suggestions

    except Exception as e:
        logger.error(f"Groq branding suggestion failed: {str(e)}")
        # Mock fallback
        return {
            "colors": {"primary": "#007bff", "secondary": "#6c757d"},
            "tone": "professional",
            "tagline": "Your Dream Home Awaits",
            "logoIdeas": ["Modern house icon", "Key with AI spark", "Abstract property skyline"]
        }
