"""
Analytics Data Service
=====================
Service for managing analytics data and metrics
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.schemas.analytics_data import (
    AnalyticsData, AnalyticsDataCreate, AnalyticsDataUpdate,
    AnalyticsSummary, AnalyticsChartData, AnalyticsDataResponse
)
from app.core.exceptions import AnalyticsDataNotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class AnalyticsDataService:
    """Service for analytics data operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.analytics_data
        self.logger = logging.getLogger(__name__)
    
    async def get_analytics_data(
        self,
        property_id: Optional[str] = None,
        content_id: Optional[str] = None,
        metric_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 1000,
        skip: int = 0
    ) -> List[AnalyticsDataResponse]:
        """Get analytics data with optional filtering"""
        try:
            # Build filter
            filter_dict = {}
            if property_id:
                filter_dict["property_id"] = property_id
            if content_id:
                filter_dict["content_id"] = content_id
            if metric_type:
                filter_dict["metric_type"] = metric_type
            if user_id:
                filter_dict["user_id"] = user_id
            
            # Add date range filter
            if date_from or date_to:
                date_filter = {}
                if date_from:
                    date_filter["$gte"] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                if date_to:
                    date_filter["$lte"] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                filter_dict["date"] = date_filter
            
            # Query database
            cursor = self.collection.find(filter_dict).skip(skip).limit(limit).sort("date", -1)
            analytics_data = []
            
            async for doc in cursor:
                analytics_data.append(AnalyticsDataResponse(**doc))
            
            self.logger.info(f"Retrieved {len(analytics_data)} analytics data points")
            return analytics_data
            
        except Exception as e:
            self.logger.error(f"Error getting analytics data: {e}")
            raise DatabaseError(f"Failed to get analytics data: {e}")
    
    async def get_analytics_data_by_id(self, data_id: str) -> AnalyticsDataResponse:
        """Get a specific analytics data point by ID"""
        try:
            doc = await self.collection.find_one({"data_id": data_id})
            if not doc:
                raise AnalyticsDataNotFoundError(f"Analytics data with ID {data_id} not found")
            
            return AnalyticsDataResponse(**doc)
            
        except AnalyticsDataNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting analytics data {data_id}: {e}")
            raise DatabaseError(f"Failed to get analytics data: {e}")
    
    async def create_analytics_data(self, data: AnalyticsDataCreate, user_id: str) -> AnalyticsDataResponse:
        """Create new analytics data"""
        try:
            # Generate unique data ID
            data_id = f"analytics_{ObjectId()}"
            
            # Create document
            doc = {
                "_id": ObjectId(),
                "data_id": data_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                **data.model_dump()
            }
            
            # Insert into database
            result = await self.collection.insert_one(doc)
            if not result.inserted_id:
                raise DatabaseError("Failed to insert analytics data")
            
            self.logger.info(f"Created analytics data: {data_id}")
            return AnalyticsDataResponse(**doc)
            
        except Exception as e:
            self.logger.error(f"Error creating analytics data: {e}")
            raise DatabaseError(f"Failed to create analytics data: {e}")
    
    async def update_analytics_data(self, data_id: str, data: AnalyticsDataUpdate) -> AnalyticsDataResponse:
        """Update analytics data"""
        try:
            # Check if data exists
            existing = await self.collection.find_one({"data_id": data_id})
            if not existing:
                raise AnalyticsDataNotFoundError(f"Analytics data with ID {data_id} not found")
            
            # Prepare update data
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            # Update document
            result = await self.collection.update_one(
                {"data_id": data_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise DatabaseError("Failed to update analytics data")
            
            # Get updated document
            updated_doc = await self.collection.find_one({"data_id": data_id})
            self.logger.info(f"Updated analytics data: {data_id}")
            return AnalyticsDataResponse(**updated_doc)
            
        except AnalyticsDataNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating analytics data {data_id}: {e}")
            raise DatabaseError(f"Failed to update analytics data: {e}")
    
    async def delete_analytics_data(self, data_id: str) -> bool:
        """Delete analytics data"""
        try:
            # Check if data exists
            existing = await self.collection.find_one({"data_id": data_id})
            if not existing:
                raise AnalyticsDataNotFoundError(f"Analytics data with ID {data_id} not found")
            
            # Delete document
            result = await self.collection.delete_one({"data_id": data_id})
            
            if result.deleted_count == 0:
                raise DatabaseError("Failed to delete analytics data")
            
            self.logger.info(f"Deleted analytics data: {data_id}")
            return True
            
        except AnalyticsDataNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting analytics data {data_id}: {e}")
            raise DatabaseError(f"Failed to delete analytics data: {e}")
    
    async def get_analytics_summary(
        self,
        property_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AnalyticsSummary:
        """Get analytics summary"""
        try:
            # Build filter
            filter_dict = {}
            if property_id:
                filter_dict["property_id"] = property_id
            if user_id:
                filter_dict["user_id"] = user_id
            
            # Add date range filter
            if date_from or date_to:
                date_filter = {}
                if date_from:
                    date_filter["$gte"] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                if date_to:
                    date_filter["$lte"] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                filter_dict["date"] = date_filter
            
            # Get total metrics
            total_views = await self.collection.count_documents({**filter_dict, "metric_type": "views"})
            total_clicks = await self.collection.count_documents({**filter_dict, "metric_type": "clicks"})
            total_engagement = await self.collection.count_documents({**filter_dict, "metric_type": "engagement"})
            total_leads = await self.collection.count_documents({**filter_dict, "metric_type": "leads"})
            
            # Get total revenue
            revenue_pipeline = [
                {"$match": {**filter_dict, "metric_type": "revenue"}},
                {"$group": {"_id": None, "total": {"$sum": "$value"}}}
            ]
            revenue_result = await self.collection.aggregate(revenue_pipeline).to_list(1)
            total_revenue = revenue_result[0]["total"] if revenue_result else 0.0
            
            # Get top performing content
            top_content_pipeline = [
                {"$match": filter_dict},
                {"$group": {"_id": "$content_id", "total_views": {"$sum": {"$cond": [{"$eq": ["$metric_type", "views"]}, "$value", 0]}}}},
                {"$sort": {"total_views": -1}},
                {"$limit": 5}
            ]
            top_performing_content = []
            async for doc in self.collection.aggregate(top_content_pipeline):
                top_performing_content.append({
                    "content_id": doc["_id"],
                    "total_views": doc["total_views"]
                })
            
            # Get channel performance
            channel_pipeline = [
                {"$match": filter_dict},
                {"$group": {
                    "_id": "$channel",
                    "views": {"$sum": {"$cond": [{"$eq": ["$metric_type", "views"]}, "$value", 0]}},
                    "clicks": {"$sum": {"$cond": [{"$eq": ["$metric_type", "clicks"]}, "$value", 0]}},
                    "engagement": {"$sum": {"$cond": [{"$eq": ["$metric_type", "engagement"]}, "$value", 0]}}
                }}
            ]
            channel_performance = {}
            async for doc in self.collection.aggregate(channel_pipeline):
                channel_performance[doc["_id"]] = {
                    "views": doc["views"],
                    "clicks": doc["clicks"],
                    "engagement": doc["engagement"]
                }
            
            # Get date range
            date_range = {}
            if date_from:
                date_range["from"] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            if date_to:
                date_range["to"] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            
            # Calculate growth metrics (simplified)
            growth_metrics = {
                "views_growth": 0.0,
                "clicks_growth": 0.0,
                "engagement_growth": 0.0,
                "leads_growth": 0.0
            }
            
            return AnalyticsSummary(
                total_views=total_views,
                total_clicks=total_clicks,
                total_engagement=total_engagement,
                total_leads=total_leads,
                total_revenue=total_revenue,
                top_performing_content=top_performing_content,
                channel_performance=channel_performance,
                date_range=date_range,
                growth_metrics=growth_metrics
            )
            
        except Exception as e:
            self.logger.error(f"Error getting analytics summary: {e}")
            raise DatabaseError(f"Failed to get analytics summary: {e}")
    
    async def get_chart_data(
        self,
        property_id: Optional[str] = None,
        metric_type: str = "views",
        period: str = "7d",
        user_id: Optional[str] = None
    ) -> AnalyticsChartData:
        """Get chart data for analytics visualization"""
        try:
            # Build filter
            filter_dict = {"metric_type": metric_type}
            if property_id:
                filter_dict["property_id"] = property_id
            if user_id:
                filter_dict["user_id"] = user_id
            
            # Calculate date range based on period
            end_date = datetime.now(timezone.utc)
            if period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            elif period == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=7)
            
            filter_dict["date"] = {"$gte": start_date, "$lte": end_date}
            
            # Aggregate data by date
            pipeline = [
                {"$match": filter_dict},
                {"$group": {
                    "_id": {
                        "year": {"$year": "$date"},
                        "month": {"$month": "$date"},
                        "day": {"$dayOfMonth": "$date"}
                    },
                    "value": {"$sum": "$value"}
                }},
                {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
            ]
            
            labels = []
            values = []
            total = 0.0
            
            async for doc in self.collection.aggregate(pipeline):
                date_str = f"{doc['_id']['year']}-{doc['_id']['month']:02d}-{doc['_id']['day']:02d}"
                labels.append(date_str)
                values.append(doc["value"])
                total += doc["value"]
            
            datasets = [{
                "label": metric_type.title(),
                "data": values,
                "borderColor": "rgb(75, 192, 192)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)"
            }]
            
            return AnalyticsChartData(
                labels=labels,
                datasets=datasets,
                total=total,
                period=period
            )
            
        except Exception as e:
            self.logger.error(f"Error getting chart data: {e}")
            raise DatabaseError(f"Failed to get chart data: {e}")
