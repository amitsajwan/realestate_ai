"""Localization models for multi-language support."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class Language(str, Enum):
    """Supported languages."""
    ENGLISH = "en"
    MARATHI = "mr"
    HINDI = "hi"
    GUJARATI = "gu"
    TAMIL = "ta"
    TELUGU = "te"
    KANNADA = "kn"
    BENGALI = "bn"


class PropertyType(str, Enum):
    """Property types for India market."""
    APARTMENT = "apartment"
    VILLA = "villa"
    INDEPENDENT_HOUSE = "independent_house"
    BUILDER_FLOOR = "builder_floor"
    PENTHOUSE = "penthouse"
    STUDIO = "studio"
    PLOT = "plot"
    COMMERCIAL = "commercial"
    OFFICE = "office"
    SHOP = "shop"
    WAREHOUSE = "warehouse"
    FARMHOUSE = "farmhouse"


class LocationDetails(BaseModel):
    """Location details for Indian properties."""
    city: str = Field(..., description="City name")
    locality: str = Field(..., description="Locality/Area name")
    society: Optional[str] = Field(None, description="Society/Building name")
    landmark: Optional[str] = Field(None, description="Nearby landmark")
    pincode: Optional[str] = Field(None, description="Pin code")
    state: str = Field(..., description="State name")
    
    # Marathi translations
    city_mr: Optional[str] = Field(None, description="City name in Marathi")
    locality_mr: Optional[str] = Field(None, description="Locality in Marathi")
    state_mr: Optional[str] = Field(None, description="State name in Marathi")


class IndianListingDetails(BaseModel):
    """Listing details specific to Indian real estate market."""
    property_type: Optional[PropertyType] = Field(..., description="Type of property")
    price: Optional[float] = Field(..., description="Price in INR")
    price_per_sqft: Optional[float] = Field(None, description="Price per square foot")
    carpet_area: Optional[float] = Field(None, description="Carpet area in sq ft")
    built_up_area: Optional[float] = Field(None, description="Built-up area in sq ft")
    super_area: Optional[float] = Field(None, description="Super built-up area in sq ft")
    
    # Property details
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, description="Number of bathrooms")
    balconies: Optional[int] = Field(None, description="Number of balconies")
    parking: Optional[int] = Field(None, description="Number of parking spaces")
    floor: Optional[str] = Field(None, description="Floor number (e.g., '3 out of 5')")
    
    # Financial details
    maintenance: Optional[float] = Field(None, description="Monthly maintenance in INR")
    security_deposit: Optional[float] = Field(None, description="Security deposit in INR")
    
    # Property features
    furnished: Optional[str] = Field(None, description="Furnished/Semi-furnished/Unfurnished")
    facing: Optional[str] = Field(None, description="Property facing direction")
    age_of_property: Optional[str] = Field(None, description="Age of property")
    
    # Legal details
    ownership_type: Optional[str] = Field(None, description="Freehold/Leasehold")
    rera_id: Optional[str] = Field(None, description="RERA registration ID")
    
    # Location
    location: Optional[LocationDetails] = Field(..., description="Property location details")
    
    # Description
    description: Optional[str] = Field(..., description="Property description")
    description_mr: Optional[str] = Field(None, description="Property description in Marathi")
    
    # Agent contact
    contact_preference: Optional[str] = Field(None, description="Preferred contact method")


class TranslationEntry(BaseModel):
    """Translation entry for a specific key."""
    key: str = Field(..., description="Translation key")
    english: str = Field(..., description="English text")
    marathi: str = Field(..., description="Marathi text")
    hindi: Optional[str] = Field(None, description="Hindi text")


class MarathiTemplates:
    """Marathi language templates for social media posts."""
    
    # Just Listed templates
    just_listed_templates = [
        "🏠 नवीन संपत्ती! {location} मध्ये सुंदर {property_type}। किंमत: ₹{price}। आज च संपर्क साधा! #RealEstate #Property #Maharashtra",
        "✨ नुकतीच लिस्ट झाली! {location} मधील {bedrooms}BHK {property_type}। {carpet_area} चौ.फूट, ₹{price}। तुमचे स्वप्नांचे घर आहे का? #PropertyAlert #Maharashtra",
        "🔥 HOT PROPERTY! {location} मध्ये {property_type}, फक्त ₹{price}। {furnished} स्थितीत. लगेच पाहायला या! #NewListing #RealEstate"
    ]
    
    # Open House templates  
    open_house_templates = [
        "🏡 ओपन हाउस! {date} रोजी {time} वाजता {location} मध्ये. {property_type} पाहा. नोंदणी आवश्यक नाही! #OpenHouse #PropertyViewing",
        "👀 घर पाहायची संधी! {location} मधील सुंदर {property_type}. {date} ला {time} वाजता ओपन हाउस. सर्वांचे स्वागत! #PropertyShow #RealEstate",
        "🗓️ {date} रोजी ओपन हाउस! {location} - {property_type}, ₹{price}. कुटुंबासह या आणि तुमचे नवे घर पाहा! #OpenHouse"
    ]
    
    # Price Drop templates
    price_drop_templates = [
        "💰 किंमत कमी! {location} मधील {property_type} आता फक्त ₹{price} (पूर्वी ₹{old_price}). मोठी बचत! #PriceDrop #BestDeal",
        "🔻 मोठी सूट! {property_type} in {location}, ₹{old_price} वरून ₹{price}. ही संधी सुटू देऊ नका! #PropertyDeal #Discount",
        "⚡ URGENT सूट! {location} - {property_type} च्या किंमतीत ₹{discount} ची कपात. आता ₹{price}! #UrgentSale #PriceReduced"
    ]
    
    # Sold templates
    sold_templates = [
        "🎉 विकले गेले! {location} मधील {property_type} यशस्वीपणे विकले. आमच्या क्लायंटचे स्वप्न पूर्ण झाले! #SOLD #HappyClient",
        "✅ डील पूर्ण! {location} - {property_type} विकले गेले. तुमच्या प्रॉपर्टीची विक्री करायची आहे का? संपर्क साधा! #PropertySold #RealEstate",
        "🏆 यशस्वी विक्री! {location} मधील {property_type} {days} दिवसात विकले. आम्ही तुमच्याही प्रॉपर्टी लवकर विकू शकतो! #FastSale #SOLD"
    ]
    
    # Coming Soon templates
    coming_soon_templates = [
        "🔜 लवकरच येत आहे! {location} मध्ये नवीन {property_type} प्रोजेक्ट. अगोदर नोंदणी करा! #ComingSoon #PreLaunch #NewProject",
        "⏳ प्री-लॉन्च ऑफर! {location} - {property_type} लवकरच. विशेष किंमत मिळवा! #PreLaunch #EarlyBird #RealEstate",
        "🚀 नवीन प्रोजेक्ट! {location} मध्ये {property_type}, {launch_date} पासून. आधी बुकिंग सुरू! #NewLaunch #PropertyInvestment"
    ]


class AutoResponseMarathi:
    """Marathi auto-response templates."""
    
    general_inquiry = [
        "नमस्कार! तुमच्या प्रॉपर्टीच्या आवडीबद्दल धन्यवाद. मी लगेच तुम्हाला संपूर्ण माहिती पाठवतो. तुमचा फोन नंबर शेअर करू शकता का?",
        "धन्यवाद! ही प्रॉपर्टी अजूनही उपलब्ध आहे. अधिक माहितीसाठी आणि घर पाहण्यासाठी मला कॉल करा: {phone}",
        "नमस्कार! मला खूष झाले की तुम्हाला ही प्रॉपर्टी आवडली. मी तुम्हाला व्हॉट्सऍपवर संपूर्ण डिटेल्स पाठवतो. तुमचा नंबर?"
    ]
    
    price_inquiry = [
        "प्रॉपर्टीची किंमत ₹{price} आहे. EMI तुम्ही ₹{emi} पासून सुरू करू शकता. अधिक माहितीसाठी मला कॉल करा!",
        "किंमत: ₹{price}. होम लोनसाठी मी तुम्हाला मदत करू शकतो. सर्वोत्तम रेट मिळवून देतो. संपर्क करा: {phone}",
        "₹{price} मध्ये ही प्रॉपर्टी उपलब्ध आहे. तुमचे बजेट काय आहे? योग्य ऑप्शन्स सुचवतो."
    ]
    
    availability_inquiry = [
        "होय, ही प्रॉपर्टी अजूनही उपलब्ध आहे! घर पाहण्यासाठी कधी येऊ शकता? मी अपॉइंटमेंट बुक करतो.",
        "अजूनही उपलब्ध आहे! तुम्ही आज किंवा उद्या पाहू शकता. व्हिडिओ कॉलवर देखील दाखवू शकतो.",
        "होय उपलब्ध आहे! पण अनेकांना आवडत आहे. लवकर निर्णय घ्या. आज पाहायला या!"
    ]
    
    viewing_request = [
        "नक्कीच! घर पाहण्यासाठी आपोंतमेंट: कधी सोयीस्कर आहे? सकाळ 10 ते सायंकाळ 7 पर्यंत उपलब्ध आहे.",
        "छान! व्हिडिओ कॉल किंवा फिजिकल व्हिजिट काय करायचे? दोन्ही उपलब्ध आहे. तुमची पसंती?",
        "घर पाहायला जरूर या! आजच्या आजच वेळ द्या. मी सर्व डॉक्युमेंट्स तयार ठेवतो."
    ]
