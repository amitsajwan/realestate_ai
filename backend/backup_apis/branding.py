"""
Branding Suggestions API
========================
AI-powered branding suggestions for real estate businesses
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Helper functions for generating branding elements
def _generate_color_palette(style: str, variant: int = 0):
    """Generate color palette based on style and variant"""
    palettes = {
        "Professional": [
            {"primary": "#1a365d", "secondary": "#e53e3e", "accent": "#38b2ac", "neutral": "#f7fafc"},
            {"primary": "#2d3748", "secondary": "#3182ce", "accent": "#ed8936", "neutral": "#f7fafc"},
            {"primary": "#1a202c", "secondary": "#38b2ac", "accent": "#ed64a6", "neutral": "#f7fafc"}
        ],
        "Modern": [
            {"primary": "#2563eb", "secondary": "#64748b", "accent": "#06b6d4", "neutral": "#f8fafc"},
            {"primary": "#7c3aed", "secondary": "#6b7280", "accent": "#10b981", "neutral": "#f9fafb"},
            {"primary": "#059669", "secondary": "#374151", "accent": "#f59e0b", "neutral": "#f3f4f6"}
        ],
        "Luxury": [
            {"primary": "#1a1a1a", "secondary": "#d4af37", "accent": "#8b4513", "neutral": "#fafafa"},
            {"primary": "#1f2937", "secondary": "#f59e0b", "accent": "#7c2d12", "neutral": "#f9fafb"},
            {"primary": "#374151", "secondary": "#fbbf24", "accent": "#991b1b", "neutral": "#f3f4f6"}
        ],
        "Traditional": [
            {"primary": "#1e40af", "secondary": "#dc2626", "accent": "#059669", "neutral": "#f7fafc"},
            {"primary": "#7c2d12", "secondary": "#1d4ed8", "accent": "#047857", "neutral": "#f9fafb"},
            {"primary": "#92400e", "secondary": "#1e3a8a", "accent": "#065f46", "neutral": "#f3f4f6"}
        ]
    }
    
    style_palettes = palettes.get(style, palettes["Professional"])
    return style_palettes[variant % len(style_palettes)]

def _generate_typography(style: str):
    """Generate typography settings based on style"""
    fonts = {
        "Professional": {"primary": "Inter, sans-serif", "headings": "Inter, sans-serif", "body": "Inter, sans-serif", "accent": "Inter, sans-serif"},
        "Modern": {"primary": "Poppins, sans-serif", "headings": "Poppins, sans-serif", "body": "Inter, sans-serif", "accent": "Poppins, sans-serif"},
        "Luxury": {"primary": "Playfair Display, serif", "headings": "Playfair Display, serif", "body": "Crimson Text, serif", "accent": "Playfair Display, serif"},
        "Traditional": {"primary": "Merriweather, serif", "headings": "Merriweather, serif", "body": "Open Sans, sans-serif", "accent": "Merriweather, serif"},
        "Contemporary": {"primary": "Montserrat, sans-serif", "headings": "Montserrat, sans-serif", "body": "Source Sans Pro, sans-serif", "accent": "Montserrat, sans-serif"},
        "Elegant": {"primary": "Cormorant Garamond, serif", "headings": "Cormorant Garamond, serif", "body": "Lato, sans-serif", "accent": "Cormorant Garamond, serif"},
        "Sophisticated": {"primary": "Libre Baskerville, serif", "headings": "Libre Baskerville, serif", "body": "Source Sans Pro, sans-serif", "accent": "Libre Baskerville, serif"}
    }
    return fonts.get(style, fonts["Professional"])

def _generate_personality(style: str):
    """Generate brand personality based on style"""
    personalities = {
        "Professional": {"voice": "Professional", "traits": "Trustworthy, Reliable, Expert", "message": "competence and reliability"},
        "Modern": {"voice": "Contemporary", "traits": "Innovative, Forward-thinking, Tech-savvy", "message": "innovation and cutting-edge service"},
        "Luxury": {"voice": "Sophisticated", "traits": "Exclusive, Premium, Refined", "message": "luxury and exclusivity"},
        "Traditional": {"voice": "Established", "traits": "Time-tested, Dependable, Classic", "message": "tradition and stability"},
        "Contemporary": {"voice": "Fresh", "traits": "Current, Relevant, Approachable", "message": "modern relevance and accessibility"},
        "Elegant": {"voice": "Refined", "traits": "Graceful, Polished, Distinguished", "message": "elegance and sophistication"},
        "Sophisticated": {"voice": "Cultured", "traits": "Worldly, Discerning, Elevated", "message": "cultural sophistication and expertise"}
    }
    return personalities.get(style, personalities["Professional"])

def _generate_tagline(company_name: str, business_type: str, target_audience: str, style: str):
    """Generate contextual taglines based on inputs"""
    templates = {
        "Professional": [
            f"{company_name} - Your Trusted Real Estate Partner",
            f"Excellence in {business_type} Real Estate",
            f"Professional Service, Personal Touch"
        ],
        "Modern": [
            f"{company_name} - Redefining Real Estate",
            f"The Future of {business_type} Real Estate",
            f"Smart Homes, Smarter Choices"
        ],
        "Luxury": [
            f"{company_name} - Exclusively Yours",
            f"Curating Exceptional {business_type} Properties",
            f"Where Luxury Meets Legacy"
        ],
        "Traditional": [
            f"{company_name} - Established Excellence Since",
            f"Time-Honored Service in {business_type} Real Estate",
            f"Building Relationships, Creating Homes"
        ]
    }
    
    style_templates = templates.get(style, templates["Professional"])
    return style_templates[0]  # Return the first template for consistency

def _generate_about_section(company_name: str, agent_name: str, business_type: str, target_audience: str, style: str):
    """Generate personalized about section"""
    templates = {
        "Professional": f"Welcome to {company_name}. {agent_name} brings years of expertise in {business_type.lower()} real estate, specializing in serving {target_audience.lower()}. Our commitment to professional excellence ensures every client receives personalized service and expert guidance throughout their real estate journey.",
        "Modern": f"At {company_name}, {agent_name} leverages cutting-edge technology and innovative marketing strategies to serve {target_audience.lower()} in the {business_type.lower()} market. We're redefining the real estate experience with smart solutions and forward-thinking approaches.",
        "Luxury": f"{company_name} represents the pinnacle of {business_type.lower()} real estate excellence. {agent_name} curates exclusive opportunities for discerning {target_audience.lower()}, offering white-glove service and access to the most prestigious properties in the market.",
        "Traditional": f"With deep roots in the community, {company_name} has been serving {target_audience.lower()} with integrity and dedication. {agent_name} continues this tradition of excellence in {business_type.lower()} real estate, building lasting relationships based on trust and proven results."
    }
    return templates.get(style, templates["Professional"])

def _generate_logo_ideas(business_type: str, style: str):
    """Generate logo concept ideas"""
    base_concepts = {
        "Professional": [
            "Clean geometric house icon with company initials",
            "Minimalist key and home combination",
            "Simple, bold typography with architectural element"
        ],
        "Modern": [
            "Abstract building silhouette with gradient effect",
            "Geometric home icon with tech-inspired lines",
            "Contemporary typography with smart home elements"
        ],
        "Luxury": [
            "Elegant monogram with gold accents",
            "Sophisticated crest with property elements",
            "Premium serif typography with refined details"
        ],
        "Traditional": [
            "Classic house icon with established date",
            "Heritage-style badge with community elements",
            "Timeless serif font with architectural details"
        ]
    }
    return base_concepts.get(style, base_concepts["Professional"])

class BrandingSuggestionRequest(BaseModel):
    company_name: str
    agent_name: str
    position: Optional[str] = None
    business_type: Optional[str] = None  # e.g., "Residential", "Commercial", "Luxury"
    target_audience: Optional[str] = None  # e.g., "First-time buyers", "Luxury clients", "Families"
    brand_style: Optional[str] = None  # e.g., "Professional", "Modern", "Traditional", "Luxury"
    brand_tone: Optional[str] = None  # e.g., "Friendly", "Formal", "Approachable", "Sophisticated"
    additionalContext: Optional[str] = None

class BrandingSuggestion(BaseModel):
    primaryColor: str
    secondaryColor: str
    fontFamily: str
    brandVoice: str
    designStyle: str
    reasoning: str
    colorPalette: dict
    typography: dict
    # Enhanced branding fields
    tagline: Optional[str] = None
    about: Optional[str] = None
    logoIdeas: Optional[list[str]] = None
    brandPersonality: Optional[str] = None
    targetMessage: Optional[str] = None

class BrandingSuggestionResponse(BaseModel):
    suggestions: list[BrandingSuggestion]
    selectedIndex: Optional[int] = 0

@router.post("/suggestions", response_model=BrandingSuggestionResponse)
async def get_branding_suggestions(request: BrandingSuggestionRequest):
    """Generate AI-powered branding suggestions for real estate businesses"""
    try:
        logger.info(f"Generating branding suggestions for {request.company_name}")

        # Validate that we have enough information to generate meaningful suggestions
        if not request.business_type or not request.target_audience:
            raise HTTPException(
                status_code=400,
                detail="Please provide business type and target audience for better branding suggestions"
            )

        # Generate multiple comprehensive branding suggestions
        suggestions = []
        
        # Define style variations for multiple suggestions
        style_variants = [
            {
                "style": request.brand_style or "Professional",
                "colors": _generate_color_palette(request.brand_style or "Professional", 0),
                "fonts": _generate_typography(request.brand_style or "Professional"),
                "personality": _generate_personality(request.brand_style or "Professional")
            },
            {
                "style": "Modern" if request.brand_style != "Modern" else "Contemporary",
                "colors": _generate_color_palette("Modern", 1),
                "fonts": _generate_typography("Modern"),
                "personality": _generate_personality("Modern")
            },
            {
                "style": "Elegant" if request.brand_style != "Luxury" else "Sophisticated",
                "colors": _generate_color_palette("Luxury", 2),
                "fonts": _generate_typography("Luxury"),
                "personality": _generate_personality("Luxury")
            }
        ]
        
        # Generate 3 suggestions for variety
        for i, variant in enumerate(style_variants):
            tagline = _generate_tagline(request.company_name, request.business_type, request.target_audience, variant["style"])
            about = _generate_about_section(request.company_name, request.agent_name, request.business_type, request.target_audience, variant["style"])
            logo_ideas = _generate_logo_ideas(request.business_type, variant["style"])
            
            suggestion = BrandingSuggestion(
                primaryColor=variant["colors"]["primary"],
                secondaryColor=variant["colors"]["secondary"],
                fontFamily=variant["fonts"]["primary"],
                brandVoice=request.brand_tone or variant["personality"]["voice"],
                designStyle=variant["style"],
                reasoning=f"Based on {request.business_type} business targeting {request.target_audience} with {variant['style'].lower()} approach. This style conveys {variant['personality']['message']}",
                colorPalette=variant["colors"],
                typography=variant["fonts"],
                tagline=tagline,
                about=about,
                logoIdeas=logo_ideas,
                brandPersonality=variant["personality"]["traits"],
                targetMessage=variant["personality"]["message"]
            )
            suggestions.append(suggestion)
        
        # Return all suggestions
        return BrandingSuggestionResponse(
            suggestions=suggestions,
            selectedIndex=0
        )

    except Exception as e:
        logger.error(f"Error generating branding suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate branding suggestions"
        )
