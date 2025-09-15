"""
Multi-Channel Publishing Service
===============================
Service for publishing posts to multiple social media platforms
including Facebook, Instagram, LinkedIn, and Twitter.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from app.services.facebook_service import FacebookService
from app.services.instagram_service import InstagramService
from app.services.linkedin_service import LinkedInService
from app.services.twitter_service import TwitterService

logger = logging.getLogger(__name__)


class MultiChannelPublishingService:
    """
    Service for publishing posts to multiple social media channels.
    """
    
    def __init__(self):
        self.facebook_service = FacebookService()
        self.instagram_service = InstagramService()
        self.linkedin_service = LinkedInService()
        self.twitter_service = TwitterService()
        
        logger.info("Initialized MultiChannelPublishingService")
    
    async def publish_to_channels(self, 
                                 post_data: Dict[str, Any], 
                                 channels: List[str]) -> Dict[str, Any]:
        """
        Publish post to multiple channels.
        
        Args:
            post_data (Dict[str, Any]): Post content and metadata
            channels (List[str]): List of channels to publish to
            
        Returns:
            Dict[str, Any]: Publishing results for each channel
        """
        try:
            logger.info(f"Publishing post to channels: {channels}")
            
            results = {}
            
            for channel in channels:
                try:
                    if channel.lower() == "facebook":
                        result = await self._publish_to_facebook(post_data)
                    elif channel.lower() == "instagram":
                        result = await self._publish_to_instagram(post_data)
                    elif channel.lower() == "linkedin":
                        result = await self._publish_to_linkedin(post_data)
                    elif channel.lower() == "twitter":
                        result = await self._publish_to_twitter(post_data)
                    else:
                        result = {
                            "status": "error",
                            "error": f"Unsupported channel: {channel}"
                        }
                    
                    results[channel] = result
                    
                except Exception as e:
                    logger.error(f"Failed to publish to {channel}: {e}")
                    results[channel] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Log overall results
            successful_channels = [ch for ch, result in results.items() 
                                 if result.get("status") == "success"]
            failed_channels = [ch for ch, result in results.items() 
                             if result.get("status") == "error"]
            
            logger.info(f"Publishing completed. Success: {successful_channels}, Failed: {failed_channels}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to publish to channels: {e}")
            raise Exception(f"Failed to publish to channels: {str(e)}")
    
    async def _publish_to_facebook(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish post to Facebook."""
        try:
            # Prepare Facebook-specific content
            facebook_content = self._prepare_facebook_content(post_data)
            
            # Publish to Facebook
            result = await self.facebook_service.publish_post(facebook_content)
            
            return {
                "status": "success",
                "channel": "facebook",
                "post_id": result.get("post_id"),
                "url": result.get("url"),
                "metrics": result.get("metrics", {}),
                "published_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Facebook publishing failed: {e}")
            return {
                "status": "error",
                "channel": "facebook",
                "error": str(e)
            }
    
    async def _publish_to_instagram(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish post to Instagram."""
        try:
            # Prepare Instagram-specific content
            instagram_content = self._prepare_instagram_content(post_data)
            
            # Publish to Instagram
            result = await self.instagram_service.publish_post(instagram_content)
            
            return {
                "status": "success",
                "channel": "instagram",
                "post_id": result.get("post_id"),
                "url": result.get("url"),
                "metrics": result.get("metrics", {}),
                "published_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Instagram publishing failed: {e}")
            return {
                "status": "error",
                "channel": "instagram",
                "error": str(e)
            }
    
    async def _publish_to_linkedin(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish post to LinkedIn."""
        try:
            # Prepare LinkedIn-specific content
            linkedin_content = self._prepare_linkedin_content(post_data)
            
            # Publish to LinkedIn
            result = await self.linkedin_service.publish_post(linkedin_content)
            
            return {
                "status": "success",
                "channel": "linkedin",
                "post_id": result.get("post_id"),
                "url": result.get("url"),
                "metrics": result.get("metrics", {}),
                "published_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LinkedIn publishing failed: {e}")
            return {
                "status": "error",
                "channel": "linkedin",
                "error": str(e)
            }
    
    async def _publish_to_twitter(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish post to Twitter."""
        try:
            # Prepare Twitter-specific content
            twitter_content = self._prepare_twitter_content(post_data)
            
            # Publish to Twitter
            result = await self.twitter_service.publish_post(twitter_content)
            
            return {
                "status": "success",
                "channel": "twitter",
                "post_id": result.get("post_id"),
                "url": result.get("url"),
                "metrics": result.get("metrics", {}),
                "published_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Twitter publishing failed: {e}")
            return {
                "status": "error",
                "channel": "twitter",
                "error": str(e)
            }
    
    def _prepare_facebook_content(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content optimized for Facebook."""
        content = post_data.get("optimized_content", post_data.get("content", ""))
        
        # Facebook-specific optimizations
        facebook_content = {
            "message": content,
            "property_title": post_data.get("property_title", ""),
            "property_location": post_data.get("property_location", ""),
            "property_price": post_data.get("property_price", ""),
            "language": post_data.get("language", "en"),
            "hashtags": self._generate_hashtags(post_data),
            "call_to_action": "Contact us for more information!",
            "platform": "facebook"
        }
        
        return facebook_content
    
    def _prepare_instagram_content(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content optimized for Instagram."""
        content = post_data.get("optimized_content", post_data.get("content", ""))
        
        # Instagram-specific optimizations
        instagram_content = {
            "caption": content,
            "property_title": post_data.get("property_title", ""),
            "property_location": post_data.get("property_location", ""),
            "property_price": post_data.get("property_price", ""),
            "language": post_data.get("language", "en"),
            "hashtags": self._generate_hashtags(post_data, max_hashtags=30),
            "call_to_action": "DM us for details!",
            "platform": "instagram"
        }
        
        return instagram_content
    
    def _prepare_linkedin_content(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content optimized for LinkedIn."""
        content = post_data.get("optimized_content", post_data.get("content", ""))
        
        # LinkedIn-specific optimizations
        linkedin_content = {
            "text": content,
            "property_title": post_data.get("property_title", ""),
            "property_location": post_data.get("property_location", ""),
            "property_price": post_data.get("property_price", ""),
            "language": post_data.get("language", "en"),
            "hashtags": self._generate_hashtags(post_data, max_hashtags=5),
            "call_to_action": "Connect with us for more information",
            "platform": "linkedin"
        }
        
        return linkedin_content
    
    def _prepare_twitter_content(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare content optimized for Twitter."""
        content = post_data.get("optimized_content", post_data.get("content", ""))
        
        # Twitter-specific optimizations (character limit)
        if len(content) > 280:
            content = content[:277] + "..."
        
        twitter_content = {
            "text": content,
            "property_title": post_data.get("property_title", ""),
            "property_location": post_data.get("property_location", ""),
            "property_price": post_data.get("property_price", ""),
            "language": post_data.get("language", "en"),
            "hashtags": self._generate_hashtags(post_data, max_hashtags=3),
            "call_to_action": "DM for details",
            "platform": "twitter"
        }
        
        return twitter_content
    
    def _generate_hashtags(self, post_data: Dict[str, Any], max_hashtags: int = 10) -> List[str]:
        """Generate relevant hashtags for the post."""
        hashtags = []
        
        # Property type hashtags
        property_type = post_data.get("property_type", "").lower()
        if property_type:
            hashtags.append(f"#{property_type}")
        
        # Location hashtags
        location = post_data.get("property_location", "").lower()
        if location:
            # Extract city/area from location
            location_parts = location.split(",")
            if location_parts:
                city = location_parts[0].strip().replace(" ", "")
                hashtags.append(f"#{city}")
        
        # Price range hashtags
        price = post_data.get("property_price", "")
        if price:
            try:
                # Extract numeric value from price
                price_num = float(''.join(filter(str.isdigit, price)))
                if price_num < 100000:
                    hashtags.append("#affordable")
                elif price_num < 500000:
                    hashtags.append("#midrange")
                else:
                    hashtags.append("#luxury")
            except:
                pass
        
        # General real estate hashtags
        general_hashtags = [
            "#realestate", "#property", "#home", "#house", "#apartment",
            "#investment", "#forsale", "#newlisting", "#realestateagent"
        ]
        
        hashtags.extend(general_hashtags)
        
        # Language-specific hashtags
        language = post_data.get("language", "en")
        if language == "hi":
            hashtags.extend(["#संपत्ति", "#घर", "#निवेश"])
        elif language == "ta":
            hashtags.extend(["#சொத்து", "#வீடு", "#முதலீடு"])
        elif language == "te":
            hashtags.extend(["#ఆస్తి", "#ఇల్లు", "#పెట్టుబడి"])
        
        # Return limited number of hashtags
        return hashtags[:max_hashtags]
    
    async def get_channel_status(self, channel: str) -> Dict[str, Any]:
        """
        Get the status of a specific channel.
        
        Args:
            channel (str): Channel name
            
        Returns:
            Dict[str, Any]: Channel status information
        """
        try:
            if channel.lower() == "facebook":
                return await self.facebook_service.get_status()
            elif channel.lower() == "instagram":
                return await self.instagram_service.get_status()
            elif channel.lower() == "linkedin":
                return await self.linkedin_service.get_status()
            elif channel.lower() == "twitter":
                return await self.twitter_service.get_status()
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported channel: {channel}"
                }
                
        except Exception as e:
            logger.error(f"Failed to get status for channel {channel}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_all_channels_status(self) -> Dict[str, Any]:
        """
        Get status of all available channels.
        
        Returns:
            Dict[str, Any]: Status of all channels
        """
        try:
            channels = ["facebook", "instagram", "linkedin", "twitter"]
            status_results = {}
            
            for channel in channels:
                status_results[channel] = await self.get_channel_status(channel)
            
            return status_results
            
        except Exception as e:
            logger.error(f"Failed to get all channels status: {e}")
            raise Exception(f"Failed to get channels status: {str(e)}")
    
    async def test_publishing(self, channels: List[str]) -> Dict[str, Any]:
        """
        Test publishing to specified channels with a test post.
        
        Args:
            channels (List[str]): Channels to test
            
        Returns:
            Dict[str, Any]: Test results
        """
        try:
            # Create test post data
            test_post_data = {
                "content": "This is a test post for multi-channel publishing.",
                "property_title": "Test Property",
                "property_location": "Test Location",
                "property_price": "Test Price",
                "language": "en"
            }
            
            # Test publishing
            results = await self.publish_to_channels(test_post_data, channels)
            
            return {
                "test_post": test_post_data,
                "results": results,
                "tested_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to test publishing: {e}")
            raise Exception(f"Failed to test publishing: {str(e)}")