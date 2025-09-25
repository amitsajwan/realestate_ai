"""
Token Cleanup Service
=====================
Automated token lifecycle management and cleanup
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from app.repositories.token_repository import TokenRepository
from app.core.database import get_database

logger = logging.getLogger(__name__)

class TokenCleanupService:
    """Service for automated token cleanup and lifecycle management"""
    
    def __init__(self):
        self.token_repo: TokenRepository = None
        self.is_running = False
        self.cleanup_interval = 3600  # 1 hour in seconds
        self.cleanup_task = None
    
    async def initialize(self):
        """Initialize the cleanup service"""
        try:
            db = get_database()
            if db is None:
                logger.error("Database not available for token cleanup service")
                return False
            
            self.token_repo = TokenRepository(db)
            logger.info("Token cleanup service initialized")
            return True
        except Exception as e:
            logger.error(f"Error initializing token cleanup service: {e}")
            return False
    
    async def start_cleanup_scheduler(self):
        """Start the automated cleanup scheduler"""
        if self.is_running:
            logger.warning("Token cleanup scheduler is already running")
            return
        
        if not self.token_repo:
            if not await self.initialize():
                logger.error("Failed to initialize token cleanup service")
                return
        
        self.is_running = True
        logger.info("Starting token cleanup scheduler")
        
        # Start the cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_scheduler(self):
        """Stop the automated cleanup scheduler"""
        if not self.is_running:
            logger.warning("Token cleanup scheduler is not running")
            return
        
        self.is_running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                logger.info("Token cleanup scheduler stopped")
        
        logger.info("Token cleanup scheduler stopped")
    
    async def _cleanup_loop(self):
        """Main cleanup loop"""
        while self.is_running:
            try:
                await self.perform_cleanup()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in token cleanup loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def perform_cleanup(self) -> Dict[str, Any]:
        """Perform comprehensive token cleanup"""
        if not self.token_repo:
            logger.error("Token repository not initialized")
            return {"error": "Repository not initialized"}
        
        try:
            logger.info("Starting token cleanup process")
            cleanup_stats = {}
            
            # Clean up expired tokens
            expired_count = await self.token_repo.cleanup_expired_tokens()
            cleanup_stats["expired_tokens_cleaned"] = expired_count
            
            # Clean up old inactive tokens (older than 30 days)
            old_count = await self.token_repo.cleanup_old_tokens(days_old=30)
            cleanup_stats["old_tokens_cleaned"] = old_count
            
            # Get current token statistics
            token_stats = await self.token_repo.get_token_stats()
            cleanup_stats["current_stats"] = token_stats
            
            logger.info(f"Token cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error performing token cleanup: {e}")
            return {"error": str(e)}
    
    async def cleanup_user_tokens(self, user_id: str) -> Dict[str, Any]:
        """Clean up all tokens for a specific user"""
        if not self.token_repo:
            logger.error("Token repository not initialized")
            return {"error": "Repository not initialized"}
        
        try:
            # Get user's active tokens before cleanup
            user_tokens = await self.token_repo.find_user_tokens(user_id)
            active_count = len([t for t in user_tokens if t.get("is_active", False)])
            
            # Revoke all user tokens
            revoked_count = await self.token_repo.revoke_user_tokens(user_id)
            
            logger.info(f"Cleaned up {revoked_count} tokens for user {user_id}")
            
            return {
                "user_id": user_id,
                "active_tokens_before": active_count,
                "tokens_revoked": revoked_count
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up tokens for user {user_id}: {e}")
            return {"error": str(e)}
    
    async def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup service statistics"""
        if not self.token_repo:
            return {"error": "Repository not initialized"}
        
        try:
            stats = await self.token_repo.get_token_stats()
            stats.update({
                "service_running": self.is_running,
                "cleanup_interval_seconds": self.cleanup_interval,
                "last_cleanup": datetime.utcnow().isoformat()
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cleanup stats: {e}")
            return {"error": str(e)}
    
    async def force_cleanup(self) -> Dict[str, Any]:
        """Force an immediate cleanup (useful for testing or manual triggers)"""
        logger.info("Forcing immediate token cleanup")
        return await self.perform_cleanup()
    
    async def update_cleanup_interval(self, new_interval: int):
        """Update the cleanup interval"""
        if new_interval < 60:  # Minimum 1 minute
            logger.warning("Cleanup interval too short, using minimum of 60 seconds")
            new_interval = 60
        
        self.cleanup_interval = new_interval
        logger.info(f"Token cleanup interval updated to {new_interval} seconds")

# Global instance
token_cleanup_service = TokenCleanupService()

async def start_token_cleanup():
    """Start the global token cleanup service"""
    await token_cleanup_service.start_cleanup_scheduler()

async def stop_token_cleanup():
    """Stop the global token cleanup service"""
    await token_cleanup_service.stop_cleanup_scheduler()
