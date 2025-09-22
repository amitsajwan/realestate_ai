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
    
    async def get_top_performing_posts(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing posts for a user.
        
        Args:
            user_id (str): User ID
            limit (int): Number of posts to return
            
        Returns:
            List[Dict[str, Any]]: Top performing posts
        """
        try:
            logger.info(f"Getting top performing posts for user {user_id}")
            
            # Get all analytics for the user
            analytics_records = await self.get_all(
                {"user_id": user_id}
            )
            
            if not analytics_records:
                return []
            
            # Calculate performance score for each post
            post_scores = {}
            for record in analytics_records:
                post_id = record.get("post_id")
                if not post_id:
                    continue
                    
                if post_id not in post_scores:
                    post_scores[post_id] = {
                        "post_id": post_id,
                        "total_views": 0,
                        "total_likes": 0,
                        "total_shares": 0,
                        "total_comments": 0,
                        "platforms": set()
                    }
                
                metrics = record.get("metrics", {})
                post_scores[post_id]["total_views"] += metrics.get("views", 0)
                post_scores[post_id]["total_likes"] += metrics.get("likes", 0)
                post_scores[post_id]["total_shares"] += metrics.get("shares", 0)
                post_scores[post_id]["total_comments"] += metrics.get("comments", 0)
                post_scores[post_id]["platforms"].add(record.get("platform", "unknown"))
            
            # Calculate performance score (weighted combination)
            top_posts = []
            for post_id, data in post_scores.items():
                performance_score = (
                    data["total_views"] * 0.3 +
                    data["total_likes"] * 0.4 +
                    data["total_shares"] * 0.2 +
                    data["total_comments"] * 0.1
                )
                
                top_posts.append({
                    "post_id": post_id,
                    "performance_score": round(performance_score, 2),
                    "total_views": data["total_views"],
                    "total_likes": data["total_likes"],
                    "total_shares": data["total_shares"],
                    "total_comments": data["total_comments"],
                    "platforms": list(data["platforms"])
                })
            
            # Sort by performance score and return top N
            top_posts.sort(key=lambda x: x["performance_score"], reverse=True)
            
            logger.debug(f"Retrieved top {min(limit, len(top_posts))} performing posts for user {user_id}")
            return top_posts[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get top performing posts for user {user_id}: {e}")
            raise Exception(f"Failed to get top performing posts: {str(e)}")
    
    async def export_analytics(self, user_id: str, format: str = "json", days: int = 30) -> Dict[str, Any]:
        """
        Export analytics data for a user.
        
        Args:
            user_id (str): User ID
            format (str): Export format (json, csv)
            days (int): Number of days to export
            
        Returns:
            Dict[str, Any]: Exported analytics data
        """
        try:
            logger.info(f"Exporting analytics for user {user_id} in {format} format")
            
            # Get comprehensive analytics data
            user_analytics = await self.get_user_analytics(user_id, days=days)
            dashboard_metrics = await self.get_dashboard_metrics(user_id)
            top_posts = await self.get_top_performing_posts(user_id, limit=10)
            
            # Combine all data
            combined_data = {
                "user_analytics": user_analytics,
                "dashboard_metrics": dashboard_metrics,
                "top_posts": top_posts
            }
            
            if format.lower() == "csv":
                # Convert to CSV format
                csv_data = self._convert_to_csv(user_analytics)
                return {
                    "user_id": user_id,
                    "format": "csv",
                    "data": csv_data,
                    "exported_at": datetime.utcnow().isoformat()
                }
            else:
                # Return as JSON
                return {
                    "user_id": user_id,
                    "format": "json",
                    "data": combined_data,
                    "exported_at": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Failed to export analytics for user {user_id}: {e}")
            raise Exception(f"Failed to export analytics: {str(e)}")
    
    def _convert_to_csv(self, analytics_data: Dict[str, Any]) -> str:
        """Convert analytics data to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Metric", "Value", "Platform", "Date"
        ])
        
        # Write data
        for platform, data in analytics_data.get("platform_breakdown", {}).items():
            for metric, value in data.items():
                writer.writerow([
                    metric,
                    value,
                    platform,
                    analytics_data.get("generated_at", "")
                ])
        
        return output.getvalue()


# Create a singleton instance (lazy initialization)
analytics_service = None

def get_analytics_service():
    global analytics_service
    if analytics_service is None:
        analytics_service = AnalyticsService()
    return analytics_service