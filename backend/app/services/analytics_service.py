"""
Analytics Service
================
Service for tracking and analyzing post performance metrics
with real-time data collection and reporting.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class AnalyticsService(BaseService):
    """
    Service for analytics and performance tracking.
    """
    
    def __init__(self):
        super().__init__("analytics")
        logger.info("Initialized AnalyticsService")
    
    async def track_post_engagement(self, 
                                  post_id: str, 
                                  platform: str, 
                                  metrics: Dict[str, Any],
                                  user_id: str) -> bool:
        """
        Track post engagement metrics.
        
        Args:
            post_id (str): Post ID
            platform (str): Platform name (facebook, instagram, etc.)
            metrics (Dict[str, Any]): Engagement metrics
            user_id (str): User ID who owns the post
            
        Returns:
            bool: True if tracking successful
        """
        try:
            logger.info(f"Tracking engagement for post {post_id} on {platform}")
            
            # Prepare analytics data
            analytics_data = {
                "post_id": post_id,
                "platform": platform,
                "user_id": user_id,
                "metrics": metrics,
                "timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Store in database
            await self.create(analytics_data)
            
            logger.debug(f"Successfully tracked engagement for post {post_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track engagement for post {post_id}: {e}")
            return False
    
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a post.
        
        Args:
            post_id (str): Post ID
            
        Returns:
            Dict[str, Any]: Analytics data
        """
        try:
            logger.info(f"Getting analytics for post {post_id}")
            
            # Get analytics from database
            filter_dict = {"post_id": post_id}
            analytics_records = await self.get_all(filter_dict=filter_dict)
            
            # Process analytics data
            platform_metrics = {}
            total_metrics = {
                "views": 0,
                "likes": 0,
                "shares": 0,
                "comments": 0,
                "clicks": 0
            }
            
            for record in analytics_records:
                platform = record["platform"]
                metrics = record["metrics"]
                
                if platform not in platform_metrics:
                    platform_metrics[platform] = {
                        "views": 0,
                        "likes": 0,
                        "shares": 0,
                        "comments": 0,
                        "clicks": 0
                    }
                
                # Aggregate platform metrics
                for metric_name, value in metrics.items():
                    if metric_name in platform_metrics[platform]:
                        platform_metrics[platform][metric_name] += value
                        total_metrics[metric_name] += value
            
            analytics = {
                "post_id": post_id,
                "total_metrics": total_metrics,
                "platform_metrics": platform_metrics,
                "last_updated": datetime.utcnow().isoformat(),
                "total_records": len(analytics_records)
            }
            
            logger.debug(f"Retrieved analytics for post {post_id}")
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get analytics for post {post_id}: {e}")
            raise Exception(f"Failed to get post analytics: {str(e)}")
    
    async def get_user_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics for a user's posts.
        
        Args:
            user_id (str): User ID
            days (int): Number of days to analyze
            
        Returns:
            Dict[str, Any]: User analytics data
        """
        try:
            logger.info(f"Getting analytics for user {user_id} for {days} days")
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get analytics records for user
            filter_dict = {
                "user_id": user_id,
                "timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            analytics_records = await self.get_all(filter_dict=filter_dict)
            
            # Process user analytics
            total_posts = len(set(record["post_id"] for record in analytics_records))
            total_metrics = {
                "views": 0,
                "likes": 0,
                "shares": 0,
                "comments": 0,
                "clicks": 0
            }
            
            platform_breakdown = {}
            
            for record in analytics_records:
                platform = record["platform"]
                metrics = record["metrics"]
                
                # Initialize platform breakdown
                if platform not in platform_breakdown:
                    platform_breakdown[platform] = {
                        "views": 0,
                        "likes": 0,
                        "shares": 0,
                        "comments": 0,
                        "clicks": 0,
                        "posts": 0
                    }
                
                # Aggregate metrics
                for metric_name, value in metrics.items():
                    if metric_name in total_metrics:
                        total_metrics[metric_name] += value
                        platform_breakdown[platform][metric_name] += value
                
                platform_breakdown[platform]["posts"] += 1
            
            # Calculate engagement rate
            total_engagement = total_metrics["likes"] + total_metrics["shares"] + total_metrics["comments"]
            engagement_rate = (total_engagement / total_metrics["views"]) * 100 if total_metrics["views"] > 0 else 0
            
            user_analytics = {
                "user_id": user_id,
                "period_days": days,
                "total_posts": total_posts,
                "total_metrics": total_metrics,
                "platform_breakdown": platform_breakdown,
                "engagement_rate": round(engagement_rate, 2),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Retrieved analytics for user {user_id}")
            return user_analytics
            
        except Exception as e:
            logger.error(f"Failed to get user analytics for {user_id}: {e}")
            raise Exception(f"Failed to get user analytics: {str(e)}")
    
    async def get_dashboard_metrics(self, user_id: str) -> Dict[str, Any]:
        """
        Get dashboard-level metrics for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            Dict[str, Any]: Dashboard metrics
        """
        try:
            logger.info(f"Getting dashboard metrics for user {user_id}")
            
            # Get 30-day analytics
            user_analytics = await self.get_user_analytics(user_id, days=30)
            
            dashboard_metrics = {
                "user_id": user_id,
                "overview": {
                    "total_posts": user_analytics["total_posts"],
                    "total_views": user_analytics["total_metrics"]["views"],
                    "total_likes": user_analytics["total_metrics"]["likes"],
                    "total_shares": user_analytics["total_metrics"]["shares"],
                    "total_comments": user_analytics["total_metrics"]["comments"],
                    "engagement_rate": user_analytics["engagement_rate"]
                },
                "platform_breakdown": user_analytics["platform_breakdown"],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Retrieved dashboard metrics for user {user_id}")
            return dashboard_metrics
            
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics for user {user_id}: {e}")
            raise Exception(f"Failed to get dashboard metrics: {str(e)}")