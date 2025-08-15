"""Facebook webhook service for handling comment events."""
import hmac
import hashlib
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException
from models.lead import Lead, FacebookComment, LeadSource, LeadStatus
from repositories.lead_repository import LeadRepository
from repositories.agent_repository import AgentRepository
from services.facebook_client import FacebookClient
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class FacebookWebhookService:
    """Service for processing Facebook webhook events."""
    
    def __init__(self):
        self.lead_repo = LeadRepository()
        self.agent_repo = AgentRepository()
        self.facebook_client = FacebookClient()
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Facebook webhook signature."""
        if not settings.FACEBOOK_WEBHOOK_SECRET:
            logger.warning("No webhook secret configured")
            return True  # Allow in development
        
        expected_signature = hmac.new(
            settings.FACEBOOK_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        signature = signature.replace('sha256=', '')
        return hmac.compare_digest(signature, expected_signature)
    
    async def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Facebook webhook event."""
        try:
            results = []
            
            if event_data.get("object") == "page":
                for entry in event_data.get("entry", []):
                    page_id = entry.get("id")
                    
                    # Process comment events
                    for change in entry.get("changes", []):
                        if change.get("field") == "feed" and change.get("value", {}).get("verb") == "add":
                            if "comment_id" in change.get("value", {}):
                                result = await self._process_comment_event(page_id, change["value"])
                                results.append(result)
            
            return {"processed": len(results), "results": results}
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing event: {str(e)}")
    
    async def _process_comment_event(self, page_id: str, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single comment event."""
        try:
            # Find agent who owns this page
            agent = await self.agent_repo.find_agent_by_facebook_page(page_id)
            if not agent:
                logger.warning(f"No agent found for page {page_id}")
                return {"status": "skipped", "reason": "no_agent_found"}
            
            # Extract comment information
            comment = FacebookComment(
                comment_id=comment_data.get("comment_id"),
                post_id=comment_data.get("post_id"),
                user_id=comment_data.get("from", {}).get("id"),
                user_name=comment_data.get("from", {}).get("name", "Unknown User"),
                message=comment_data.get("message", ""),
                created_time=datetime.fromisoformat(
                    comment_data.get("created_time", datetime.utcnow().isoformat())
                ),
                parent_id=comment_data.get("parent_id")
            )
            
            # Skip if it's a reply to another comment (optional)
            if comment.parent_id:
                logger.info(f"Skipping reply comment {comment.comment_id}")
                return {"status": "skipped", "reason": "is_reply"}
            
            # Check if this user is already a lead
            existing_lead = await self.lead_repo.find_lead_by_facebook_id(
                agent.agent_id, comment.user_id
            )
            
            if not existing_lead:
                # Create new lead
                lead = Lead(
                    lead_id=str(uuid.uuid4()),
                    agent_id=agent.agent_id,
                    name=comment.user_name,
                    facebook_id=comment.user_id,
                    source=LeadSource.FACEBOOK_COMMENT,
                    status=LeadStatus.NEW,
                    initial_message=comment.message,
                    created_at=datetime.utcnow(),
                    metadata={
                        "comment_id": comment.comment_id,
                        "post_id": comment.post_id
                    }
                )
                
                await self.lead_repo.create_lead(lead)
                logger.info(f"Created new lead {lead.lead_id} from comment")
            else:
                # Update existing lead
                existing_lead.last_contact = datetime.utcnow()
                existing_lead.metadata = existing_lead.metadata or {}
                existing_lead.metadata[f"comment_{comment.comment_id}"] = {
                    "message": comment.message,
                    "post_id": comment.post_id,
                    "created_time": comment.created_time.isoformat()
                }
                
                await self.lead_repo.update_lead(existing_lead)
                logger.info(f"Updated existing lead {existing_lead.lead_id}")
            
            # Find matching auto-responses
            matching_responses = await self.lead_repo.find_matching_responses(
                agent.agent_id, comment.message
            )
            
            if matching_responses:
                # Use the first matching response
                response = matching_responses[0]
                
                # Send DM to the user
                dm_result = await self._send_direct_message(
                    agent, comment.user_id, response.response_message
                )
                
                if dm_result.get("success"):
                    # Increment usage count
                    await self.lead_repo.increment_response_usage(response.response_id)
                    
                    logger.info(f"Sent auto-response to {comment.user_name}")
                    return {
                        "status": "responded", 
                        "lead_id": existing_lead.lead_id if existing_lead else lead.lead_id,
                        "response_id": response.response_id,
                        "message_sent": True
                    }
                else:
                    return {
                        "status": "lead_created", 
                        "lead_id": existing_lead.lead_id if existing_lead else lead.lead_id,
                        "message_sent": False,
                        "error": dm_result.get("error")
                    }
            else:
                logger.info(f"No matching auto-response for comment: {comment.message}")
                return {
                    "status": "lead_created", 
                    "lead_id": existing_lead.lead_id if existing_lead else lead.lead_id,
                    "message_sent": False,
                    "reason": "no_matching_response"
                }
        
        except Exception as e:
            logger.error(f"Error processing comment event: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _send_direct_message(self, agent, user_id: str, message: str) -> Dict[str, Any]:
        """Send a direct message to a Facebook user."""
        try:
            # Get agent's Facebook access token
            facebook_page = next(
                (page for page in agent.facebook_pages if page.is_connected), None
            )
            
            if not facebook_page:
                return {"success": False, "error": "No connected Facebook page"}
            
            # Send message using Facebook Messenger API
            # Note: This requires additional permissions and page setup
            result = await self.facebook_client.send_private_message(
                facebook_page.access_token,
                facebook_page.page_id,
                user_id,
                message
            )
            
            return {"success": True, "message_id": result.get("message_id")}
            
        except Exception as e:
            logger.error(f"Error sending DM: {str(e)}")
            return {"success": False, "error": str(e)}
