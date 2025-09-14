"""
Demo API endpoints for testing
Provides working endpoints that don't require complex authentication
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from app.core.auth_backend import current_active_user
from app.models.user import User

router = APIRouter()

# Demo data
DEMO_LEADS = [
    {
        "id": 1,
        "name": "Rohit Sharma",
        "email": "rohit.sharma@email.com", 
        "phone": "+91-9876543210",
        "status": "hot_lead",
        "budget": "₹50L - ₹75L",
        "location": "Bandra, Mumbai",
        "created_at": "2024-01-15"
    },
    {
        "id": 2,
        "name": "Priya Patel", 
        "email": "priya.patel@email.com",
        "phone": "+91-9876543211",
        "status": "warm_lead",
        "budget": "₹75L - ₹1Cr",
        "location": "Powai, Mumbai", 
        "created_at": "2024-01-16"
    },
    {
        "id": 3,
        "name": "Amit Kumar",
        "email": "amit.kumar@email.com",
        "phone": "+91-9876543212", 
        "status": "cold_lead",
        "budget": "₹30L - ₹50L",
        "location": "Andheri, Mumbai",
        "created_at": "2024-01-17"
    }
]

DEMO_PROPERTIES = [
    {
        "id": 1,
        "title": "Luxury 3BHK in Bandra",
        "price": "₹2.5 Cr",
        "location": "Bandra West, Mumbai",
        "area": "1250 sq ft",
        "bedrooms": 3,
        "bathrooms": 2,
        "status": "available",
        "features": ["Sea View", "Gym", "Swimming Pool"],
        "created_at": "2024-01-10"
    },
    {
        "id": 2, 
        "title": "Modern 2BHK in Powai",
        "price": "₹1.8 Cr",
        "location": "Powai, Mumbai",
        "area": "950 sq ft", 
        "bedrooms": 2,
        "bathrooms": 2,
        "status": "available",
        "features": ["Lake View", "Club House", "Security"],
        "created_at": "2024-01-12"
    },
    {
        "id": 3,
        "title": "Spacious 4BHK in Juhu", 
        "price": "₹4.2 Cr",
        "location": "Juhu, Mumbai",
        "area": "1800 sq ft",
        "bedrooms": 4, 
        "bathrooms": 3,
        "status": "sold",
        "features": ["Beach View", "Terrace Garden", "Parking"],
        "created_at": "2024-01-08"
    }
]

@router.get("/demo/leads")
async def get_demo_leads(current_user: User = Depends(current_active_user)):
    """Get demo leads data - working endpoint"""
    
    # Get current user
    user = current_user
    
    return {
        "success": True,
        "leads": DEMO_LEADS,
        "total": len(DEMO_LEADS),
        "user": user["name"] if user else "Demo User"
    }

@router.post("/demo/leads")
async def create_demo_lead(request: Request, current_user: User = Depends(current_active_user)):
    """Create new demo lead"""
    
    user = current_user
    
    try:
        lead_data = await request.json()
        
        # Create new lead with demo ID
        new_lead = {
            "id": len(DEMO_LEADS) + 1,
            "name": lead_data.get("name", "New Lead"),
            "email": lead_data.get("email", "new@email.com"),
            "phone": lead_data.get("phone", "+91-9876543213"),
            "status": lead_data.get("status", "new_lead"),
            "budget": lead_data.get("budget", "₹50L+"),
            "location": lead_data.get("location", "Mumbai"),
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        
        DEMO_LEADS.append(new_lead)
        
        return {
            "success": True,
            "message": "Lead created successfully",
            "lead": new_lead
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request data: {e}")

@router.get("/demo/properties")
async def get_demo_properties(current_user: User = Depends(current_active_user)):
    """Get demo properties data - working endpoint"""
    
    user = current_user
    
    return {
        "success": True,
        "properties": DEMO_PROPERTIES,
        "total": len(DEMO_PROPERTIES), 
        "user": user["name"] if user else "Demo User"
    }

@router.post("/demo/properties") 
async def create_demo_property(request: Request, current_user: User = Depends(current_active_user)):
    """Create new demo property"""
    
    user = current_user
    
    try:
        property_data = await request.json()
        
        new_property = {
            "id": len(DEMO_PROPERTIES) + 1,
            "title": property_data.get("title", "New Property"),
            "price": property_data.get("price", "₹1 Cr"),
            "location": property_data.get("location", "Mumbai"),
            "area": property_data.get("area", "1000 sq ft"),
            "bedrooms": property_data.get("bedrooms", 2),
            "bathrooms": property_data.get("bathrooms", 1),
            "status": "available",
            "features": property_data.get("features", ["New Property"]),
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        
        DEMO_PROPERTIES.append(new_property)
        
        return {
            "success": True,
            "message": "Property created successfully", 
            "property": new_property
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request data: {e}")

@router.get("/demo/dashboard")
async def get_demo_dashboard(current_user: User = Depends(current_active_user)):
    """Get demo dashboard data"""
    
    user = current_user
    
    # Calculate some demo metrics
    total_leads = len(DEMO_LEADS)
    hot_leads = len([l for l in DEMO_LEADS if l["status"] == "hot_lead"])
    total_properties = len(DEMO_PROPERTIES)
    available_properties = len([p for p in DEMO_PROPERTIES if p["status"] == "available"])
    
    return {
        "success": True,
        "dashboard": {
            "leads": {
                "total": total_leads,
                "hot": hot_leads,
                "conversion_rate": f"{(hot_leads/total_leads*100):.1f}%" if total_leads > 0 else "0%"
            },
            "properties": {
                "total": total_properties, 
                "available": available_properties,
                "sold": total_properties - available_properties
            },
            "recent_activity": [
                "New lead: Rohit Sharma",
                "Property listed: Luxury 3BHK",
                "Lead converted: Priya Patel",
                "Property sold: Spacious 4BHK"
            ]
        },
        "user": user["name"] if user else "Demo User"
    }

@router.get("/demo/status")
async def get_demo_api_status():
    """Get API status - always working endpoint for testing"""
    
    return {
        "success": True,
        "status": "API Working",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "leads": "/api/demo/leads",
            "properties": "/api/demo/properties", 
            "dashboard": "/api/demo/dashboard"
        },
        "message": "Demo API endpoints are functioning correctly"
    }

@router.get("/demo/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
