from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class ListingTemplate(str, Enum):
    JUST_LISTED = "just_listed"
    OPEN_HOUSE = "open_house" 
    PRICE_DROP = "price_drop"
    SOLD = "sold"
    COMING_SOON = "coming_soon"

class ListingDetails(BaseModel):
    template: ListingTemplate
    address: str
    city: str
    state: str
    zip_code: Optional[str] = None
    price: str
    bedrooms: int
    bathrooms: float
    square_feet: Optional[int] = None
    features: List[str] = []
    
    # Template-specific fields
    open_house_date: Optional[str] = None  # For open_house template
    open_house_time: Optional[str] = None
    previous_price: Optional[str] = None   # For price_drop template
    listing_agent: Optional[str] = None
    mls_number: Optional[str] = None

class GeneratedListingPost(BaseModel):
    template_used: ListingTemplate
    caption: str
    hashtags: List[str]
    suggested_cta: str
    fair_housing_disclaimer: str
