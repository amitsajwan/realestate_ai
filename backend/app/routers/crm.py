#!/usr/bin/env python3
"""
Advanced CRM Router
===================
Handles CRM operations, lead scoring, and business intelligence
"""

import os
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import json
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

router = APIRouter()

# Import shared utilities
from app.utils import verify_jwt_token

class LeadScoringService:
    """Advanced lead scoring algorithm"""
    
    def __init__(self):
        self.scoring_weights = {
            'budget_match': 0.25,
            'urgency': 0.20,
            'location_preference': 0.15,
            'property_type': 0.15,
            'timeline': 0.15,
            'communication': 0.10
        }
    
    def calculate_lead_score(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive lead score"""
        try:
            total_score = 0
            score_breakdown = {}
            
            # Budget match scoring (0-100)
            budget_score = self._score_budget_match(
                lead_data.get('budget', 0),
                lead_data.get('property_price', 0)
            )
            total_score += budget_score * self.scoring_weights['budget_match']
            score_breakdown['budget_match'] = budget_score
            
            # Urgency scoring (0-100)
            urgency_score = self._score_urgency(
                lead_data.get('timeline', ''),
                lead_data.get('urgency_level', '')
            )
            total_score += urgency_score * self.scoring_weights['urgency']
            score_breakdown['urgency'] = urgency_score
            
            # Location preference scoring (0-100)
            location_score = self._score_location_preference(
                lead_data.get('preferred_locations', []),
                lead_data.get('current_location', '')
            )
            total_score += location_score * self.scoring_weights['location_preference']
            score_breakdown['location_preference'] = location_score
            
            # Property type scoring (0-100)
            property_score = self._score_property_type(
                lead_data.get('property_type_preference', ''),
                lead_data.get('available_properties', [])
            )
            total_score += property_score * self.scoring_weights['property_type']
            score_breakdown['property_type'] = property_score
            
            # Timeline scoring (0-100)
            timeline_score = self._score_timeline(
                lead_data.get('timeline', ''),
                lead_data.get('market_conditions', '')
            )
            total_score += timeline_score * self.scoring_weights['timeline']
            score_breakdown['timeline'] = timeline_score
            
            # Communication scoring (0-100)
            communication_score = self._score_communication(
                lead_data.get('response_time', 0),
                lead_data.get('communication_frequency', 0)
            )
            total_score += communication_score * self.scoring_weights['communication']
            score_breakdown['communication'] = communication_score
            
            # Determine lead quality
            quality = self._determine_quality(total_score)
            
            return {
                'total_score': round(total_score, 2),
                'quality': quality,
                'score_breakdown': score_breakdown,
                'recommendations': self._generate_recommendations(score_breakdown),
                'priority': self._determine_priority(total_score, quality)
            }
            
        except Exception as e:
            logger.error(f"Lead scoring error: {e}")
            return {
                'total_score': 0,
                'quality': 'Unknown',
                'error': str(e)
            }
    
    def _score_budget_match(self, budget: float, property_price: float) -> float:
        """Score budget match (0-100)"""
        if not budget or not property_price:
            return 50  # Neutral score
        
        ratio = min(budget, property_price) / max(budget, property_price)
        if ratio >= 0.9:
            return 100  # Excellent match
        elif ratio >= 0.8:
            return 85   # Good match
        elif ratio >= 0.7:
            return 70   # Fair match
        elif ratio >= 0.6:
            return 55   # Poor match
        else:
            return 30   # Very poor match
    
    def _score_urgency(self, timeline: str, urgency_level: str) -> float:
        """Score urgency (0-100)"""
        urgency_scores = {
            'immediate': 100,
            'urgent': 90,
            'high': 80,
            'medium': 60,
            'low': 40,
            'flexible': 30
        }
        
        # Check timeline keywords
        timeline_lower = timeline.lower()
        if any(word in timeline_lower for word in ['asap', 'immediately', 'urgent', 'quick']):
            return 95
        elif any(word in timeline_lower for word in ['this month', 'next month', 'soon']):
            return 75
        elif any(word in timeline_lower for word in ['3 months', '6 months', 'flexible']):
            return 50
        else:
            return urgency_scores.get(urgency_level.lower(), 50)
    
    def _score_location_preference(self, preferred_locations: List[str], current_location: str) -> float:
        """Score location preference (0-100)"""
        if not preferred_locations:
            return 50
        
        # Check if current location matches preferences
        if current_location in preferred_locations:
            return 100
        
        # Check for nearby locations (simplified)
        mumbai_areas = ['mumbai', 'thane', 'navi mumbai', 'panvel']
        pune_areas = ['pune', 'pimpri', 'hinjewadi', 'wakad']
        
        current_lower = current_location.lower()
        preferred_lower = [loc.lower() for loc in preferred_locations]
        
        # Check if in same metro area
        if any(area in current_lower for area in mumbai_areas) and any(area in preferred_lower for area in mumbai_areas):
            return 80
        elif any(area in current_lower for area in pune_areas) and any(area in preferred_lower for area in pune_areas):
            return 80
        else:
            return 40
    
    def _score_property_type(self, preference: str, available: List[str]) -> float:
        """Score property type match (0-100)"""
        if not preference or not available:
            return 50
        
        preference_lower = preference.lower()
        available_lower = [prop.lower() for prop in available]
        
        if preference_lower in available_lower:
            return 100
        elif any(pref in available_lower for pref in ['apartment', 'flat']) and 'apartment' in preference_lower:
            return 90
        elif any(pref in available_lower for pref in ['house', 'villa', 'bungalow']) and any(pref in preference_lower for pref in ['house', 'villa', 'bungalow']):
            return 90
        else:
            return 60
    
    def _score_timeline(self, timeline: str, market_conditions: str) -> float:
        """Score timeline feasibility (0-100)"""
        timeline_lower = timeline.lower()
        
        # Check if timeline is realistic
        if any(word in timeline_lower for word in ['asap', 'immediately']):
            return 70  # Challenging but possible
        elif any(word in timeline_lower for word in ['this month', 'next month']):
            return 85  # Realistic
        elif any(word in timeline_lower for word in ['3 months', '6 months']):
            return 95  # Very realistic
        else:
            return 80  # Default to realistic
    
    def _score_communication(self, response_time: float, frequency: float) -> float:
        """Score communication quality (0-100)"""
        if not response_time or not frequency:
            return 50
        
        # Response time scoring (lower is better)
        if response_time <= 1:  # 1 hour or less
            response_score = 100
        elif response_time <= 4:  # 4 hours or less
            response_score = 85
        elif response_time <= 24:  # 24 hours or less
            response_score = 70
        else:
            response_score = 50
        
        # Frequency scoring (higher is better, but not too high)
        if frequency >= 3:  # 3+ interactions per week
            frequency_score = 90
        elif frequency >= 2:  # 2 interactions per week
            frequency_score = 100
        elif frequency >= 1:  # 1 interaction per week
            frequency_score = 80
        else:
            frequency_score = 60
        
        return (response_score + frequency_score) / 2
    
    def _determine_quality(self, score: float) -> str:
        """Determine lead quality based on score"""
        if score >= 90:
            return 'Premium'
        elif score >= 80:
            return 'High'
        elif score >= 70:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        elif score >= 50:
            return 'Average'
        else:
            return 'Low'
    
    def _determine_priority(self, score: float, quality: str) -> str:
        """Determine lead priority"""
        if score >= 85:
            return 'High'
        elif score >= 70:
            return 'Medium'
        else:
            return 'Low'
    
    def _generate_recommendations(self, score_breakdown: Dict[str, float]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if score_breakdown.get('budget_match', 0) < 70:
            recommendations.append("Consider properties closer to client's budget range")
        
        if score_breakdown.get('urgency', 0) < 70:
            recommendations.append("Follow up more frequently to understand urgency")
        
        if score_breakdown.get('location_preference', 0) < 70:
            recommendations.append("Explore properties in preferred locations")
        
        if score_breakdown.get('communication', 0) < 70:
            recommendations.append("Improve response time and communication frequency")
        
        if not recommendations:
            recommendations.append("Lead is well-qualified, maintain current approach")
        
        return recommendations

# Initialize lead scoring service
lead_scoring = LeadScoringService()

class CRMService:
    """Advanced CRM service with MongoDB persistence"""
    
    def __init__(self, db = None):
        self.db = db
        self.leads_collection = None
        self.deals_collection = None
        self.activities_collection = None
        
        if self.db is not None:
            self.leads_collection = self.db.leads
            self.deals_collection = self.db.deals
            self.activities_collection = self.db.activities
            # Initialize demo data in MongoDB
            self._initialize_demo_data()
    
    async def _initialize_demo_data(self):
        """Initialize with demo data in MongoDB"""
        try:
            # Check if demo data already exists
            existing_leads = await self.leads_collection.count_documents({})
            if existing_leads > 0:
                return
                
            # Insert demo leads
            demo_leads = [
                {
                    'name': 'Rajesh Kumar',
                    'email': 'rajesh@email.com',
                    'phone': '+919876543210',
                    'budget': 5000000,
                    'property_type_preference': 'Apartment',
                    'preferred_locations': ['Mumbai', 'Thane'],
                    'timeline': '3 months',
                    'urgency_level': 'medium',
                    'source': 'Website',
                    'status': 'New',
                    'created_at': datetime.utcnow() - timedelta(days=2),
                    'last_contact': datetime.utcnow() - timedelta(days=1)
                },
                {
                    'name': 'Priya Sharma',
                    'email': 'priya@email.com',
                    'phone': '+919876543211',
                    'budget': 8000000,
                    'property_type_preference': 'Villa',
                    'preferred_locations': ['Pune', 'Hinjewadi'],
                    'timeline': 'ASAP',
                    'urgency_level': 'high',
                    'source': 'Referral',
                    'status': 'Qualified',
                    'created_at': datetime.utcnow() - timedelta(days=5),
                    'last_contact': datetime.utcnow()
                }
            ]
            
            await self.leads_collection.insert_many(demo_leads)
            
            # Insert demo deals
            demo_deals = [
                {
                    'lead_id': (await self.leads_collection.find_one({'name': 'Priya Sharma'}))['_id'],
                    'property_id': ObjectId(),  # Placeholder
                    'value': 7500000,
                    'stage': 'Negotiation',
                    'probability': 80,
                    'expected_close': datetime.utcnow() + timedelta(days=30),
                    'created_at': datetime.utcnow() - timedelta(days=3)
                }
            ]
            
            await self.deals_collection.insert_many(demo_deals)
            
        except Exception as e:
            logger.error(f"Error initializing demo data: {e}")
    
    async def get_lead_analytics(self) -> Dict[str, Any]:
        """Get comprehensive lead analytics"""
        try:
            if self.leads_collection is None:
                return {'error': 'Database not connected'}
                
            total_leads = await self.leads_collection.count_documents({})
            qualified_leads = await self.leads_collection.count_documents({'status': 'Qualified'})
            conversion_rate = (qualified_leads / total_leads * 100) if total_leads > 0 else 0
            
            # Get all leads for scoring analysis
            leads_cursor = self.leads_collection.find({})
            leads = await leads_cursor.to_list(length=None)
            
            # Lead scoring analysis
            lead_scores = []
            for lead in leads:
                score_data = lead_scoring.calculate_lead_score(lead)
                lead_scores.append({
                    'lead_id': str(lead['_id']),
                    'name': lead.get('name', 'Unknown'),
                    'score': score_data.get('total_score', 0),
                    'quality': score_data.get('quality', 'Unknown'),
                    'priority': score_data.get('priority', 'Low')
                })
            
            # Sort by score
            lead_scores.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'total_leads': total_leads,
                'qualified_leads': qualified_leads,
                'conversion_rate': round(conversion_rate, 2),
                'lead_scores': lead_scores,
                'top_leads': lead_scores[:5],
                'average_score': round(sum(ls['score'] for ls in lead_scores) / len(lead_scores), 2) if lead_scores else 0
            }
            
        except Exception as e:
            logger.error(f"Lead analytics error: {e}")
            return {'error': str(e)}
    
    async def get_deal_pipeline(self) -> Dict[str, Any]:
        """Get deal pipeline analysis"""
        try:
            if self.deals_collection is None:
                return {'error': 'Database not connected'}
                
            deals_cursor = self.deals_collection.find({})
            deals = await deals_cursor.to_list(length=None)
            
            total_deals = len(deals)
            total_value = sum(deal['value'] for deal in deals)
            weighted_value = sum(deal['value'] * deal['probability'] / 100 for deal in deals)
            
            # Stage breakdown
            stages = {}
            for deal in deals:
                stage = deal['stage']
                if stage not in stages:
                    stages[stage] = {'count': 0, 'value': 0}
                stages[stage]['count'] += 1
                stages[stage]['value'] += deal['value']
            
            return {
                'total_deals': total_deals,
                'total_value': total_value,
                'weighted_value': round(weighted_value, 2),
                'stages': stages,
                'average_deal_size': round(total_value / total_deals, 2) if total_deals > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Deal pipeline error: {e}")
            return {'error': str(e)}

# Initialize CRM service
from app.core.database import get_database

async def get_crm_service():
    """Get CRM service with database connection"""
    db = get_database()
    return CRMService(db)

# For backward compatibility, create a global instance
crm_service = None

@router.get("/analytics/dashboard")
async def get_crm_analytics_dashboard(request: Request):
    """Get CRM analytics dashboard data"""
    try:
        # Token verification
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token")

        token = token.split(" ")[1]
        payload = verify_jwt_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get CRM service with database connection
        crm_svc = await get_crm_service()
        
        # Get analytics
        lead_analytics = await crm_svc.get_lead_analytics()
        deal_pipeline = await crm_svc.get_deal_pipeline()
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "lead_analytics": lead_analytics,
                "deal_pipeline": deal_pipeline,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CRM analytics dashboard error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )

@router.get("/analytics")
async def get_crm_analytics(request: Request):
    """Get comprehensive CRM analytics"""
    try:
        # Token verification
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token")

        token = token.split(" ")[1]
        payload = verify_jwt_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get CRM service with database connection
        crm_svc = await get_crm_service()
        
        # Get analytics
        lead_analytics = await crm_svc.get_lead_analytics()
        deal_pipeline = await crm_svc.get_deal_pipeline()
        
        return JSONResponse(content={
            "success": True,
            "lead_analytics": lead_analytics,
            "deal_pipeline": deal_pipeline,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CRM analytics error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )

@router.get("/leads/stats")
async def get_crm_leads_stats(request: Request):
    """Get CRM leads statistics"""
    try:
        # Token verification
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token")

        token = token.split(" ")[1]
        payload = verify_jwt_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get CRM service with database connection
        crm_svc = await get_crm_service()
        
        # Get lead analytics
        lead_analytics = await crm_svc.get_lead_analytics()
        
        return JSONResponse(content={
            "success": True,
            "data": lead_analytics
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get CRM leads stats error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )

@router.get("/leads")
async def get_crm_leads(request: Request):
    """Get all CRM leads with scoring"""
    try:
        logger.info("Starting CRM leads request")
        
        # Token verification
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            logger.error("No valid Authorization header")
            raise HTTPException(status_code=401, detail="Invalid token")

        token = token.split(" ")[1]
        logger.info(f"Verifying token: {token[:20]}...")
        
        try:
            payload = verify_jwt_token(token)
            if not payload:
                logger.error("Token verification returned None")
                raise HTTPException(status_code=401, detail="Invalid token")
            logger.info("Token verified successfully")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get CRM service with database connection
        logger.info("Getting CRM service...")
        try:
            crm_svc = await get_crm_service()
            logger.info("CRM service obtained")
        except Exception as e:
            logger.error(f"Failed to get CRM service: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"Failed to get CRM service: {str(e)}"}
            )
        
        # Get leads with scoring
        if crm_svc.leads_collection is None:
            logger.error("Leads collection is None")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Database not connected"}
            )
        
        logger.info("Querying leads from database...")
        try:
            leads_cursor = crm_svc.leads_collection.find({})
            leads = await leads_cursor.to_list(length=None)
            logger.info(f"Found {len(leads)} leads")
        except Exception as e:
            logger.error(f"Failed to query leads: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"Failed to query leads: {str(e)}"}
            )
        
        leads_with_scores = []
        logger.info("Processing leads with scoring...")
        for i, lead in enumerate(leads):
            try:
                score_data = lead_scoring.calculate_lead_score(lead)
                lead_with_score = lead.copy()
                lead_with_score['_id'] = str(lead['_id'])  # Convert ObjectId to string
                
                # Convert datetime objects to ISO strings for JSON serialization
                for key, value in lead_with_score.items():
                    if hasattr(value, 'isoformat'):  # Check if it's a datetime object
                        lead_with_score[key] = value.isoformat()
                
                lead_with_score['scoring'] = score_data
                leads_with_scores.append(lead_with_score)
            except Exception as e:
                logger.error(f"Error processing lead {lead.get('_id', 'unknown')}: {e}")
                # Add lead without scoring if scoring fails
                lead_with_score = lead.copy()
                lead_with_score['_id'] = str(lead['_id'])
                
                # Convert datetime objects to ISO strings for JSON serialization
                for key, value in lead_with_score.items():
                    if hasattr(value, 'isoformat'):  # Check if it's a datetime object
                        lead_with_score[key] = value.isoformat()
                
                lead_with_score['scoring'] = {
                    'total_score': 0,
                    'quality': 'Unknown',
                    'priority': 'Low',
                    'error': str(e)
                }
                leads_with_scores.append(lead_with_score)
        
        # Sort by score (with error handling)
        logger.info("Sorting leads by score...")
        try:
            leads_with_scores.sort(key=lambda x: x.get('scoring', {}).get('total_score', 0), reverse=True)
            logger.info("Leads sorted successfully")
        except Exception as e:
            logger.error(f"Error sorting leads: {e}")
            # Continue without sorting if there's an error
        
        logger.info(f"Returning {len(leads_with_scores)} leads")
        return JSONResponse(content={
            "success": True,
            "leads": leads_with_scores,
            "count": len(leads_with_scores)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get CRM leads error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Internal server error: {str(e)}"}
        )

@router.post("/leads")
async def create_crm_lead(request: Request):
    """Create new CRM lead"""
    try:
        # Token verification
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token")

        token = token.split(" ")[1]
        payload = verify_jwt_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Parse request body
        body = await request.json()
        
        # Get CRM service with database connection
        crm_svc = await get_crm_service()
        
        # Create new lead
        new_lead = {
            'name': body.get('name', ''),
            'email': body.get('email', ''),
            'phone': body.get('phone', ''),
            'budget': body.get('budget', 0),
            'property_type_preference': body.get('property_type_preference', ''),
            'preferred_locations': body.get('preferred_locations', []),
            'timeline': body.get('timeline', ''),
            'urgency_level': body.get('urgency_level', 'medium'),
            'source': body.get('source', 'Website'),
            'status': 'New',
            'created_at': datetime.utcnow(),
            'last_contact': datetime.utcnow()
        }
        
        # Insert into MongoDB
        result = await crm_svc.leads_collection.insert_one(new_lead)
        new_lead['_id'] = str(result.inserted_id)
        
        # Calculate score for new lead
        score_data = lead_scoring.calculate_lead_score(new_lead)
        
        return JSONResponse(content={
            "success": True,
            "lead": new_lead,
            "scoring": score_data,
            "message": "Lead created successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create CRM lead error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )

@router.get("/deals")
async def get_crm_deals(request: Request):
    """Get all CRM deals"""
    try:
        # Token verification
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token")

        token = token.split(" ")[1]
        payload = verify_jwt_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get CRM service with database connection
        crm_svc = await get_crm_service()
        
        # Get deals from MongoDB
        deals_cursor = crm_svc.deals_collection.find({})
        deals = await deals_cursor.to_list(length=None)
        
        # Convert ObjectIds to strings
        for deal in deals:
            deal['_id'] = str(deal['_id'])
            if 'lead_id' in deal and isinstance(deal['lead_id'], ObjectId):
                deal['lead_id'] = str(deal['lead_id'])
        
        return JSONResponse(content={
            "success": True,
            "deals": deals,
            "count": len(deals)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get CRM deals error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )
