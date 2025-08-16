from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from models.listing import ListingTemplate, ListingDetails, GeneratedListingPost
from core.config import settings

# Initialize LLM only if API key is available
llm = None
try:
    if settings.GROQ_API_KEY:
        from langchain_groq import ChatGroq
        llm = ChatGroq(model="llama3-70b-8192", temperature=0.3)
except Exception:
    pass

TEMPLATE_PROMPTS = {
    ListingTemplate.JUST_LISTED: {
        "system": """You're a professional real estate copywriter. Create an engaging "Just Listed" Facebook post that:
- Announces the new listing with excitement
- Highlights key features and selling points
- Includes relevant emojis and a strong call-to-action
- Maintains professional tone while being engaging
- Keep it under 280 characters for optimal Facebook performance""",
        
        "hashtags": ["#JustListed", "#NewListing", "#RealEstate", "#ForSale", "#DreamHome"],
        "cta": "Call today to schedule your private showing!"
    },
    
    ListingTemplate.OPEN_HOUSE: {
        "system": """You're a professional real estate copywriter. Create an inviting "Open House" Facebook post that:
- Creates urgency and excitement about the open house event
- Highlights the property's best features
- Includes clear date/time information
- Encourages immediate action
- Uses engaging emojis and friendly tone""",
        
        "hashtags": ["#OpenHouse", "#RealEstate", "#TourToday", "#HomeShopping", "#NewListing"],
        "cta": "See you this weekend! No appointment necessary."
    },
    
    ListingTemplate.PRICE_DROP: {
        "system": """You're a professional real estate copywriter. Create a compelling "Price Reduction" Facebook post that:
- Emphasizes the value and opportunity
- Mentions the price improvement positively
- Highlights why this is a great deal
- Creates urgency without being pushy
- Maintains excitement about the property""",
        
        "hashtags": ["#PriceReduced", "#GreatValue", "#RealEstate", "#Opportunity", "#PricedToSell"],
        "cta": "This won't last long at this price - call now!"
    },
    
    ListingTemplate.SOLD: {
        "system": """You're a professional real estate copywriter. Create a celebratory "SOLD" Facebook post that:
- Celebrates the successful sale
- Thanks buyers and sellers
- Demonstrates market expertise
- Invites others to contact you
- Maintains professional yet celebratory tone""",
        
        "hashtags": ["#SOLD", "#AnotherOneSold", "#RealEstate", "#ClosingDay", "#ThankYou"],
        "cta": "Ready to buy or sell? Let's make it happen together!"
    },
    
    ListingTemplate.COMING_SOON: {
        "system": """You're a professional real estate copywriter. Create an exciting "Coming Soon" Facebook post that:
- Builds anticipation for the upcoming listing
- Teases key features without giving everything away
- Encourages people to get in touch for early access
- Creates FOMO (fear of missing out)
- Maintains professional excitement""",
        
        "hashtags": ["#ComingSoon", "#ExclusivePreview", "#RealEstate", "#NewListing", "#StayTuned"],
        "cta": "Want early access? Message me for exclusive details!"
    }
}

FAIR_HOUSING_DISCLAIMER = """Equal Housing Opportunity. All real estate advertised herein is subject to the Federal Fair Housing Act, which makes it illegal to advertise any preference, limitation, or discrimination based on race, color, religion, sex, handicap, familial status, or national origin."""

async def generate_listing_post(details: ListingDetails, agent_brand: str = None) -> GeneratedListingPost:
    """Generate a branded listing post using the specified template"""
    print(" =======  ==== =  === ")
    template_config = TEMPLATE_PROMPTS[details.template]
    
    # Build property description
    property_desc = f"{details.bedrooms}BR/{details.bathrooms}BA home at {details.address}, {details.city}, {details.state}"
    if details.square_feet:
        property_desc += f" ({details.square_feet:,} sq ft)"
    
    features_text = ", ".join(details.features) if details.features else "beautiful features throughout"
    
    # Template-specific additions
    template_details = ""
    if details.template == ListingTemplate.OPEN_HOUSE and details.open_house_date:
        template_details = f"Open House: {details.open_house_date}"
        if details.open_house_time:
            template_details += f" at {details.open_house_time}"
    elif details.template == ListingTemplate.PRICE_DROP and details.previous_price:
        template_details = f"Now priced at {details.price} (reduced from {details.previous_price})"
    
    # Create prompt
    user_message = f"""
Property: {property_desc}
Price: {details.price}
Features: {features_text}
{template_details if template_details else ""}
{f"Agent/Brand: {agent_brand}" if agent_brand else ""}

Create an engaging social media post for this property.
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", template_config["system"]),
        ("user", user_message)
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    import logging
    logger = logging.getLogger("listing_post_generation")
    logger.setLevel(logging.INFO)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.info(f"Generating listing post for template: {details.template}, address: {details.address}, city: {details.city}, state: {details.state}")
    logger.info(f"Prompt to LLM: {user_message}")
    print(" =======  ==== =  === " + llm)
    try:
        if llm:
            logger.info("Calling Groq LLM for listing post generation...")
            caption = await chain.ainvoke({})
            logger.info(f"LLM response: {caption}")
        else:
            logger.warning("GROQ_API_KEY not set or LLM unavailable. Using fallback caption generator.")
            caption = _generate_fallback_caption(details)
            logger.info(f"Fallback caption: {caption}")

        return GeneratedListingPost(
            template_used=details.template,
            caption=caption.strip(),
            hashtags=template_config["hashtags"],
            suggested_cta=template_config["cta"],
            fair_housing_disclaimer=FAIR_HOUSING_DISCLAIMER
        )

    except Exception as e:
        logger.error(f"Error during LLM generation: {e}. Using fallback caption.")
        fallback_caption = _generate_fallback_caption(details)
        logger.info(f"Fallback caption: {fallback_caption}")

        return GeneratedListingPost(
            template_used=details.template,
            caption=fallback_caption,
            hashtags=template_config["hashtags"],
            suggested_cta=template_config["cta"],
            fair_housing_disclaimer=FAIR_HOUSING_DISCLAIMER
        )

def _generate_fallback_caption(details: ListingDetails) -> str:
    """Generate a simple fallback caption if LLM is unavailable"""
    
    templates = {
        ListingTemplate.JUST_LISTED: f"🏡 JUST LISTED! Beautiful {details.bedrooms}BR/{details.bathrooms}BA home at {details.address} for {details.price}. {', '.join(details.features[:3]) if details.features else 'Amazing features throughout'}. Don't miss this opportunity!",
        
        ListingTemplate.OPEN_HOUSE: f"🏠 OPEN HOUSE this weekend! Come see this stunning {details.bedrooms}BR/{details.bathrooms}BA home at {details.address}. Priced at {details.price}. {details.open_house_date + ' ' + (details.open_house_time or '') if details.open_house_date else 'See you there!'}",
        
        ListingTemplate.PRICE_DROP: f"💰 PRICE REDUCED! This beautiful {details.bedrooms}BR/{details.bathrooms}BA home at {details.address} is now {details.price}. {f'Previously {details.previous_price}. ' if details.previous_price else ''}Great value in today's market!",
        
        ListingTemplate.SOLD: f"🎉 SOLD! Another successful closing at {details.address}. Thank you to our wonderful buyers and sellers for trusting us with your real estate needs. Ready to buy or sell? Let's chat!",
        
        ListingTemplate.COMING_SOON: f"🔜 COMING SOON! Exciting new listing at {details.address} - {details.bedrooms}BR/{details.bathrooms}BA home. Stay tuned for details!"
    }
    
    return templates.get(details.template, f"Beautiful {details.bedrooms}BR/{details.bathrooms}BA home at {details.address} for {details.price}.")
