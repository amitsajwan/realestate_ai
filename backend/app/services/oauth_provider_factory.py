"""
OAuth Provider Factory and Strategy Pattern
===========================================
Multi-provider OAuth integration with strategy pattern
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx
import secrets
import logging
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.errors import create_oauth_error, ErrorCodes

logger = logging.getLogger(__name__)


class OAuthProviderConfig(BaseModel):
    """OAuth provider configuration"""
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str]
    auth_url: str
    token_url: str
    user_info_url: str
    api_base_url: Optional[str] = None


class OAuthUserInfo(BaseModel):
    """Standardized OAuth user information"""
    provider: str
    provider_user_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture: Optional[str] = None
    raw_data: Dict[str, Any] = {}


class OAuthTokenData(BaseModel):
    """OAuth token data"""
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "bearer"
    scope: Optional[str] = None
    created_at: datetime = datetime.utcnow()


class OAuthProvider(ABC):
    """Abstract base class for OAuth providers"""
    
    def __init__(self, config: OAuthProviderConfig):
        self.config = config
        self.provider_name = self.__class__.__name__.replace("OAuthProvider", "").lower()
    
    @abstractmethod
    async def get_authorization_url(self, state: str) -> str:
        """Generate authorization URL"""
        pass
    
    @abstractmethod
    async def exchange_code_for_token(self, code: str, state: str) -> OAuthTokenData:
        """Exchange authorization code for access token"""
        pass
    
    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user information from provider"""
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> OAuthTokenData:
        """Refresh access token"""
        pass
    
    @abstractmethod
    async def revoke_token(self, access_token: str) -> bool:
        """Revoke access token"""
        pass
    
    def generate_state(self) -> str:
        """Generate secure state parameter"""
        return secrets.token_urlsafe(32)
    
    def validate_state(self, received_state: str, expected_state: str) -> bool:
        """Validate state parameter"""
        return received_state == expected_state


class FacebookOAuthProvider(OAuthProvider):
    """Facebook OAuth provider implementation"""
    
    def __init__(self, config: OAuthProviderConfig):
        super().__init__(config)
        self.provider_name = "facebook"
    
    async def get_authorization_url(self, state: str) -> str:
        """Generate Facebook authorization URL"""
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": ",".join(self.config.scopes),
            "response_type": "code",
            "state": state
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config.auth_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, state: str) -> OAuthTokenData:
        """Exchange code for Facebook access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.token_url,
                    data={
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "redirect_uri": self.config.redirect_uri,
                        "code": code
                    }
                )
                response.raise_for_status()
                
                token_data = response.json()
                
                return OAuthTokenData(
                    access_token=token_data["access_token"],
                    expires_in=token_data.get("expires_in"),
                    token_type=token_data.get("token_type", "bearer"),
                    scope=token_data.get("scope")
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Facebook token exchange error: {e}")
            raise create_oauth_error(
                ErrorCodes.OAUTH_TOKEN_EXCHANGE_FAILED,
                f"Failed to exchange Facebook authorization code: {str(e)}",
                provider="facebook"
            )
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get Facebook user information"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.config.user_info_url,
                    params={
                        "access_token": access_token,
                        "fields": "id,name,email,first_name,last_name,picture"
                    }
                )
                response.raise_for_status()
                
                user_data = response.json()
                
                return OAuthUserInfo(
                    provider=self.provider_name,
                    provider_user_id=user_data["id"],
                    email=user_data.get("email", ""),
                    first_name=user_data.get("first_name"),
                    last_name=user_data.get("last_name"),
                    profile_picture=user_data.get("picture", {}).get("data", {}).get("url"),
                    raw_data=user_data
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Facebook user info error: {e}")
            raise create_oauth_error(
                ErrorCodes.OAUTH_PROVIDER_ERROR,
                f"Failed to get Facebook user information: {str(e)}",
                provider="facebook"
            )
    
    async def refresh_token(self, refresh_token: str) -> OAuthTokenData:
        """Refresh Facebook access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.token_url}",
                    params={
                        "grant_type": "fb_exchange_token",
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "fb_exchange_token": refresh_token
                    }
                )
                response.raise_for_status()
                
                token_data = response.json()
                
                return OAuthTokenData(
                    access_token=token_data["access_token"],
                    expires_in=token_data.get("expires_in"),
                    token_type=token_data.get("token_type", "bearer")
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Facebook token refresh error: {e}")
            raise create_oauth_error(
                ErrorCodes.OAUTH_PROVIDER_ERROR,
                f"Failed to refresh Facebook token: {str(e)}",
                provider="facebook"
            )
    
    async def revoke_token(self, access_token: str) -> bool:
        """Revoke Facebook access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.config.api_base_url}/me/permissions",
                    params={"access_token": access_token}
                )
                return response.status_code == 200
                
        except httpx.HTTPError as e:
            logger.error(f"Facebook token revocation error: {e}")
            return False


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth provider implementation"""
    
    def __init__(self, config: OAuthProviderConfig):
        super().__init__(config)
        self.provider_name = "google"
    
    async def get_authorization_url(self, state: str) -> str:
        """Generate Google authorization URL"""
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(self.config.scopes),
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config.auth_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, state: str) -> OAuthTokenData:
        """Exchange code for Google access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.token_url,
                    data={
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "redirect_uri": self.config.redirect_uri,
                        "code": code,
                        "grant_type": "authorization_code"
                    }
                )
                response.raise_for_status()
                
                token_data = response.json()
                
                return OAuthTokenData(
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token"),
                    expires_in=token_data.get("expires_in"),
                    token_type=token_data.get("token_type", "bearer"),
                    scope=token_data.get("scope")
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Google token exchange error: {e}")
            raise create_oauth_error(
                ErrorCodes.OAUTH_TOKEN_EXCHANGE_FAILED,
                f"Failed to exchange Google authorization code: {str(e)}",
                provider="google"
            )
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get Google user information"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.config.user_info_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                
                user_data = response.json()
                
                return OAuthUserInfo(
                    provider=self.provider_name,
                    provider_user_id=user_data["id"],
                    email=user_data.get("email", ""),
                    first_name=user_data.get("given_name"),
                    last_name=user_data.get("family_name"),
                    profile_picture=user_data.get("picture"),
                    raw_data=user_data
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Google user info error: {e}")
            raise create_oauth_error(
                ErrorCodes.OAUTH_PROVIDER_ERROR,
                f"Failed to get Google user information: {str(e)}",
                provider="google"
            )
    
    async def refresh_token(self, refresh_token: str) -> OAuthTokenData:
        """Refresh Google access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.token_url,
                    data={
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                response.raise_for_status()
                
                token_data = response.json()
                
                return OAuthTokenData(
                    access_token=token_data["access_token"],
                    refresh_token=refresh_token,  # Google doesn't return new refresh token
                    expires_in=token_data.get("expires_in"),
                    token_type=token_data.get("token_type", "bearer")
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Google token refresh error: {e}")
            raise create_oauth_error(
                ErrorCodes.OAUTH_PROVIDER_ERROR,
                f"Failed to refresh Google token: {str(e)}",
                provider="google"
            )
    
    async def revoke_token(self, access_token: str) -> bool:
        """Revoke Google access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": access_token}
                )
                return response.status_code == 200
                
        except httpx.HTTPError as e:
            logger.error(f"Google token revocation error: {e}")
            return False


class LinkedInOAuthProvider(OAuthProvider):
    """LinkedIn OAuth provider implementation"""
    
    def __init__(self, config: OAuthProviderConfig):
        super().__init__(config)
        self.provider_name = "linkedin"
    
    async def get_authorization_url(self, state: str) -> str:
        """Generate LinkedIn authorization URL"""
        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "state": state,
            "scope": " ".join(self.config.scopes)
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config.auth_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, state: str) -> OAuthTokenData:
        """Exchange code for LinkedIn access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": self.config.redirect_uri,
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret
                    }
                )
                response.raise_for_status()
                
                token_data = response.json()
                
                return OAuthTokenData(
                    access_token=token_data["access_token"],
                    expires_in=token_data.get("expires_in"),
                    token_type=token_data.get("token_type", "bearer"),
                    scope=token_data.get("scope")
                )
                
        except httpx.HTTPError as e:
            logger.error(f"LinkedIn token exchange error: {e}")
            raise create_oauth_error(
                ErrorCodes.OAUTH_TOKEN_EXCHANGE_FAILED,
                f"Failed to exchange LinkedIn authorization code: {str(e)}",
                provider="linkedin"
            )
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get LinkedIn user information"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.config.user_info_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                
                user_data = response.json()
                
                return OAuthUserInfo(
                    provider=self.provider_name,
                    provider_user_id=user_data["id"],
                    email=user_data.get("emailAddress", ""),
                    first_name=user_data.get("firstName", {}).get("localized", {}).get("en_US"),
                    last_name=user_data.get("lastName", {}).get("localized", {}).get("en_US"),
                    profile_picture=user_data.get("profilePicture", {}).get("displayImage~", {}).get("elements", [{}])[0].get("identifiers", [{}])[0].get("identifier"),
                    raw_data=user_data
                )
                
        except httpx.HTTPError as e:
            logger.error(f"LinkedIn user info error: {e}")
            raise create_oauth_error(
                ErrorCodes.OAUTH_PROVIDER_ERROR,
                f"Failed to get LinkedIn user information: {str(e)}",
                provider="linkedin"
            )
    
    async def refresh_token(self, refresh_token: str) -> OAuthTokenData:
        """Refresh LinkedIn access token"""
        # LinkedIn doesn't support refresh tokens in the same way
        raise create_oauth_error(
            ErrorCodes.OAUTH_PROVIDER_ERROR,
            "LinkedIn does not support token refresh",
            provider="linkedin"
        )
    
    async def revoke_token(self, access_token: str) -> bool:
        """Revoke LinkedIn access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://www.linkedin.com/oauth/v2/revoke",
                    params={"token": access_token}
                )
                return response.status_code == 200
                
        except httpx.HTTPError as e:
            logger.error(f"LinkedIn token revocation error: {e}")
            return False


class OAuthProviderFactory:
    """Factory for creating OAuth providers"""
    
    _providers = {
        "facebook": FacebookOAuthProvider,
        "google": GoogleOAuthProvider,
        "linkedin": LinkedInOAuthProvider
    }
    
    @classmethod
    def create_provider(cls, provider_type: str) -> OAuthProvider:
        """Create OAuth provider instance"""
        if provider_type not in cls._providers:
            raise ValueError(f"Unsupported OAuth provider: {provider_type}")
        
        # Get provider configuration
        config = cls._get_provider_config(provider_type)
        
        # Create provider instance
        provider_class = cls._providers[provider_type]
        return provider_class(config)
    
    @classmethod
    def _get_provider_config(cls, provider_type: str) -> OAuthProviderConfig:
        """Get provider configuration from settings"""
        if provider_type == "facebook":
            return OAuthProviderConfig(
                client_id=settings.facebook_app_id or "",
                client_secret=settings.facebook_app_secret or "",
                redirect_uri=f"{settings.cors_origins[0]}/api/v1/oauth/facebook/callback",
                scopes=["email", "public_profile"],
                auth_url="https://www.facebook.com/v18.0/dialog/oauth",
                token_url="https://graph.facebook.com/v18.0/oauth/access_token",
                user_info_url="https://graph.facebook.com/me",
                api_base_url="https://graph.facebook.com"
            )
        elif provider_type == "google":
            return OAuthProviderConfig(
                client_id=settings.google_client_id or "",
                client_secret=settings.google_client_secret or "",
                redirect_uri=f"{settings.cors_origins[0]}/api/v1/oauth/google/callback",
                scopes=["openid", "email", "profile"],
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                user_info_url="https://www.googleapis.com/oauth2/v2/userinfo"
            )
        elif provider_type == "linkedin":
            return OAuthProviderConfig(
                client_id=settings.linkedin_client_id or "",
                client_secret=settings.linkedin_client_secret or "",
                redirect_uri=f"{settings.cors_origins[0]}/api/v1/oauth/linkedin/callback",
                scopes=["r_liteprofile", "r_emailaddress"],
                auth_url="https://www.linkedin.com/oauth/v2/authorization",
                token_url="https://www.linkedin.com/oauth/v2/accessToken",
                user_info_url="https://api.linkedin.com/v2/people/~"
            )
        else:
            raise ValueError(f"No configuration found for provider: {provider_type}")
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported OAuth providers"""
        return list(cls._providers.keys())
    
    @classmethod
    def register_provider(cls, provider_type: str, provider_class: type):
        """Register a new OAuth provider"""
        if not issubclass(provider_class, OAuthProvider):
            raise ValueError("Provider class must inherit from OAuthProvider")
        
        cls._providers[provider_type] = provider_class
        logger.info(f"Registered OAuth provider: {provider_type}")


class SocialTokenManager:
    """Enhanced token management for social providers"""
    
    def __init__(self, user_repository, redis_client):
        self.user_repository = user_repository
        self.redis = redis_client
    
    async def store_provider_tokens(self, user_id: str, provider: str, tokens: OAuthTokenData) -> bool:
        """Store provider tokens with encryption"""
        try:
            # Encrypt tokens before storage
            encrypted_tokens = await self._encrypt_tokens(tokens)
            
            # Store in Redis with TTL
            key = f"social_tokens:{user_id}:{provider}"
            await self.redis.setex(
                key,
                tokens.expires_in or 3600,  # Default 1 hour if no expiration
                encrypted_tokens
            )
            
            # Also store in database for persistence
            await self.user_repository.update_social_connection(
                user_id, 
                provider, 
                {
                    "access_token": tokens.access_token,
                    "refresh_token": tokens.refresh_token,
                    "expires_at": datetime.utcnow() + timedelta(seconds=tokens.expires_in or 3600),
                    "connected_at": datetime.utcnow()
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing provider tokens: {e}")
            return False
    
    async def get_provider_tokens(self, user_id: str, provider: str) -> Optional[OAuthTokenData]:
        """Get provider tokens"""
        try:
            key = f"social_tokens:{user_id}:{provider}"
            encrypted_tokens = await self.redis.get(key)
            
            if encrypted_tokens:
                return await self._decrypt_tokens(encrypted_tokens)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting provider tokens: {e}")
            return None
    
    async def refresh_provider_tokens(self, user_id: str, provider: str) -> Optional[OAuthTokenData]:
        """Refresh provider tokens"""
        try:
            # Get current tokens
            current_tokens = await self.get_provider_tokens(user_id, provider)
            if not current_tokens or not current_tokens.refresh_token:
                return None
            
            # Create provider and refresh token
            oauth_provider = OAuthProviderFactory.create_provider(provider)
            new_tokens = await oauth_provider.refresh_token(current_tokens.refresh_token)
            
            # Store new tokens
            await self.store_provider_tokens(user_id, provider, new_tokens)
            
            return new_tokens
            
        except Exception as e:
            logger.error(f"Error refreshing provider tokens: {e}")
            return None
    
    async def handle_token_expiration(self, user_id: str, provider: str) -> bool:
        """Handle token expiration gracefully"""
        try:
            # Try to refresh token
            new_tokens = await self.refresh_provider_tokens(user_id, provider)
            
            if new_tokens:
                logger.info(f"Successfully refreshed {provider} tokens for user {user_id}")
                return True
            else:
                # Mark connection as expired
                await self.user_repository.update_social_connection(
                    user_id,
                    provider,
                    {"expired": True, "expired_at": datetime.utcnow()}
                )
                logger.warning(f"Failed to refresh {provider} tokens for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling token expiration: {e}")
            return False
    
    async def _encrypt_tokens(self, tokens: OAuthTokenData) -> str:
        """Encrypt tokens for storage"""
        # Simple base64 encoding for now - in production, use proper encryption
        import base64
        import json
        
        token_json = tokens.model_dump_json()
        return base64.b64encode(token_json.encode()).decode()
    
    async def _decrypt_tokens(self, encrypted_tokens: str) -> OAuthTokenData:
        """Decrypt tokens from storage"""
        # Simple base64 decoding for now - in production, use proper decryption
        import base64
        import json
        
        token_json = base64.b64decode(encrypted_tokens.encode()).decode()
        return OAuthTokenData.model_validate_json(token_json)
