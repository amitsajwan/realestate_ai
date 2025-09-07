from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
import logging

from app.core.database import get_database

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking and managing analytics data"""
    
    def __init__(self):
        self.db = get_database()
        self.views_collection = self.db.property_views
        self.inquiries_collection = self.db.property_inquiries
        self.shares_collection = self.db.property_shares
        self.favorites_collection = self.db.property_favorites
    
    async def track_property_view(
        self,
        property_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track a property view"""
        try:
            view_data = {
                "property_id": property_id,
                "user_id": user_id,
                "session_id": session_id,
                "viewed_at": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            await self.views_collection.insert_one(view_data)
            logger.info(f"Tracked view for property {property_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to track property view: {e}")
            return False
    
    async def track_property_inquiry(
        self,
        property_id: str,
        user_id: str,
        inquiry_type: str = "general",
        message: Optional[str] = None
    ) -> bool:
        """Track a property inquiry"""
        try:
            inquiry_data = {
                "property_id": property_id,
                "user_id": user_id,
                "inquiry_type": inquiry_type,
                "message": message,
                "created_at": datetime.utcnow()
            }
            
            await self.inquiries_collection.insert_one(inquiry_data)
            logger.info(f"Tracked inquiry for property {property_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to track property inquiry: {e}")
            return False
    
    async def track_property_share(
        self,
        property_id: str,
        user_id: str,
        platform: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track a property share"""
        try:
            share_data = {
                "property_id": property_id,
                "user_id": user_id,
                "platform": platform,
                "shared_at": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            await self.shares_collection.insert_one(share_data)
            logger.info(f"Tracked share for property {property_id} on {platform}")
            return True
        except Exception as e:
            logger.error(f"Failed to track property share: {e}")
            return False
    
    async def toggle_property_favorite(
        self,
        property_id: str,
        user_id: str
    ) -> bool:
        """Toggle property favorite status"""
        try:
            existing = await self.favorites_collection.find_one({
                "property_id": property_id,
                "user_id": user_id
            })
            
            if existing:
                # Remove favorite
                await self.favorites_collection.delete_one({
                    "_id": existing["_id"]
                })
                logger.info(f"Removed favorite for property {property_id}")
                return False
            else:
                # Add favorite
                await self.favorites_collection.insert_one({
                    "property_id": property_id,
                    "user_id": user_id,
                    "favorited_at": datetime.utcnow()
                })
                logger.info(f"Added favorite for property {property_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to toggle property favorite: {e}")
            return False
    
    async def get_property_analytics(
        self,
        property_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for a specific property"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get counts
            views_count = await self.views_collection.count_documents({
                "property_id": property_id,
                "viewed_at": {"$gte": since_date}
            })
            
            inquiries_count = await self.inquiries_collection.count_documents({
                "property_id": property_id,
                "created_at": {"$gte": since_date}
            })
            
            shares_count = await self.shares_collection.count_documents({
                "property_id": property_id,
                "shared_at": {"$gte": since_date}
            })
            
            favorites_count = await self.favorites_collection.count_documents({
                "property_id": property_id
            })
            
            # Get daily trends
            daily_views = await self._get_daily_trend(
                self.views_collection,
                "property_id",
                property_id,
                "viewed_at",
                days
            )
            
            return {
                "property_id": property_id,
                "period_days": days,
                "metrics": {
                    "views": views_count,
                    "inquiries": inquiries_count,
                    "shares": shares_count,
                    "favorites": favorites_count
                },
                "trends": {
                    "daily_views": daily_views
                },
                "engagement_rate": self._calculate_engagement_rate(
                    views_count, inquiries_count, shares_count, favorites_count
                )
            }
        except Exception as e:
            logger.error(f"Failed to get property analytics: {e}")
            return {
                "property_id": property_id,
                "error": str(e),
                "metrics": {
                    "views": 0,
                    "inquiries": 0,
                    "shares": 0,
                    "favorites": 0
                }
            }
    
    async def get_user_analytics(
        self,
        user_id: str,
        property_ids: List[str],
        days: int = 30
    ) -> Dict[str, Any]:
        """Get aggregated analytics for multiple properties"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Aggregate metrics
            total_views = await self.views_collection.count_documents({
                "property_id": {"$in": property_ids},
                "viewed_at": {"$gte": since_date}
            })
            
            total_inquiries = await self.inquiries_collection.count_documents({
                "property_id": {"$in": property_ids},
                "created_at": {"$gte": since_date}
            })
            
            total_shares = await self.shares_collection.count_documents({
                "property_id": {"$in": property_ids},
                "shared_at": {"$gte": since_date}
            })
            
            total_favorites = await self.favorites_collection.count_documents({
                "property_id": {"$in": property_ids}
            })
            
            # Get top performing properties
            top_properties = await self._get_top_properties(property_ids, since_date)
            
            return {
                "user_id": user_id,
                "period_days": days,
                "total_properties": len(property_ids),
                "aggregate_metrics": {
                    "total_views": total_views,
                    "total_inquiries": total_inquiries,
                    "total_shares": total_shares,
                    "total_favorites": total_favorites
                },
                "average_metrics": {
                    "avg_views_per_property": total_views / len(property_ids) if property_ids else 0,
                    "avg_inquiries_per_property": total_inquiries / len(property_ids) if property_ids else 0,
                    "avg_engagement_rate": self._calculate_engagement_rate(
                        total_views, total_inquiries, total_shares, total_favorites
                    )
                },
                "top_properties": top_properties
            }
        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            return {
                "user_id": user_id,
                "error": str(e),
                "aggregate_metrics": {}
            }
    
    async def _get_daily_trend(
        self,
        collection: AsyncIOMotorCollection,
        field_name: str,
        field_value: str,
        date_field: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """Get daily trend data"""
        pipeline = [
            {
                "$match": {
                    field_name: field_value,
                    date_field: {"$gte": datetime.utcnow() - timedelta(days=days)}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": f"${date_field}"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        return [{"date": r["_id"], "count": r["count"]} for r in results]
    
    async def _get_top_properties(
        self,
        property_ids: List[str],
        since_date: datetime,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get top performing properties by views"""
        pipeline = [
            {
                "$match": {
                    "property_id": {"$in": property_ids},
                    "viewed_at": {"$gte": since_date}
                }
            },
            {
                "$group": {
                    "_id": "$property_id",
                    "views": {"$sum": 1}
                }
            },
            {"$sort": {"views": -1}},
            {"$limit": limit}
        ]
        
        cursor = self.views_collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        return [
            {"property_id": r["_id"], "views": r["views"]}
            for r in results
        ]
    
    def _calculate_engagement_rate(
        self,
        views: int,
        inquiries: int,
        shares: int,
        favorites: int
    ) -> float:
        """Calculate engagement rate"""
        if views == 0:
            return 0.0
        
        engagements = inquiries + shares + favorites
        return round((engagements / views) * 100, 2)


# Global instance
analytics_service = AnalyticsService()