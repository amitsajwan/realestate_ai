"""
Token Lifecycle Management Service
=================================
Comprehensive token management with rotation, monitoring, and cleanup
"""

import secrets
import hashlib
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status
import redis.asyncio as redis
import logging

from app.core.config import settings
from app.schemas.token import TokenData, TokenPair, TokenValidationResult, TokenMetadata
from app.schemas.errors import create_token_error, ErrorCodes
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class TokenLifecycleManager:
    """Comprehensive token lifecycle management service"""
    
    def __init__(self, user_repository: UserRepository, redis_client: redis.Redis):
        self.user_repository = user_repository
        self.redis = redis_client
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
        
        # Token rotation settings
        self.enable_token_rotation = True
        self.max_refresh_tokens_per_user = 5
        self.token_cleanup_interval = 3600  # 1 hour
        
        # Start background tasks
        self._cleanup_task = None
        self._monitoring_task = None
    
    async def initialize(self):
        """Initialize the token lifecycle manager"""
        try:
            # Start background cleanup task
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            # Start monitoring task
            self._monitoring_task = asyncio.create_task(self._monitor_token_health())
            
            logger.info("Token Lifecycle Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Token Lifecycle Manager: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the token lifecycle manager"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._monitoring_task:
                self._monitoring_task.cancel()
            
            logger.info("Token Lifecycle Manager shutdown completed")
        except Exception as e:
            logger.error(f"Error during Token Lifecycle Manager shutdown: {e}")
    
    async def create_tokens(self, user_id: str, device_info: str = None, ip_address: str = None) -> TokenPair:
        """Generate access and refresh tokens with proper metadata"""
        try:
            # Generate token fingerprint for tracking
            token_fingerprint = self._generate_token_fingerprint(user_id, device_info, ip_address)
            
            # Create access token
            access_token = await self._create_access_token(user_id, token_fingerprint)
            
            # Create refresh token
            refresh_token = await self._create_refresh_token(user_id, token_fingerprint)
            
            # Calculate expiration times
            access_expires = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            refresh_expires = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
            
            # Store token metadata
            token_metadata = TokenMetadata(
                user_id=user_id,
                token_fingerprint=token_fingerprint,
                device_info=device_info,
                ip_address=ip_address,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                usage_count=1
            )
            
            await self._store_token_metadata(token_metadata)
            
            # Store tokens in repository
            token_data = TokenData(
                access_token=access_token,
                refresh_token=refresh_token,
                access_token_expires=access_expires,
                refresh_token_expires=refresh_expires
            )
            
            await self.user_repository.update_tokens(user_id, token_data)
            
            # Track active refresh tokens for rotation
            if self.enable_token_rotation:
                await self._track_refresh_token(user_id, refresh_token, token_fingerprint)
            
            logger.info(f"Tokens created successfully for user {user_id}")
            
            return TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire_minutes * 60,
                refresh_expires_in=self.refresh_token_expire_days * 24 * 60 * 60
            )
            
        except Exception as e:
            logger.error(f"Error creating tokens for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create tokens"
            )
    
    async def refresh_tokens(self, refresh_token: str, device_info: str = None, ip_address: str = None) -> TokenPair:
        """Refresh tokens with rotation strategy"""
        try:
            # Validate refresh token
            validation_result = await self.validate_token(refresh_token, "refresh")
            if not validation_result.valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=create_token_error(
                        ErrorCodes.TOKEN_EXPIRED,
                        "Refresh token is invalid or expired"
                    ).model_dump()
                )
            
            user_id = validation_result.user_id
            
            # Check if refresh token is in active list (for rotation)
            if self.enable_token_rotation:
                if not await self._is_refresh_token_active(user_id, refresh_token):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=create_token_error(
                            ErrorCodes.TOKEN_REVOKED,
                            "Refresh token has been revoked"
                        ).model_dump()
                    )
            
            # Revoke old refresh token if rotation is enabled
            if self.enable_token_rotation:
                await self._revoke_refresh_token(user_id, refresh_token)
            
            # Create new tokens
            new_tokens = await self.create_tokens(user_id, device_info, ip_address)
            
            logger.info(f"Tokens refreshed successfully for user {user_id}")
            return new_tokens
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing tokens: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refresh tokens"
            )
    
    async def validate_token(self, token: str, token_type: str = "access") -> TokenValidationResult:
        """Validate token and return detailed result"""
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                return TokenValidationResult(
                    valid=False,
                    error_message="Invalid token type"
                )
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                return TokenValidationResult(
                    valid=False,
                    error_message="Token has expired"
                )
            
            # Check if token is blacklisted
            if await self._is_token_blacklisted(token):
                return TokenValidationResult(
                    valid=False,
                    error_message="Token has been revoked"
                )
            
            # Update token usage
            user_id = payload.get("sub")
            token_fingerprint = payload.get("fingerprint")
            if user_id and token_fingerprint:
                await self._update_token_usage(user_id, token_fingerprint)
            
            return TokenValidationResult(
                valid=True,
                user_id=user_id,
                token_type=token_type,
                expires_at=datetime.fromtimestamp(exp) if exp else None
            )
            
        except JWTError as e:
            return TokenValidationResult(
                valid=False,
                error_message=f"Token validation failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return TokenValidationResult(
                valid=False,
                error_message="Token validation error"
            )
    
    async def revoke_all_user_tokens(self, user_id: str, reason: str = "User logout") -> bool:
        """Revoke all tokens for a user"""
        try:
            # Revoke tokens in repository
            await self.user_repository.revoke_tokens(user_id)
            
            # Blacklist all active tokens for this user
            await self._blacklist_user_tokens(user_id)
            
            # Clear refresh token tracking
            if self.enable_token_rotation:
                await self._clear_user_refresh_tokens(user_id)
            
            # Log security event
            logger.warning(f"All tokens revoked for user {user_id}: {reason}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error revoking tokens for user {user_id}: {e}")
            return False
    
    async def revoke_token(self, token: str, reason: str = "Token revocation") -> bool:
        """Revoke a specific token"""
        try:
            # Add token to blacklist
            await self._blacklist_token(token)
            
            # If it's a refresh token, remove from tracking
            validation_result = await self.validate_token(token, "refresh")
            if validation_result.valid and validation_result.user_id:
                await self._revoke_refresh_token(validation_result.user_id, token)
            
            logger.info(f"Token revoked: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    async def monitor_expiration(self) -> Dict[str, Any]:
        """Proactive token expiration monitoring"""
        try:
            current_time = datetime.utcnow()
            stats = {
                "expiring_soon": 0,
                "expired": 0,
                "active": 0,
                "cleanup_performed": False
            }
            
            # Check for tokens expiring in the next hour
            expiring_soon = await self._get_tokens_expiring_soon(3600)  # 1 hour
            stats["expiring_soon"] = len(expiring_soon)
            
            # Check for expired tokens
            expired = await self._get_expired_tokens()
            stats["expired"] = len(expired)
            
            # Get active token count
            active = await self._get_active_token_count()
            stats["active"] = active
            
            # Perform cleanup if needed
            if expired:
                await self._cleanup_expired_tokens()
                stats["cleanup_performed"] = True
            
            logger.info(f"Token expiration monitoring completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during token expiration monitoring: {e}")
            return {"error": str(e)}
    
    async def get_user_token_stats(self, user_id: str) -> Dict[str, Any]:
        """Get token statistics for a user"""
        try:
            stats = {
                "active_tokens": 0,
                "refresh_tokens": 0,
                "last_activity": None,
                "device_count": 0
            }
            
            # Get active refresh tokens
            if self.enable_token_rotation:
                refresh_tokens = await self._get_user_refresh_tokens(user_id)
                stats["refresh_tokens"] = len(refresh_tokens)
            
            # Get token metadata
            metadata = await self._get_user_token_metadata(user_id)
            stats["active_tokens"] = len(metadata)
            
            if metadata:
                # Get last activity
                last_activity = max(token.last_used for token in metadata if token.last_used)
                stats["last_activity"] = last_activity
                
                # Count unique devices
                devices = set(token.device_info for token in metadata if token.device_info)
                stats["device_count"] = len(devices)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting token stats for user {user_id}: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
    def _generate_token_fingerprint(self, user_id: str, device_info: str = None, ip_address: str = None) -> str:
        """Generate unique token fingerprint"""
        data = f"{user_id}:{device_info or 'unknown'}:{ip_address or 'unknown'}:{secrets.token_hex(16)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    async def _create_access_token(self, user_id: str, fingerprint: str) -> str:
        """Create access token"""
        payload = {
            "sub": user_id,
            "type": "access",
            "fingerprint": fingerprint,
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)).timestamp()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def _create_refresh_token(self, user_id: str, fingerprint: str) -> str:
        """Create refresh token"""
        payload = {
            "sub": user_id,
            "type": "refresh",
            "fingerprint": fingerprint,
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)).timestamp()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def _store_token_metadata(self, metadata: TokenMetadata):
        """Store token metadata in Redis"""
        try:
            key = f"token_metadata:{metadata.user_id}:{metadata.token_fingerprint}"
            await self.redis.setex(
                key,
                self.refresh_token_expire_days * 24 * 3600,  # TTL in seconds
                metadata.model_dump_json()
            )
        except Exception as e:
            logger.error(f"Error storing token metadata: {e}")
    
    async def _track_refresh_token(self, user_id: str, refresh_token: str, fingerprint: str):
        """Track refresh token for rotation"""
        try:
            key = f"refresh_tokens:{user_id}"
            
            # Add new token
            token_data = {
                "token": refresh_token,
                "fingerprint": fingerprint,
                "created_at": datetime.utcnow().isoformat()
            }
            
            await self.redis.lpush(key, token_data)
            
            # Limit number of refresh tokens per user
            await self.redis.ltrim(key, 0, self.max_refresh_tokens_per_user - 1)
            
            # Set expiration
            await self.redis.expire(key, self.refresh_token_expire_days * 24 * 3600)
            
        except Exception as e:
            logger.error(f"Error tracking refresh token: {e}")
    
    async def _is_refresh_token_active(self, user_id: str, refresh_token: str) -> bool:
        """Check if refresh token is in active list"""
        try:
            key = f"refresh_tokens:{user_id}"
            tokens = await self.redis.lrange(key, 0, -1)
            
            for token_data in tokens:
                if token_data.get("token") == refresh_token:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking refresh token status: {e}")
            return False
    
    async def _revoke_refresh_token(self, user_id: str, refresh_token: str):
        """Revoke specific refresh token"""
        try:
            key = f"refresh_tokens:{user_id}"
            tokens = await self.redis.lrange(key, 0, -1)
            
            # Remove the specific token
            updated_tokens = [
                token_data for token_data in tokens
                if token_data.get("token") != refresh_token
            ]
            
            # Update the list
            if updated_tokens:
                await self.redis.delete(key)
                for token_data in updated_tokens:
                    await self.redis.lpush(key, token_data)
            else:
                await self.redis.delete(key)
                
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
    
    async def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            return await self.redis.exists(f"blacklist:{token_hash}")
        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False
    
    async def _blacklist_token(self, token: str):
        """Add token to blacklist"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            # Blacklist for maximum token lifetime
            await self.redis.setex(f"blacklist:{token_hash}", self.refresh_token_expire_days * 24 * 3600, "1")
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
    
    async def _blacklist_user_tokens(self, user_id: str):
        """Blacklist all tokens for a user"""
        try:
            # Get all token metadata for user
            pattern = f"token_metadata:{user_id}:*"
            keys = await self.redis.keys(pattern)
            
            for key in keys:
                metadata_json = await self.redis.get(key)
                if metadata_json:
                    # Extract fingerprint and blacklist
                    # This would require parsing the metadata to get the actual token
                    # For now, we'll rely on the repository cleanup
                    pass
                    
        except Exception as e:
            logger.error(f"Error blacklisting user tokens: {e}")
    
    async def _update_token_usage(self, user_id: str, fingerprint: str):
        """Update token usage statistics"""
        try:
            key = f"token_metadata:{user_id}:{fingerprint}"
            metadata_json = await self.redis.get(key)
            
            if metadata_json:
                metadata = TokenMetadata.model_validate_json(metadata_json)
                metadata.last_used = datetime.utcnow()
                metadata.usage_count += 1
                
                await self.redis.setex(
                    key,
                    self.refresh_token_expire_days * 24 * 3600,
                    metadata.model_dump_json()
                )
                
        except Exception as e:
            logger.error(f"Error updating token usage: {e}")
    
    async def _get_tokens_expiring_soon(self, seconds: int) -> List[Dict[str, Any]]:
        """Get tokens expiring within specified seconds"""
        # This would require scanning all token metadata
        # For now, return empty list
        return []
    
    async def _get_expired_tokens(self) -> List[Dict[str, Any]]:
        """Get expired tokens"""
        # This would require scanning all token metadata
        # For now, return empty list
        return []
    
    async def _get_active_token_count(self) -> int:
        """Get count of active tokens"""
        try:
            pattern = "token_metadata:*"
            keys = await self.redis.keys(pattern)
            return len(keys)
        except Exception as e:
            logger.error(f"Error getting active token count: {e}")
            return 0
    
    async def _cleanup_expired_tokens(self):
        """Clean up expired tokens"""
        try:
            # Clean up expired tokens in repository
            await self.user_repository.cleanup_expired_tokens()
            
            # Clean up expired metadata in Redis
            pattern = "token_metadata:*"
            keys = await self.redis.keys(pattern)
            
            for key in keys:
                metadata_json = await self.redis.get(key)
                if metadata_json:
                    try:
                        metadata = TokenMetadata.model_validate_json(metadata_json)
                        # Check if token is expired (this would need actual token validation)
                        # For now, rely on Redis TTL
                        pass
                    except Exception:
                        # Remove invalid metadata
                        await self.redis.delete(key)
            
            logger.info("Expired token cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during token cleanup: {e}")
    
    async def _clear_user_refresh_tokens(self, user_id: str):
        """Clear all refresh tokens for a user"""
        try:
            key = f"refresh_tokens:{user_id}"
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error clearing user refresh tokens: {e}")
    
    async def _get_user_refresh_tokens(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all refresh tokens for a user"""
        try:
            key = f"refresh_tokens:{user_id}"
            return await self.redis.lrange(key, 0, -1)
        except Exception as e:
            logger.error(f"Error getting user refresh tokens: {e}")
            return []
    
    async def _get_user_token_metadata(self, user_id: str) -> List[TokenMetadata]:
        """Get token metadata for a user"""
        try:
            pattern = f"token_metadata:{user_id}:*"
            keys = await self.redis.keys(pattern)
            
            metadata_list = []
            for key in keys:
                metadata_json = await self.redis.get(key)
                if metadata_json:
                    try:
                        metadata = TokenMetadata.model_validate_json(metadata_json)
                        metadata_list.append(metadata)
                    except Exception:
                        # Skip invalid metadata
                        continue
            
            return metadata_list
            
        except Exception as e:
            logger.error(f"Error getting user token metadata: {e}")
            return []
    
    async def _periodic_cleanup(self):
        """Periodic cleanup task"""
        while True:
            try:
                await asyncio.sleep(self.token_cleanup_interval)
                await self._cleanup_expired_tokens()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def _monitor_token_health(self):
        """Monitor token system health"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                stats = await self.monitor_expiration()
                logger.debug(f"Token health check: {stats}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in token health monitoring: {e}")
