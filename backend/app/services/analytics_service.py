#!/usr/bin/env python3
"""
Analytics Service
================
Comprehensive analytics and reporting service
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import json

from app.schemas.analytics import (
    AnalyticsFilter, DashboardMetrics, PropertyAnalytics, LeadAnalytics,
    AgentPerformance, TeamAnalytics, MarketAnalytics, RevenueAnalytics,
    AnalyticsMetric, MetricType, AnalyticsPeriod, ChartData
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Comprehensive analytics service"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.properties_collection = db.properties
        self.leads_collection = db.leads
        self.users_collection = db.users
        self.teams_collection = db.teams
        self.audit_logs_collection = db.audit_logs
    
    async def get_dashboard_metrics(self, agent_id: str, team_id: Optional[str], 
                                  filters: AnalyticsFilter) -> DashboardMetrics:
        """Get comprehensive dashboard metrics"""
        try:
            # Get date range
            start_date, end_date = self._get_date_range(filters.period, filters.start_date, filters.end_date)
            
            # Build base query
            base_query = {"agent_id": agent_id}
            if team_id:
                base_query["team_id"] = team_id
            
            # Get property analytics
            property_analytics = await self._get_property_analytics(base_query, start_date, end_date, filters)
            
            # Get lead analytics
            lead_analytics = await self._get_lead_analytics(base_query, start_date, end_date, filters)
            
            # Get team analytics if team_id provided
            team_analytics = None
            if team_id:
                team_analytics = await self._get_team_analytics(team_id, start_date, end_date, filters)
            
            # Get overview metrics
            overview_metrics = await self._get_overview_metrics(base_query, start_date, end_date, filters)
            
            return DashboardMetrics(
                overview_metrics=overview_metrics,
                property_analytics=property_analytics,
                lead_analytics=lead_analytics,
                team_analytics=team_analytics,
                generated_at=datetime.utcnow(),
                period=filters.period,
                date_range={"start": start_date, "end": end_date}
            )
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            raise
    
    async def _get_property_analytics(self, base_query: Dict, start_date: date, 
                                    end_date: date, filters: AnalyticsFilter) -> PropertyAnalytics:
        """Get property analytics"""
        try:
            # Build property query
            property_query = {**base_query}
            if filters.property_types:
                property_query["property_type"] = {"$in": filters.property_types}
            if filters.locations:
                property_query["location"] = {"$in": filters.locations}
            
            # Get total counts
            total_properties = await self.properties_collection.count_documents(property_query)
            published_properties = await self.properties_collection.count_documents({
                **property_query,
                "publishing_status": "published"
            })
            draft_properties = await self.properties_collection.count_documents({
                **property_query,
                "publishing_status": "draft"
            })
            archived_properties = await self.properties_collection.count_documents({
                **property_query,
                "publishing_status": "archived"
            })
            
            # Get price analytics
            price_pipeline = [
                {"$match": property_query},
                {"$group": {
                    "_id": None,
                    "avg_price": {"$avg": "$price"},
                    "total_value": {"$sum": "$price"},
                    "min_price": {"$min": "$price"},
                    "max_price": {"$max": "$price"}
                }}
            ]
            
            price_stats = await self.properties_collection.aggregate(price_pipeline).to_list(1)
            avg_price = price_stats[0]["avg_price"] if price_stats else 0
            total_value = price_stats[0]["total_value"] if price_stats else 0
            
            # Get distributions
            type_distribution = await self._get_property_type_distribution(property_query)
            location_distribution = await self._get_location_distribution(property_query)
            status_distribution = await self._get_property_status_distribution(property_query)
            price_range_distribution = await self._get_price_range_distribution(property_query)
            
            # Get performance metrics
            avg_days_on_market = await self._get_average_days_on_market(property_query)
            conversion_rate = await self._get_property_conversion_rate(property_query)
            
            # Get top performing properties
            top_properties = await self._get_top_performing_properties(property_query)
            
            # Get recent activity
            recent_activity = await self._get_property_recent_activity(property_query)
            
            return PropertyAnalytics(
                total_properties=total_properties,
                published_properties=published_properties,
                draft_properties=draft_properties,
                archived_properties=archived_properties,
                average_price=round(avg_price, 2),
                total_value=round(total_value, 2),
                price_range_distribution=price_range_distribution,
                property_type_distribution=type_distribution,
                location_distribution=location_distribution,
                status_distribution=status_distribution,
                average_days_on_market=avg_days_on_market,
                conversion_rate=conversion_rate,
                top_performing_properties=top_properties,
                recent_activity=recent_activity
            )
            
        except Exception as e:
            logger.error(f"Error getting property analytics: {e}")
            raise
    
    async def _get_lead_analytics(self, base_query: Dict, start_date: date, 
                                end_date: date, filters: AnalyticsFilter) -> LeadAnalytics:
        """Get lead analytics"""
        try:
            # Build lead query
            lead_query = {**base_query}
            if filters.lead_sources:
                lead_query["source"] = {"$in": filters.lead_sources}
            
            # Get counts by status
            status_pipeline = [
                {"$match": lead_query},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            
            status_counts = await self.leads_collection.aggregate(status_pipeline).to_list(None)
            status_dict = {item["_id"]: item["count"] for item in status_counts}
            
            total_leads = sum(status_dict.values())
            converted_leads = status_dict.get("converted", 0)
            conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
            
            # Get average lead score
            score_pipeline = [
                {"$match": lead_query},
                {"$group": {
                    "_id": None,
                    "avg_score": {"$avg": "$score"}
                }}
            ]
            
            score_stats = await self.leads_collection.aggregate(score_pipeline).to_list(1)
            avg_score = score_stats[0]["avg_score"] if score_stats else 0
            
            # Get distributions
            source_distribution = await self._get_lead_source_distribution(lead_query)
            urgency_distribution = await self._get_lead_urgency_distribution(lead_query)
            budget_distribution = await self._get_lead_budget_distribution(lead_query)
            
            # Get deal analytics
            deal_pipeline = [
                {"$match": {**lead_query, "status": "converted"}},
                {"$group": {
                    "_id": None,
                    "avg_deal_value": {"$avg": "$conversion_value"},
                    "total_pipeline": {"$sum": "$conversion_value"}
                }}
            ]
            
            deal_stats = await self.leads_collection.aggregate(deal_pipeline).to_list(1)
            avg_deal_value = deal_stats[0]["avg_deal_value"] if deal_stats else 0
            total_pipeline = deal_stats[0]["total_pipeline"] if deal_stats else 0
            
            # Get performance metrics
            response_time = await self._get_lead_response_time(lead_query)
            follow_up_rate = await self._get_follow_up_completion_rate(lead_query)
            
            # Get top performing sources
            top_sources = await self._get_top_performing_sources(lead_query)
            
            # Get recent activities
            recent_activities = await self._get_lead_recent_activities(lead_query)
            
            return LeadAnalytics(
                total_leads=total_leads,
                new_leads=status_dict.get("new", 0),
                contacted_leads=status_dict.get("contacted", 0),
                qualified_leads=status_dict.get("qualified", 0),
                converted_leads=converted_leads,
                lost_leads=status_dict.get("lost", 0),
                conversion_rate=round(conversion_rate, 2),
                average_lead_score=round(avg_score, 2),
                lead_source_distribution=source_distribution,
                urgency_distribution=urgency_distribution,
                budget_distribution=budget_distribution,
                average_deal_value=round(avg_deal_value, 2),
                total_pipeline_value=round(total_pipeline, 2),
                lead_response_time=response_time,
                follow_up_completion_rate=follow_up_rate,
                top_performing_sources=top_sources,
                recent_activities=recent_activities
            )
            
        except Exception as e:
            logger.error(f"Error getting lead analytics: {e}")
            raise
    
    async def _get_team_analytics(self, team_id: str, start_date: date, 
                                end_date: date, filters: AnalyticsFilter) -> TeamAnalytics:
        """Get team analytics"""
        try:
            # Get team info
            team = await self.teams_collection.find_one({"_id": ObjectId(team_id)})
            if not team:
                raise ValueError("Team not found")
            
            # Get member counts
            total_members = await self.db.team_members.count_documents({"team_id": team_id})
            active_members = await self.db.team_members.count_documents({
                "team_id": team_id,
                "is_active": True
            })
            
            # Get team performance
            team_query = {"team_id": team_id}
            total_leads = await self.leads_collection.count_documents(team_query)
            total_properties = await self.properties_collection.count_documents(team_query)
            
            # Get conversion rate
            converted_leads = await self.leads_collection.count_documents({
                **team_query,
                "status": "converted"
            })
            conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
            
            # Get total sales
            sales_pipeline = [
                {"$match": {**team_query, "status": "converted"}},
                {"$group": {
                    "_id": None,
                    "total_sales": {"$sum": "$conversion_value"}
                }}
            ]
            
            sales_stats = await self.leads_collection.aggregate(sales_pipeline).to_list(1)
            total_sales = sales_stats[0]["total_sales"] if sales_stats else 0
            
            # Get agent performance
            agent_performance = await self._get_agent_performance(team_id, start_date, end_date)
            
            # Get recent activity
            recent_activity = await self._get_team_recent_activity(team_id)
            
            return TeamAnalytics(
                team_id=team_id,
                team_name=team["name"],
                total_members=total_members,
                active_members=active_members,
                total_leads=total_leads,
                total_properties=total_properties,
                total_sales=round(total_sales, 2),
                average_conversion_rate=round(conversion_rate, 2),
                team_performance_score=round(conversion_rate, 2),  # Simplified
                top_performers=agent_performance[:5],
                recent_activity=recent_activity
            )
            
        except Exception as e:
            logger.error(f"Error getting team analytics: {e}")
            raise
    
    async def _get_overview_metrics(self, base_query: Dict, start_date: date, 
                                  end_date: date, filters: AnalyticsFilter) -> List[AnalyticsMetric]:
        """Get overview metrics"""
        try:
            metrics = []
            
            # Total properties
            total_properties = await self.properties_collection.count_documents(base_query)
            metrics.append(AnalyticsMetric(
                name="Total Properties",
                value=total_properties,
                type=MetricType.COUNT,
                description="Total number of properties"
            ))
            
            # Total leads
            total_leads = await self.leads_collection.count_documents(base_query)
            metrics.append(AnalyticsMetric(
                name="Total Leads",
                value=total_leads,
                type=MetricType.COUNT,
                description="Total number of leads"
            ))
            
            # Conversion rate
            converted_leads = await self.leads_collection.count_documents({
                **base_query,
                "status": "converted"
            })
            conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
            metrics.append(AnalyticsMetric(
                name="Conversion Rate",
                value=conversion_rate,
                type=MetricType.PERCENTAGE,
                unit="%",
                description="Lead conversion rate"
            ))
            
            # Average deal value
            deal_pipeline = [
                {"$match": {**base_query, "status": "converted"}},
                {"$group": {
                    "_id": None,
                    "avg_value": {"$avg": "$conversion_value"}
                }}
            ]
            
            deal_stats = await self.leads_collection.aggregate(deal_pipeline).to_list(1)
            avg_deal_value = deal_stats[0]["avg_value"] if deal_stats else 0
            
            metrics.append(AnalyticsMetric(
                name="Average Deal Value",
                value=round(avg_deal_value, 2),
                type=MetricType.SUM,
                unit="$",
                description="Average value of converted deals"
            ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting overview metrics: {e}")
            return []
    
    def _get_date_range(self, period: AnalyticsPeriod, start_date: Optional[date], 
                       end_date: Optional[date]) -> Tuple[date, date]:
        """Get date range based on period"""
        today = date.today()
        
        if period == AnalyticsPeriod.TODAY:
            return today, today
        elif period == AnalyticsPeriod.YESTERDAY:
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        elif period == AnalyticsPeriod.THIS_WEEK:
            start = today - timedelta(days=today.weekday())
            return start, today
        elif period == AnalyticsPeriod.LAST_WEEK:
            start = today - timedelta(days=today.weekday() + 7)
            end = today - timedelta(days=today.weekday() + 1)
            return start, end
        elif period == AnalyticsPeriod.THIS_MONTH:
            start = today.replace(day=1)
            return start, today
        elif period == AnalyticsPeriod.LAST_MONTH:
            if today.month == 1:
                start = today.replace(year=today.year - 1, month=12, day=1)
            else:
                start = today.replace(month=today.month - 1, day=1)
            end = today.replace(day=1) - timedelta(days=1)
            return start, end
        elif period == AnalyticsPeriod.CUSTOM and start_date and end_date:
            return start_date, end_date
        else:
            # Default to this month
            start = today.replace(day=1)
            return start, today
    
    async def _get_property_type_distribution(self, query: Dict) -> Dict[str, int]:
        """Get property type distribution"""
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$property_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = await self.properties_collection.aggregate(pipeline).to_list(None)
        return {item["_id"]: item["count"] for item in results}
    
    async def _get_location_distribution(self, query: Dict) -> Dict[str, int]:
        """Get location distribution"""
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$location",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = await self.properties_collection.aggregate(pipeline).to_list(None)
        return {item["_id"]: item["count"] for item in results}
    
    async def _get_property_status_distribution(self, query: Dict) -> Dict[str, int]:
        """Get property status distribution"""
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$publishing_status",
                "count": {"$sum": 1}
            }}
        ]
        
        results = await self.properties_collection.aggregate(pipeline).to_list(None)
        return {item["_id"]: item["count"] for item in results}
    
    async def _get_price_range_distribution(self, query: Dict) -> Dict[str, int]:
        """Get price range distribution"""
        pipeline = [
            {"$match": query},
            {"$bucket": {
                "groupBy": "$price",
                "boundaries": [0, 100000, 250000, 500000, 750000, 1000000, 2000000, float('inf')],
                "default": "Other",
                "output": {
                    "count": {"$sum": 1}
                }
            }}
        ]
        
        results = await self.properties_collection.aggregate(pipeline).to_list(None)
        return {item["_id"]: item["count"] for item in results}
    
    async def _get_average_days_on_market(self, query: Dict) -> float:
        """Get average days on market"""
        # This would need to be calculated based on when properties were published vs sold
        # For now, return a placeholder
        return 30.0
    
    async def _get_property_conversion_rate(self, query: Dict) -> float:
        """Get property conversion rate"""
        # This would need to be calculated based on properties that led to sales
        # For now, return a placeholder
        return 15.0
    
    async def _get_top_performing_properties(self, query: Dict) -> List[Dict[str, Any]]:
        """Get top performing properties"""
        pipeline = [
            {"$match": query},
            {"$sort": {"price": -1}},
            {"$limit": 5},
            {"$project": {
                "title": 1,
                "price": 1,
                "location": 1,
                "property_type": 1,
                "publishing_status": 1
            }}
        ]
        
        return await self.properties_collection.aggregate(pipeline).to_list(5)
    
    async def _get_property_recent_activity(self, query: Dict) -> List[Dict[str, Any]]:
        """Get recent property activity"""
        # This would need to be implemented based on your activity tracking
        return []
    
    async def _get_lead_source_distribution(self, query: Dict) -> Dict[str, int]:
        """Get lead source distribution"""
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$source",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = await self.leads_collection.aggregate(pipeline).to_list(None)
        return {item["_id"]: item["count"] for item in results}
    
    async def _get_lead_urgency_distribution(self, query: Dict) -> Dict[str, int]:
        """Get lead urgency distribution"""
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$urgency",
                "count": {"$sum": 1}
            }}
        ]
        
        results = await self.leads_collection.aggregate(pipeline).to_list(None)
        return {item["_id"]: item["count"] for item in results}
    
    async def _get_lead_budget_distribution(self, query: Dict) -> Dict[str, int]:
        """Get lead budget distribution"""
        pipeline = [
            {"$match": {**query, "budget": {"$exists": True, "$ne": None}}},
            {"$bucket": {
                "groupBy": "$budget",
                "boundaries": [0, 100000, 250000, 500000, 750000, 1000000, 2000000, float('inf')],
                "default": "Other",
                "output": {
                    "count": {"$sum": 1}
                }
            }}
        ]
        
        results = await self.leads_collection.aggregate(pipeline).to_list(None)
        return {item["_id"]: item["count"] for item in results}
    
    async def _get_lead_response_time(self, query: Dict) -> float:
        """Get average lead response time"""
        # This would need to be calculated based on when leads were created vs first contact
        return 2.5  # hours
    
    async def _get_follow_up_completion_rate(self, query: Dict) -> float:
        """Get follow-up completion rate"""
        # This would need to be calculated based on scheduled vs completed follow-ups
        return 85.0  # percentage
    
    async def _get_top_performing_sources(self, query: Dict) -> List[Dict[str, Any]]:
        """Get top performing lead sources"""
        pipeline = [
            {"$match": {**query, "status": "converted"}},
            {"$group": {
                "_id": "$source",
                "count": {"$sum": 1},
                "total_value": {"$sum": "$conversion_value"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        return await self.leads_collection.aggregate(pipeline).to_list(5)
    
    async def _get_lead_recent_activities(self, query: Dict) -> List[Dict[str, Any]]:
        """Get recent lead activities"""
        # This would need to be implemented based on your activity tracking
        return []
    
    async def _get_agent_performance(self, team_id: str, start_date: date, end_date: date) -> List[AgentPerformance]:
        """Get agent performance metrics"""
        # This would need to be implemented based on your performance tracking
        return []
    
    async def _get_team_recent_activity(self, team_id: str) -> List[Dict[str, Any]]:
        """Get team recent activity"""
        # This would need to be implemented based on your activity tracking
        return []