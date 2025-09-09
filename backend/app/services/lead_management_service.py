#!/usr/bin/env python3
"""
Advanced Lead Management Service
===============================
Comprehensive lead management with scoring, automation, and analytics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import asyncio
import json

from app.schemas.lead import (
    LeadCreate, LeadUpdate, LeadResponse, LeadStats, LeadScoring,
    LeadActivity, LeadSearchFilters, LeadSearchResult,
    LeadStatus, LeadUrgency, LeadSource
)

logger = logging.getLogger(__name__)

class LeadScoringEngine:
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
    
    def calculate_lead_score(self, lead_data: Dict[str, Any], available_properties: List[Dict] = None) -> LeadScoring:
        """Calculate comprehensive lead score"""
        try:
            total_score = 0
            score_breakdown = {}
            
            # Budget match scoring (0-100)
            budget_score = self._score_budget_match(
                lead_data.get('budget', 0),
                available_properties or []
            )
            total_score += budget_score * self.scoring_weights['budget_match']
            score_breakdown['budget_match'] = budget_score
            
            # Urgency scoring (0-100)
            urgency_score = self._score_urgency(
                lead_data.get('urgency', 'medium'),
                lead_data.get('timeline', '')
            )
            total_score += urgency_score * self.scoring_weights['urgency']
            score_breakdown['urgency'] = urgency_score
            
            # Location preference scoring (0-100)
            location_score = self._score_location_preference(
                lead_data.get('location_preference', ''),
                available_properties or []
            )
            total_score += location_score * self.scoring_weights['location_preference']
            score_breakdown['location_preference'] = location_score
            
            # Property type scoring (0-100)
            property_score = self._score_property_type(
                lead_data.get('property_type_preference', ''),
                available_properties or []
            )
            total_score += property_score * self.scoring_weights['property_type']
            score_breakdown['property_type'] = property_score
            
            # Timeline scoring (0-100)
            timeline_score = self._score_timeline(
                lead_data.get('timeline', ''),
                lead_data.get('urgency', 'medium')
            )
            total_score += timeline_score * self.scoring_weights['timeline']
            score_breakdown['timeline'] = timeline_score
            
            # Communication scoring (0-100)
            communication_score = self._score_communication(
                lead_data.get('last_contact_date'),
                lead_data.get('created_at')
            )
            total_score += communication_score * self.scoring_weights['communication']
            score_breakdown['communication'] = communication_score
            
            # Determine lead quality
            quality = self._determine_quality(total_score)
            
            return LeadScoring(
                total_score=round(total_score, 2),
                quality=quality,
                score_breakdown=score_breakdown,
                recommendations=self._generate_recommendations(score_breakdown),
                last_calculated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error calculating lead score: {e}")
            return LeadScoring(
                total_score=50.0,
                quality="fair",
                score_breakdown={},
                recommendations=["Unable to calculate score"],
                last_calculated=datetime.utcnow()
            )
    
    def _score_budget_match(self, budget: float, properties: List[Dict]) -> float:
        """Score based on budget match with available properties"""
        if not budget or not properties:
            return 50.0
        
        # Find properties within budget range
        matching_properties = [
            p for p in properties 
            if p.get('price', 0) <= budget * 1.2 and p.get('price', 0) >= budget * 0.8
        ]
        
        if not matching_properties:
            return 20.0
        
        # Calculate match percentage
        match_percentage = len(matching_properties) / len(properties) * 100
        return min(match_percentage, 100.0)
    
    def _score_urgency(self, urgency: str, timeline: str) -> float:
        """Score based on urgency and timeline"""
        urgency_scores = {
            'urgent': 100.0,
            'high': 80.0,
            'medium': 60.0,
            'low': 40.0
        }
        
        base_score = urgency_scores.get(urgency, 60.0)
        
        # Adjust based on timeline
        timeline_keywords = {
            'asap': 1.2,
            'immediately': 1.2,
            'urgent': 1.2,
            'this week': 1.1,
            'this month': 1.0,
            'next month': 0.9,
            'in 3 months': 0.8,
            'in 6 months': 0.7
        }
        
        timeline_multiplier = 1.0
        for keyword, multiplier in timeline_keywords.items():
            if keyword in timeline.lower():
                timeline_multiplier = multiplier
                break
        
        return min(base_score * timeline_multiplier, 100.0)
    
    def _score_location_preference(self, location: str, properties: List[Dict]) -> float:
        """Score based on location preference match"""
        if not location or not properties:
            return 50.0
        
        location_lower = location.lower()
        matching_properties = [
            p for p in properties 
            if location_lower in p.get('location', '').lower()
        ]
        
        if not matching_properties:
            return 30.0
        
        match_percentage = len(matching_properties) / len(properties) * 100
        return min(match_percentage, 100.0)
    
    def _score_property_type(self, property_type: str, properties: List[Dict]) -> float:
        """Score based on property type match"""
        if not property_type or not properties:
            return 50.0
        
        type_lower = property_type.lower()
        matching_properties = [
            p for p in properties 
            if type_lower in p.get('property_type', '').lower()
        ]
        
        if not matching_properties:
            return 30.0
        
        match_percentage = len(matching_properties) / len(properties) * 100
        return min(match_percentage, 100.0)
    
    def _score_timeline(self, timeline: str, urgency: str) -> float:
        """Score based on timeline urgency"""
        if not timeline:
            return 50.0
        
        timeline_lower = timeline.lower()
        
        # Immediate timeline
        if any(word in timeline_lower for word in ['asap', 'immediately', 'urgent', 'today', 'tomorrow']):
            return 100.0
        
        # Short timeline
        if any(word in timeline_lower for word in ['this week', 'next week', 'within a week']):
            return 85.0
        
        # Medium timeline
        if any(word in timeline_lower for word in ['this month', 'next month', 'within a month']):
            return 70.0
        
        # Long timeline
        if any(word in timeline_lower for word in ['in 3 months', 'in 6 months', 'next year']):
            return 40.0
        
        return 50.0
    
    def _score_communication(self, last_contact: Optional[datetime], created_at: Optional[datetime]) -> float:
        """Score based on communication frequency"""
        if not last_contact or not created_at:
            return 50.0
        
        days_since_contact = (datetime.utcnow() - last_contact).days
        days_since_created = (datetime.utcnow() - created_at).days
        
        # Recent contact is good
        if days_since_contact <= 1:
            return 100.0
        elif days_since_contact <= 3:
            return 80.0
        elif days_since_contact <= 7:
            return 60.0
        elif days_since_contact <= 14:
            return 40.0
        else:
            return 20.0
    
    def _determine_quality(self, score: float) -> str:
        """Determine lead quality based on score"""
        if score >= 80:
            return "excellent"
        elif score >= 65:
            return "good"
        elif score >= 45:
            return "fair"
        else:
            return "poor"
    
    def _generate_recommendations(self, score_breakdown: Dict[str, float]) -> List[str]:
        """Generate recommendations based on score breakdown"""
        recommendations = []
        
        if score_breakdown.get('budget_match', 0) < 50:
            recommendations.append("Consider showing properties in different price ranges")
        
        if score_breakdown.get('urgency', 0) < 50:
            recommendations.append("Follow up more frequently to increase urgency")
        
        if score_breakdown.get('location_preference', 0) < 50:
            recommendations.append("Expand search to nearby areas")
        
        if score_breakdown.get('property_type', 0) < 50:
            recommendations.append("Show different property types")
        
        if score_breakdown.get('communication', 0) < 50:
            recommendations.append("Increase communication frequency")
        
        return recommendations

class LeadManagementService:
    """Comprehensive lead management service"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.leads_collection = db.leads
        self.lead_activities_collection = db.lead_activities
        self.properties_collection = db.properties
        self.scoring_engine = LeadScoringEngine()
    
    async def create_lead(self, lead_data: LeadCreate, agent_id: str, team_id: Optional[str] = None) -> LeadResponse:
        """Create a new lead with automatic scoring"""
        try:
            # Get available properties for scoring
            properties = await self._get_available_properties()
            
            # Convert to dict for scoring
            lead_dict = lead_data.model_dump()
            lead_dict['agent_id'] = agent_id
            lead_dict['team_id'] = team_id
            lead_dict['created_at'] = datetime.utcnow()
            lead_dict['updated_at'] = datetime.utcnow()
            lead_dict['status'] = LeadStatus.NEW
            
            # Calculate initial score
            scoring = self.scoring_engine.calculate_lead_score(lead_dict, properties)
            lead_dict['score'] = int(scoring.total_score)
            lead_dict['scoring'] = scoring.model_dump()
            
            # Insert lead
            result = await self.leads_collection.insert_one(lead_dict)
            lead_dict['id'] = str(result.inserted_id)
            
            # Create initial activity
            await self._create_activity(
                lead_id=str(result.inserted_id),
                activity_type="created",
                description="Lead created",
                performed_by=agent_id
            )
            
            return LeadResponse(**lead_dict)
            
        except Exception as e:
            logger.error(f"Error creating lead: {e}")
            raise
    
    async def update_lead(self, lead_id: str, update_data: LeadUpdate, agent_id: str) -> LeadResponse:
        """Update lead with automatic re-scoring"""
        try:
            # Get current lead
            lead = await self.leads_collection.find_one({"_id": ObjectId(lead_id)})
            if not lead:
                raise ValueError("Lead not found")
            
            # Update fields
            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict['updated_at'] = datetime.utcnow()
            
            # Recalculate score if relevant fields changed
            if any(field in update_dict for field in ['budget', 'urgency', 'timeline', 'property_type_preference', 'location_preference']):
                properties = await self._get_available_properties()
                lead_dict = {**lead, **update_dict}
                scoring = self.scoring_engine.calculate_lead_score(lead_dict, properties)
                update_dict['score'] = int(scoring.total_score)
                update_dict['scoring'] = scoring.model_dump()
            
            # Update lead
            await self.leads_collection.update_one(
                {"_id": ObjectId(lead_id)},
                {"$set": update_dict}
            )
            
            # Create activity
            await self._create_activity(
                lead_id=lead_id,
                activity_type="updated",
                description="Lead updated",
                performed_by=agent_id
            )
            
            # Return updated lead
            updated_lead = await self.leads_collection.find_one({"_id": ObjectId(lead_id)})
            updated_lead['id'] = str(updated_lead['_id'])
            
            # Get activities
            activities = await self._get_lead_activities(lead_id)
            updated_lead['activities'] = activities
            
            return LeadResponse(**updated_lead)
            
        except Exception as e:
            logger.error(f"Error updating lead: {e}")
            raise
    
    async def get_lead(self, lead_id: str) -> Optional[LeadResponse]:
        """Get lead by ID"""
        try:
            lead = await self.leads_collection.find_one({"_id": ObjectId(lead_id)})
            if not lead:
                return None
            
            lead['id'] = str(lead['_id'])
            activities = await self._get_lead_activities(lead_id)
            lead['activities'] = activities
            
            return LeadResponse(**lead)
            
        except Exception as e:
            logger.error(f"Error getting lead: {e}")
            raise
    
    async def search_leads(self, filters: LeadSearchFilters, agent_id: str, page: int = 1, per_page: int = 20) -> LeadSearchResult:
        """Search leads with filters"""
        try:
            # Build query
            query = {"agent_id": agent_id}
            
            if filters.status:
                query["status"] = filters.status.value
            
            if filters.urgency:
                query["urgency"] = filters.urgency.value
            
            if filters.source:
                query["source"] = filters.source.value
            
            if filters.assigned_agent_id:
                query["assigned_agent_id"] = filters.assigned_agent_id
            
            if filters.team_id:
                query["team_id"] = filters.team_id
            
            if filters.min_budget or filters.max_budget:
                budget_query = {}
                if filters.min_budget:
                    budget_query["$gte"] = filters.min_budget
                if filters.max_budget:
                    budget_query["$lte"] = filters.max_budget
                query["budget"] = budget_query
            
            if filters.min_score or filters.max_score:
                score_query = {}
                if filters.min_score:
                    score_query["$gte"] = filters.min_score
                if filters.max_score:
                    score_query["$lte"] = filters.max_score
                query["score"] = score_query
            
            if filters.date_from or filters.date_to:
                date_query = {}
                if filters.date_from:
                    date_query["$gte"] = filters.date_from
                if filters.date_to:
                    date_query["$lte"] = filters.date_to
                query["created_at"] = date_query
            
            if filters.search_term:
                search_regex = {"$regex": filters.search_term, "$options": "i"}
                query["$or"] = [
                    {"name": search_regex},
                    {"email": search_regex},
                    {"phone": search_regex},
                    {"location_preference": search_regex}
                ]
            
            # Get total count
            total = await self.leads_collection.count_documents(query)
            
            # Get leads with pagination
            skip = (page - 1) * per_page
            leads_cursor = self.leads_collection.find(query).skip(skip).limit(per_page).sort("created_at", -1)
            leads = await leads_cursor.to_list(length=per_page)
            
            # Convert to response format
            lead_responses = []
            for lead in leads:
                lead['id'] = str(lead['_id'])
                activities = await self._get_lead_activities(lead['id'])
                lead['activities'] = activities
                lead_responses.append(LeadResponse(**lead))
            
            total_pages = (total + per_page - 1) // per_page
            
            return LeadSearchResult(
                leads=lead_responses,
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
                filters_applied=filters
            )
            
        except Exception as e:
            logger.error(f"Error searching leads: {e}")
            raise
    
    async def get_lead_stats(self, agent_id: str, team_id: Optional[str] = None) -> LeadStats:
        """Get comprehensive lead statistics"""
        try:
            # Build base query
            base_query = {"agent_id": agent_id}
            if team_id:
                base_query["team_id"] = team_id
            
            # Get counts by status
            pipeline = [
                {"$match": base_query},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            
            status_counts = await self.leads_collection.aggregate(pipeline).to_list(length=None)
            status_dict = {item["_id"]: item["count"] for item in status_counts}
            
            # Get total leads
            total_leads = await self.leads_collection.count_documents(base_query)
            
            # Get conversion rate
            converted = status_dict.get("converted", 0)
            conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0
            
            # Get average deal value
            pipeline = [
                {"$match": {**base_query, "status": "converted"}},
                {"$group": {
                    "_id": None,
                    "avg_value": {"$avg": "$conversion_value"},
                    "total_value": {"$sum": "$conversion_value"}
                }}
            ]
            
            value_stats = await self.leads_collection.aggregate(pipeline).to_list(length=1)
            avg_value = value_stats[0]["avg_value"] if value_stats else 0
            total_pipeline = value_stats[0]["total_value"] if value_stats else 0
            
            # Get time-based stats
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=7)
            month_start = today_start - timedelta(days=30)
            
            leads_today = await self.leads_collection.count_documents({
                **base_query,
                "created_at": {"$gte": today_start}
            })
            
            leads_this_week = await self.leads_collection.count_documents({
                **base_query,
                "created_at": {"$gte": week_start}
            })
            
            leads_this_month = await self.leads_collection.count_documents({
                **base_query,
                "created_at": {"$gte": month_start}
            })
            
            return LeadStats(
                total_leads=total_leads,
                new_leads=status_dict.get("new", 0),
                contacted_leads=status_dict.get("contacted", 0),
                qualified_leads=status_dict.get("qualified", 0),
                converted_leads=converted,
                lost_leads=status_dict.get("lost", 0),
                conversion_rate=round(conversion_rate, 2),
                average_deal_value=round(avg_value, 2),
                total_pipeline_value=round(total_pipeline, 2),
                leads_this_month=leads_this_month,
                leads_this_week=leads_this_week,
                leads_today=leads_today
            )
            
        except Exception as e:
            logger.error(f"Error getting lead stats: {e}")
            raise
    
    async def _get_available_properties(self) -> List[Dict]:
        """Get available properties for scoring"""
        try:
            properties = await self.properties_collection.find({
                "status": "active",
                "publishing_status": "published"
            }).to_list(length=100)
            return properties
        except Exception as e:
            logger.error(f"Error getting properties: {e}")
            return []
    
    async def _create_activity(self, lead_id: str, activity_type: str, description: str, performed_by: str, metadata: Optional[Dict] = None):
        """Create lead activity"""
        try:
            activity = {
                "lead_id": lead_id,
                "activity_type": activity_type,
                "description": description,
                "performed_by": performed_by,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            result = await self.lead_activities_collection.insert_one(activity)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error creating activity: {e}")
            raise
    
    async def _get_lead_activities(self, lead_id: str) -> List[LeadActivity]:
        """Get lead activities"""
        try:
            activities_cursor = self.lead_activities_collection.find(
                {"lead_id": lead_id}
            ).sort("timestamp", -1)
            
            activities = await activities_cursor.to_list(length=50)
            
            return [
                LeadActivity(
                    id=str(activity["_id"]),
                    lead_id=activity["lead_id"],
                    activity_type=activity["activity_type"],
                    description=activity["description"],
                    performed_by=activity["performed_by"],
                    timestamp=activity["timestamp"],
                    metadata=activity.get("metadata")
                )
                for activity in activities
            ]
            
        except Exception as e:
            logger.error(f"Error getting activities: {e}")
            return []