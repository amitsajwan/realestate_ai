"""Localization service for multi-language support."""
import json
from typing import Dict, Any, Optional, List
from models.localization import (
    Language, IndianListingDetails, MarathiTemplates, 
    AutoResponseMarathi, TranslationEntry
)
import random


class LocalizationService:
    """Service for handling localization and translations."""
    
    def __init__(self):
        # Use the classes directly (they contain class attributes)
        self.marathi_templates = MarathiTemplates
        self.marathi_responses = AutoResponseMarathi
        self.translations = self._load_translations()
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translation dictionary."""
        return {
            # Common real estate terms
            "property": {"en": "Property", "mr": "मालमत्ता"},
            "house": {"en": "House", "mr": "घर"},
            "apartment": {"en": "Apartment", "mr": "फ्लॅट"},
            "villa": {"en": "Villa", "mr": "व्हिला"},
            "plot": {"en": "Plot", "mr": "प्लॉट"},
            "price": {"en": "Price", "mr": "किंमत"},
            "area": {"en": "Area", "mr": "क्षेत्रफळ"},
            "bedroom": {"en": "Bedroom", "mr": "बेडरूम"},
            "bathroom": {"en": "Bathroom", "mr": "बाथरूम"},
            "parking": {"en": "Parking", "mr": "पार्किंग"},
            "balcony": {"en": "Balcony", "mr": "बालकनी"},
            
            # Location terms
            "near": {"en": "Near", "mr": "जवळ"},
            "location": {"en": "Location", "mr": "स्थान"},
            "society": {"en": "Society", "mr": "सोसायटी"},
            "building": {"en": "Building", "mr": "इमारत"},
            
            # Transaction terms
            "for_sale": {"en": "For Sale", "mr": "विक्रीसाठी"},
            "for_rent": {"en": "For Rent", "mr": "भाड्याने"},
            "sold": {"en": "SOLD", "mr": "विकले गेले"},
            "rented": {"en": "RENTED", "mr": "भाड्याने दिले"},
            
            # Features
            "furnished": {"en": "Furnished", "mr": "सुसज्ज"},
            "unfurnished": {"en": "Unfurnished", "mr": "रिकामे"},
            "semi_furnished": {"en": "Semi-Furnished", "mr": "अर्ध-सुसज्ज"},
            "ready_to_move": {"en": "Ready to Move", "mr": "राहण्यासाठी तयार"},
            "under_construction": {"en": "Under Construction", "mr": "बांधकाम सुरू"},
            
            # Contact terms
            "contact": {"en": "Contact", "mr": "संपर्क"},
            "call": {"en": "Call", "mr": "कॉल करा"},
            "whatsapp": {"en": "WhatsApp", "mr": "व्हॉट्सऍप"},
            "visit": {"en": "Visit", "mr": "भेट द्या"},
            "schedule": {"en": "Schedule", "mr": "वेळापत्रक"},
            
            # Common phrases
            "interested": {"en": "Interested", "mr": "स्वारस्य"},
            "available": {"en": "Available", "mr": "उपलब्ध"},
            "thank_you": {"en": "Thank you", "mr": "धन्यवाद"},
            "welcome": {"en": "Welcome", "mr": "स्वागत"},
            "best_deal": {"en": "Best Deal", "mr": "सर्वोत्तम ऑफर"},
            "urgent": {"en": "Urgent", "mr": "तातडीचे"},
            "new": {"en": "New", "mr": "नवीन"},
            "exclusive": {"en": "Exclusive", "mr": "खास"},
            
            # Financial terms
            "emi": {"en": "EMI", "mr": "EMI"},
            "loan": {"en": "Loan", "mr": "कर्ज"},
            "down_payment": {"en": "Down Payment", "mr": "डाउन पेमेंट"},
            "registration": {"en": "Registration", "mr": "नोंदणी"},
            "brokerage": {"en": "Brokerage", "mr": "दलाली"},
            
            # Time-related
            "today": {"en": "Today", "mr": "आज"},
            "tomorrow": {"en": "Tomorrow", "mr": "उद्या"},
            "immediately": {"en": "Immediately", "mr": "लगेच"},
            "soon": {"en": "Soon", "mr": "लवकरच"},
        }
    
    def translate(self, key: str, language: Language = Language.MARATHI) -> str:
        """Translate a key to specified language."""
        if key in self.translations:
            return self.translations[key].get(language.value, key)
        return key
    
    def format_price_inr(self, price: float) -> str:
        """Format price in Indian format (Lakhs/Crores)."""
        if price >= 10000000:  # 1 Crore
            crores = price / 10000000
            if crores == int(crores):
                return f"₹{int(crores)} Cr"
            else:
                return f"₹{crores:.1f} Cr"
        elif price >= 100000:  # 1 Lakh
            lakhs = price / 100000
            if lakhs == int(lakhs):
                return f"₹{int(lakhs)} L"
            else:
                return f"₹{lakhs:.1f} L"
        else:
            return f"₹{int(price):,}"
    
    def generate_marathi_listing_post(self, listing: IndianListingDetails, 
                                    template_type: str = "just_listed") -> str:
        """Generate a Marathi social media post for a listing."""
        
        # Format price
        formatted_price = self.format_price_inr(listing.price)
        
        # Get appropriate templates
        templates = []
        if template_type == "just_listed":
            templates = self.marathi_templates.just_listed_templates
        elif template_type == "open_house":
            templates = self.marathi_templates.open_house_templates
        elif template_type == "price_drop":
            templates = self.marathi_templates.price_drop_templates
        elif template_type == "sold":
            templates = self.marathi_templates.sold_templates
        elif template_type == "coming_soon":
            templates = self.marathi_templates.coming_soon_templates
        else:
            templates = self.marathi_templates.just_listed_templates
        
        # Select random template
        template = random.choice(templates)
        
        # Prepare replacement values
        values = {
            "location": listing.location.locality_mr or listing.location.locality,
            "property_type": self.translate(listing.property_type.value),
            "price": formatted_price,
            "bedrooms": listing.bedrooms or "N/A",
            "carpet_area": f"{listing.carpet_area} चौ.फूट" if listing.carpet_area else "N/A",
            "furnished": self.translate(listing.furnished.lower() if listing.furnished else "unfurnished"),
        }
        
        # Handle specific template types
        if template_type == "price_drop" and "old_price" in template:
            old_price = listing.price * 1.1  # Assume 10% reduction
            values["old_price"] = self.format_price_inr(old_price)
            values["discount"] = self.format_price_inr(old_price - listing.price)
        
        if template_type == "open_house":
            from datetime import datetime, timedelta
            next_sunday = datetime.now() + timedelta(days=(6 - datetime.now().weekday()))
            values["date"] = next_sunday.strftime("%d/%m")
            values["time"] = "११:०० ते २:००"
        
        if template_type == "sold":
            values["days"] = "२१"  # Marathi numeral for 21
        
        if template_type == "coming_soon":
            from datetime import datetime, timedelta
            launch_date = datetime.now() + timedelta(days=30)
            values["launch_date"] = launch_date.strftime("%B %Y")
        
        # Replace placeholders
        try:
            post = template.format(**values)
        except KeyError:
            # If some placeholders are missing, use basic template
            post = template
            for key, value in values.items():
                post = post.replace(f"{{{key}}}", str(value))
        
        # Add fair housing disclaimer in Marathi
        disclaimer = "\n\n📋 सर्व समुदायांसाठी समान संधी. भेदभाव नाही."
        
        return post + disclaimer
    
    def get_marathi_auto_response(self, comment_text: str, 
                                property_details: Optional[IndianListingDetails] = None) -> str:
        """Get appropriate Marathi auto-response based on comment."""
        
        comment_lower = comment_text.lower()
        
        # Detect inquiry type
        if any(word in comment_lower for word in ["price", "किंमत", "rate", "cost"]):
            responses = self.marathi_responses.price_inquiry
        elif any(word in comment_lower for word in ["available", "उपलब्ध", "free"]):
            responses = self.marathi_responses.availability_inquiry
        elif any(word in comment_lower for word in ["visit", "see", "पाहायचे", "show"]):
            responses = self.marathi_responses.viewing_request
        else:
            responses = self.marathi_responses.general_inquiry
        
        # Select random response
        response = random.choice(responses)
        
        # Replace placeholders if property details available
        if property_details:
            values = {
                "price": self.format_price_inr(property_details.price),
                "phone": "+91-98765-43210",  # Default phone
            }
            
            # Calculate approximate EMI (assuming 20-year loan at 8.5%)
            if property_details.price:
                loan_amount = property_details.price * 0.8  # 80% loan
                monthly_rate = 0.085 / 12
                num_payments = 20 * 12
                emi = (loan_amount * monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
                values["emi"] = self.format_price_inr(emi)
            
            try:
                response = response.format(**values)
            except KeyError:
                # If formatting fails, return as is
                pass
        
        return response
    
    def detect_language(self, text: str) -> Language:
        """Detect language of the text (simple implementation)."""
        # Check for Devanagari script (Marathi/Hindi)
        marathi_chars = any('\u0900' <= char <= '\u097F' for char in text)
        
        if marathi_chars:
            # Simple heuristic: check for common Marathi words
            marathi_words = ["आहे", "मध्ये", "साठी", "चे", "ची", "या", "ते", "पाहायचे"]
            if any(word in text for word in marathi_words):
                return Language.MARATHI
            else:
                return Language.HINDI
        
        return Language.ENGLISH
    
    def get_city_translations(self) -> Dict[str, Dict[str, str]]:
        """Get common Indian city name translations."""
        return {
            "mumbai": {"en": "Mumbai", "mr": "मुंबई"},
            "pune": {"en": "Pune", "mr": "पुणे"},
            "nagpur": {"en": "Nagpur", "mr": "नागपूर"},
            "nashik": {"en": "Nashik", "mr": "नाशिक"},
            "aurangabad": {"en": "Aurangabad", "mr": "औरंगाबाद"},
            "kolhapur": {"en": "Kolhapur", "mr": "कोल्हापूर"},
            "solapur": {"en": "Solapur", "mr": "सोलापूर"},
            "sangli": {"en": "Sangli", "mr": "सांगली"},
            "satara": {"en": "Satara", "mr": "सातारा"},
            "thane": {"en": "Thane", "mr": "ठाणे"},
            "navi_mumbai": {"en": "Navi Mumbai", "mr": "नवी मुंबई"},
            "kalyan": {"en": "Kalyan", "mr": "कल्याण"},
            "dombivli": {"en": "Dombivli", "mr": "डोंबिवली"},
            "vasai": {"en": "Vasai", "mr": "वसई"},
            "virar": {"en": "Virar", "mr": "विरार"},
        }
    
    def get_marathi_hashtags(self, property_type: str, location: str) -> List[str]:
        """Generate relevant Marathi hashtags."""
        base_tags = ["#RealEstate", "#Property", "#मालमत्ता", "#घर", "#Maharashtra", "#मराठी"]
        
        # Add property type specific tags
        if property_type == "apartment":
            base_tags.extend(["#Flat", "#फ्लॅट", "#Apartment"])
        elif property_type == "villa":
            base_tags.extend(["#Villa", "#व्हिला", "#IndependentHouse"])
        elif property_type == "plot":
            base_tags.extend(["#Plot", "#प्लॉट", "#Land"])
        
        # Add location tags
        location_lower = location.lower()
        if "mumbai" in location_lower:
            base_tags.extend(["#Mumbai", "#मुंबई", "#MumbaiProperties"])
        elif "pune" in location_lower:
            base_tags.extend(["#Pune", "#पुणे", "#PuneProperties"])
        
        return base_tags[:10]  # Limit to 10 hashtags
