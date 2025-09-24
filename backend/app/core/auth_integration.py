"""
Authentication System Integration
===============================
Main integration file that brings together all authentication components
"""

import asyncio
import logging
from typing import Optional
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorDatabase
import redis.asyncio as redis

from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.services.token_lifecycle_manager import TokenLifecycleManager
from app.core.enhanced_security import EnhancedSecurityManager, security_manager
from app.services.auth_health_monitor import AuthHealthMonitor
from app.core.refactored_auth_backend import initialize_auth_service, get_auth_service
from app.services.oauth_provider_factory import OAuthProviderFactory, SocialTokenManager

logger = logging.getLogger(__name__)


class AuthenticationSystem:
    """Main authentication system coordinator"""
    
    def __init__(self):
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.redis_client: Optional[redis.Redis] = None
        self.user_repository: Optional[UserRepository] = None
        self.token_manager: Optional[TokenLifecycleManager] = None
        self.security_manager: Optional[EnhancedSecurityManager] = None
        self.health_monitor: Optional[AuthHealthMonitor] = None
        self.social_token_manager: Optional[SocialTokenManager] = None
        self.initialized = False
    
    async def initialize(self, app: FastAPI, database: AsyncIOMotorDatabase):
        """Initialize the complete authentication system"""
        try:
            logger.info("Initializing authentication system...")
            
            # Store database reference
            self.database = database
            
            # Initialize Redis connection
            await self._initialize_redis()
            
            # Initialize repositories
            await self._initialize_repositories()
            
            # Initialize security manager
            await self._initialize_security_manager()
            
            # Initialize token manager
            await self._initialize_token_manager()
            
            # Initialize social token manager
            await self._initialize_social_token_manager()
            
            # Initialize health monitor
            await self._initialize_health_monitor()
            
            # Initialize authentication service
            await self._initialize_auth_service()
            
            # Setup routes
            await self._setup_routes(app)
            
            # Setup middleware
            await self._setup_middleware(app)
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.initialized = True
            logger.info("Authentication system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize authentication system: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the authentication system"""
        try:
            logger.info("Shutting down authentication system...")
            
            # Shutdown token manager
            if self.token_manager:
                await self.token_manager.shutdown()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            self.initialized = False
            logger.info("Authentication system shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during authentication system shutdown: {e}")
    
    async def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            # Continue without Redis - will use in-memory fallback
            self.redis_client = None
    
    async def _initialize_repositories(self):
        """Initialize data repositories"""
        try:
            self.user_repository = UserRepository(self.database)
            logger.info("User repository initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize repositories: {e}")
            raise
    
    async def _initialize_security_manager(self):
        """Initialize security manager"""
        try:
            # Use the global security manager instance
            self.security_manager = security_manager
            await self.security_manager.initialize()
            logger.info("Security manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize security manager: {e}")
            raise
    
    async def _initialize_token_manager(self):
        """Initialize token lifecycle manager"""
        try:
            if not self.redis_client:
                raise ValueError("Redis client required for token manager")
            
            self.token_manager = TokenLifecycleManager(
                user_repository=self.user_repository,
                redis_client=self.redis_client
            )
            
            await self.token_manager.initialize()
            logger.info("Token lifecycle manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize token manager: {e}")
            raise
    
    async def _initialize_social_token_manager(self):
        """Initialize social token manager"""
        try:
            if not self.redis_client:
                logger.warning("Redis not available - social token manager will use in-memory storage")
            
            self.social_token_manager = SocialTokenManager(
                user_repository=self.user_repository,
                redis_client=self.redis_client
            )
            logger.info("Social token manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize social token manager: {e}")
            # Non-critical - continue without social token manager
            self.social_token_manager = None
    
    async def _initialize_health_monitor(self):
        """Initialize health monitor"""
        try:
            self.health_monitor = AuthHealthMonitor(
                database=self.database,
                redis_client=self.redis_client,
                user_repository=self.user_repository,
                token_manager=self.token_manager,
                security_manager=self.security_manager
            )
            logger.info("Health monitor initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize health monitor: {e}")
            # Non-critical - continue without health monitor
            self.health_monitor = None
    
    async def _initialize_auth_service(self):
        """Initialize authentication service"""
        try:
            initialize_auth_service(
                user_repository=self.user_repository,
                token_manager=self.token_manager,
                security_manager=self.security_manager
            )
            logger.info("Authentication service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize authentication service: {e}")
            raise
    
    async def _setup_routes(self, app: FastAPI):
        """Setup authentication routes"""
        try:
            from fastapi import APIRouter
            from app.core.refactored_auth_backend import get_auth_service
            
            auth_service = get_auth_service()
            
            # Create authentication router
            auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
            
            # Add FastAPI Users routes
            auth_router.include_router(auth_service.get_auth_router(), prefix="/jwt")
            auth_router.include_router(auth_service.get_register_router(), prefix="/register")
            auth_router.include_router(auth_service.get_reset_password_router(), prefix="/reset-password")
            auth_router.include_router(auth_service.get_verify_router(), prefix="/verify")
            
            # Add custom authentication endpoints
            await self._add_custom_auth_endpoints(auth_router)
            
            # Add OAuth endpoints
            await self._add_oauth_endpoints(auth_router)
            
            # Add health check endpoints
            await self._add_health_endpoints(auth_router)
            
            # Include router in app
            app.include_router(auth_router)
            
            logger.info("Authentication routes configured")
            
        except Exception as e:
            logger.error(f"Failed to setup routes: {e}")
            raise
    
    async def _add_custom_auth_endpoints(self, router):
        """Add custom authentication endpoints"""
        from fastapi import Depends, HTTPException, status
        from app.schemas.errors import create_auth_error, ErrorCodes
        from app.core.refactored_auth_backend import get_auth_service
        
        @router.post("/login")
        async def login(
            email: str,
            password: str,
            device_info: str = None,
            ip_address: str = None
        ):
            """Enhanced login endpoint"""
            auth_service = get_auth_service()
            return await auth_service.authenticate_user(email, password, device_info, ip_address)
        
        @router.post("/refresh")
        async def refresh_tokens(
            refresh_token: str,
            device_info: str = None,
            ip_address: str = None
        ):
            """Token refresh endpoint"""
            auth_service = get_auth_service()
            return await auth_service.refresh_user_tokens(refresh_token, device_info, ip_address)
        
        @router.post("/logout")
        async def logout(
            current_user = Depends(get_auth_service().current_active_user)
        ):
            """Logout endpoint"""
            auth_service = get_auth_service()
            success = await auth_service.logout_user(str(current_user.id))
            return {"success": success, "message": "Logged out successfully"}
        
        @router.get("/me")
        async def get_current_user_info(
            current_user = Depends(get_auth_service().current_active_user)
        ):
            """Get current user information"""
            return {
                "id": str(current_user.id),
                "email": current_user.email,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "is_active": current_user.is_active,
                "is_verified": current_user.is_verified,
                "onboarding_completed": current_user.onboarding_completed,
                "onboarding_step": current_user.onboarding_step
            }
        
        # Development endpoints
        if settings.environment == "development":
            @router.get("/dev/tokens")
            async def get_development_tokens():
                """Get development tokens for testing"""
                auth_service = get_auth_service()
                return await auth_service.auth_backend.get_development_tokens()
    
    async def _add_oauth_endpoints(self, router):
        """Add OAuth endpoints"""
        from fastapi import Query, HTTPException, status
        from app.schemas.errors import create_oauth_error, ErrorCodes
        
        @router.get("/oauth/{provider}/login")
        async def oauth_login(provider: str):
            """Initiate OAuth login"""
            try:
                oauth_provider = OAuthProviderFactory.create_provider(provider)
                state = oauth_provider.generate_state()
                
                # Store state for validation
                if self.redis_client:
                    await self.redis_client.setex(f"oauth_state:{state}", 600, "valid")  # 10 minutes
                
                auth_url = await oauth_provider.get_authorization_url(state)
                return {"auth_url": auth_url, "state": state}
                
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=create_oauth_error(
                        ErrorCodes.OAUTH_PROVIDER_ERROR,
                        f"Unsupported OAuth provider: {provider}"
                    ).model_dump()
                )
        
        @router.get("/oauth/{provider}/callback")
        async def oauth_callback(
            provider: str,
            code: str = Query(...),
            state: str = Query(...)
        ):
            """Handle OAuth callback"""
            try:
                # Validate state
                if self.redis_client:
                    stored_state = await self.redis_client.get(f"oauth_state:{state}")
                    if not stored_state:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=create_oauth_error(
                                ErrorCodes.OAUTH_STATE_INVALID,
                                "Invalid or expired OAuth state"
                            ).model_dump()
                        )
                    await self.redis_client.delete(f"oauth_state:{state}")
                
                # Create OAuth provider
                oauth_provider = OAuthProviderFactory.create_provider(provider)
                
                # Exchange code for token
                token_data = await oauth_provider.exchange_code_for_token(code, state)
                
                # Get user info
                user_info = await oauth_provider.get_user_info(token_data.access_token)
                
                # Handle user creation/login
                # This would integrate with your user management system
                
                return {
                    "success": True,
                    "provider": provider,
                    "user_info": user_info.model_dump(),
                    "access_token": token_data.access_token
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"OAuth callback error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=create_oauth_error(
                        ErrorCodes.OAUTH_PROVIDER_ERROR,
                        f"OAuth callback failed: {str(e)}"
                    ).model_dump()
                )
    
    async def _add_health_endpoints(self, router):
        """Add health check endpoints"""
        from fastapi import Depends
        from app.core.authorization import require_admin
        
        @router.get("/health")
        async def auth_health_check():
            """Authentication system health check"""
            if not self.health_monitor:
                return {"status": "unavailable", "message": "Health monitor not initialized"}
            
            return await self.health_monitor.check_auth_system_health()
        
        @router.get("/health/history")
        async def auth_health_history(
            limit: int = 10,
            current_user = Depends(require_admin())
        ):
            """Get health check history"""
            if not self.health_monitor:
                return {"error": "Health monitor not initialized"}
            
            return await self.health_monitor.get_health_history(limit)
        
        @router.get("/health/metrics")
        async def auth_health_metrics(
            hours: int = 24,
            current_user = Depends(require_admin())
        ):
            """Get health metrics"""
            if not self.health_monitor:
                return {"error": "Health monitor not initialized"}
            
            return await self.health_monitor.get_health_metrics(hours)
    
    async def _setup_middleware(self, app: FastAPI):
        """Setup authentication middleware"""
        try:
            from app.core.enhanced_security import SecurityMiddleware
            
            # Add security middleware
            app.add_middleware(SecurityMiddleware)
            
            logger.info("Authentication middleware configured")
            
        except Exception as e:
            logger.error(f"Failed to setup middleware: {e}")
            # Non-critical - continue without middleware
    
    async def _start_background_tasks(self):
        """Start background tasks"""
        try:
            # Start health monitoring task
            if self.health_monitor:
                asyncio.create_task(self._health_monitoring_task())
            
            logger.info("Background tasks started")
            
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
    
    async def _health_monitoring_task(self):
        """Background health monitoring task"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self.health_monitor.check_auth_system_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring task error: {e}")


# Global authentication system instance
auth_system: Optional[AuthenticationSystem] = None


async def initialize_authentication_system(app: FastAPI, database: AsyncIOMotorDatabase):
    """Initialize the global authentication system"""
    global auth_system
    auth_system = AuthenticationSystem()
    await auth_system.initialize(app, database)
    return auth_system


async def shutdown_authentication_system():
    """Shutdown the global authentication system"""
    global auth_system
    if auth_system:
        await auth_system.shutdown()
        auth_system = None


def get_authentication_system() -> AuthenticationSystem:
    """Get the global authentication system"""
    if auth_system is None:
        raise RuntimeError("Authentication system not initialized")
    return auth_system
