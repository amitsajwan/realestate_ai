"""India market listing templates with Marathi support."""
from typing import Dict, List, Optional, Any
from models.localization import IndianListingDetails, Language, PropertyType
from services.localization_service import LocalizationService
from services.listing_templates import ListingTemplate
import random
from datetime import datetime, timedelta


class IndiaListingTemplateService:
    """Enhanced listing template service for India market with Marathi support."""
    
    def __init__(self):
        self.localization = LocalizationService()
        # ListingTemplate is an enum, not a class to instantiate
        self.available_templates = list(ListingTemplate)
    
    def get_available_templates(self, language: Language = Language.ENGLISH) -> Dict[str, Any]:
        """Get available templates for India market."""
        templates = {
            "just_listed": {
                "name": "Just Listed" if language == Language.ENGLISH else "नुकते लिस्ट झाले",
                "description": "Fresh property listing announcement",
                "description_mr": "नवीन प्रॉपर्टी लिस्टिंग घोषणा"
            },
            "open_house": {
                "name": "Open House" if language == Language.ENGLISH else "ओपन हाउस",
                "description": "Open house event announcement",
                "description_mr": "ओपन हाउस कार्यक्रम घोषणा"
            },
            "price_drop": {
                "name": "Price Drop" if language == Language.ENGLISH else "किंमत कमी",
                "description": "Price reduction announcement",
                "description_mr": "किंमत कपात घोषणा"
            },
            "sold": {
                "name": "Sold" if language == Language.ENGLISH else "विकले गेले",
                "description": "Property sold celebration",
                "description_mr": "प्रॉपर्टी विकली गेल्याची घोषणा"
            },
            "coming_soon": {
                "name": "Coming Soon" if language == Language.ENGLISH else "लवकरच येत आहे",
                "description": "Pre-launch property announcement",
                "description_mr": "प्री-लॉन्च प्रॉपर्टी घोषणा"
            },
            "rental": {
                "name": "For Rent" if language == Language.ENGLISH else "भाड्याने",
                "description": "Rental property listing",
                "description_mr": "भाड्याच्या प्रॉपर्टीची यादी"
            },
            "investment": {
                "name": "Investment Opportunity" if language == Language.ENGLISH else "गुंतवणुकीची संधी",
                "description": "Investment property promotion",
                "description_mr": "गुंतवणूक प्रॉपर्टी प्रमोशन"
            }
        }
        return templates
    
    def generate_listing_post(self, listing_details: IndianListingDetails, 
                            template_type: str = "just_listed",
                            language: Language = Language.MARATHI,
                            include_hashtags: bool = True) -> Dict[str, Any]:
        """Generate a listing post for India market."""
        
        if language == Language.MARATHI:
            # Use Marathi template generation
            post_text = self.localization.generate_marathi_listing_post(
                listing_details, template_type
            )
            
            if include_hashtags:
                hashtags = self.localization.get_marathi_hashtags(
                    listing_details.property_type.value,
                    listing_details.location.locality
                )
                post_text += "\n\n" + " ".join(hashtags)
            
            return {
                "success": True,
                "post_text": post_text,
                "language": "marathi",
                "template_type": template_type,
                "character_count": len(post_text),
                "hashtags": hashtags if include_hashtags else []
            }
        
        else:
            # Use English template generation
            return self._generate_english_post(listing_details, template_type, include_hashtags)
    
    def _generate_english_post(self, listing: IndianListingDetails, 
                             template_type: str, include_hashtags: bool) -> Dict[str, Any]:
        """Generate English post for India market."""
        
        # English templates for India market
        templates = {
            "just_listed": [
                "🏠 NEW LISTING! Beautiful {property_type} in {location}. {bedrooms}BHK, {area} sq ft. Price: {price}. Ready to move! Contact now!",
                "✨ FRESH ON MARKET! Stunning {property_type} at {location}. {furnished} condition, {price}. Great investment opportunity!",
                "🔥 HOT PROPERTY! {property_type} in prime {location}. {area} sq ft, {parking} parking. Priced at {price}. Don't miss out!"
            ],
            "rental": [
                "🏡 FOR RENT! Spacious {property_type} in {location}. {bedrooms}BHK, {furnished}. Rent: {price}/month + maintenance. Available immediately!",
                "🔑 RENTAL ALERT! Premium {property_type} at {location}. {area} sq ft, {amenities}. Monthly rent: {price}. Security deposit: {deposit}.",
                "🏠 AVAILABLE FOR RENT! Beautiful {property_type} in {location}. {bedrooms}BHK, ready to move. {price}/month. Family preferred!"
            ],
            "investment": [
                "💰 INVESTMENT OPPORTUNITY! {property_type} in developing {location}. Current price: {price}. Expected appreciation: 15-20% annually!",
                "📈 SMART INVESTMENT! {property_type} near upcoming metro station in {location}. {price} - prices set to rise! Limited units available.",
                "🏆 BEST ROI! {property_type} in {location} IT corridor. Rental yield: 8-10%. Purchase price: {price}. Perfect for investors!"
            ]
        }
        
        # Use base templates if specific not found
        if template_type not in templates:
            # Fallback to basic English generation
            base_post = self.base_service.generate_fallback_caption(
                property_type=listing.property_type.value,
                location=listing.location.locality,
                price=self.localization.format_price_inr(listing.price),
                bedrooms=listing.bedrooms or 0
            )
            
            hashtags = ["#RealEstate", "#Property", "#India", f"#{listing.location.city}"]
            if include_hashtags:
                base_post += "\n\n" + " ".join(hashtags)
            
            return {
                "success": True,
                "post_text": base_post,
                "language": "english",
                "template_type": template_type,
                "character_count": len(base_post),
                "hashtags": hashtags if include_hashtags else []
            }
        
        # Select random template
        template = random.choice(templates[template_type])
        
        # Prepare values for formatting
        values = {
            "property_type": listing.property_type.value.replace("_", " ").title(),
            "location": listing.location.locality,
            "bedrooms": listing.bedrooms or "N/A",
            "area": listing.carpet_area or listing.built_up_area or "N/A",
            "price": self.localization.format_price_inr(listing.price),
            "furnished": listing.furnished or "Unfurnished",
            "parking": f"{listing.parking} car" if listing.parking else "No",
        }
        
        # Add specific values for rental
        if template_type == "rental":
            values["deposit"] = self.localization.format_price_inr(
                listing.security_deposit or listing.price * 3
            )
            values["amenities"] = "Modern amenities"
        
        # Format the post
        try:
            post_text = template.format(**values)
        except KeyError:
            # Fallback if formatting fails
            post_text = template
            for key, value in values.items():
                post_text = post_text.replace(f"{{{key}}}", str(value))
        
        # Add hashtags
        hashtags = [
            "#RealEstate", "#Property", "#India", 
            f"#{listing.location.city}", f"#{listing.property_type.value}",
            "#Investment", "#HomeLoans"
        ]
        
        if include_hashtags:
            post_text += "\n\n" + " ".join(hashtags)
        
        # Add fair housing disclaimer
        post_text += "\n\n📋 Equal housing opportunity. No discrimination."
        
        return {
            "success": True,
            "post_text": post_text,
            "language": "english",
            "template_type": template_type,
            "character_count": len(post_text),
            "hashtags": hashtags if include_hashtags else []
        }
    
    def generate_multilingual_post(self, listing_details: IndianListingDetails,
                                 template_type: str = "just_listed") -> Dict[str, Any]:
        """Generate posts in both English and Marathi."""
        
        english_post = self.generate_listing_post(
            listing_details, template_type, Language.ENGLISH
        )
        
        marathi_post = self.generate_listing_post(
            listing_details, template_type, Language.MARATHI
        )
        
        return {
            "success": True,
            "english": english_post,
            "marathi": marathi_post,
            "template_type": template_type
        }
    
    def get_location_suggestions(self, city: str) -> List[Dict[str, str]]:
        """Get popular localities for a city with translations."""
        
        localities = {
            "mumbai": [
                {"en": "Andheri", "mr": "अंधेरी"},
                {"en": "Bandra", "mr": "बांद्रा"},
                {"en": "Juhu", "mr": "जुहू"},
                {"en": "Powai", "mr": "पवई"},
                {"en": "Worli", "mr": "वरळी"},
                {"en": "Lower Parel", "mr": "लोअर परेल"},
                {"en": "Malad", "mr": "मलाड"},
                {"en": "Borivali", "mr": "बोरिवली"}
            ],
            "pune": [
                {"en": "Hinjewadi", "mr": "हिंजेवाडी"},
                {"en": "Koregaon Park", "mr": "कोरेगावपार्क"},
                {"en": "Viman Nagar", "mr": "विमान नगर"},
                {"en": "Baner", "mr": "बानेर"},
                {"en": "Wakad", "mr": "वाकड"},
                {"en": "Aundh", "mr": "औंध"},
                {"en": "Magarpatta", "mr": "मगरपट्टा"},
                {"en": "Hadapsar", "mr": "हडपसर"}
            ],
            "nagpur": [
                {"en": "Wardha Road", "mr": "वर्धा रोड"},
                {"en": "Civil Lines", "mr": "सिव्हिल लाईन्स"},
                {"en": "Dharampeth", "mr": "धरमपेठ"},
                {"en": "Ramdaspeth", "mr": "रामदास पेठ"},
                {"en": "Sadar", "mr": "सदर"},
                {"en": "Hingna", "mr": "हिंगणा"}
            ]
        }
        
        return localities.get(city.lower(), [])
    
    def format_indian_address(self, listing: IndianListingDetails) -> Dict[str, str]:
        """Format address in Indian style for both languages."""
        
        # English format
        address_en = f"{listing.location.society or ''}, {listing.location.locality}, {listing.location.city}, {listing.location.state}"
        if listing.location.pincode:
            address_en += f" - {listing.location.pincode}"
        
        # Marathi format
        society_mr = listing.location.society or ""
        locality_mr = listing.location.locality_mr or listing.location.locality
        city_mr = listing.location.city_mr or listing.location.city
        state_mr = listing.location.state_mr or listing.location.state
        
        address_mr = f"{society_mr}, {locality_mr}, {city_mr}, {state_mr}"
        if listing.location.pincode:
            address_mr += f" - {listing.location.pincode}"
        
        return {
            "english": address_en.strip(", "),
            "marathi": address_mr.strip(", ")
        }
