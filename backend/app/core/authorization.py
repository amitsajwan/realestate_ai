"""
Scope-Based Authorization System
===============================
Granular permission system for OAuth and API access
"""

from typing import List, Dict, Any, Optional, Set
from enum import Enum
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
import logging

from app.models.user import User
from app.schemas.errors import create_auth_error, ErrorCodes

logger = logging.getLogger(__name__)


class Permission(Enum):
    """System permissions"""
    # User permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_DELETE = "admin:delete"
    
    # Property permissions
    PROPERTY_READ = "property:read"
    PROPERTY_WRITE = "property:write"
    PROPERTY_DELETE = "property:delete"
    
    # Social media permissions
    SOCIAL_READ = "social:read"
    SOCIAL_WRITE = "social:write"
    SOCIAL_DELETE = "social:delete"
    
    # Analytics permissions
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_WRITE = "analytics:write"
    
    # System permissions
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_DELETE = "system:delete"


class Role(Enum):
    """User roles with associated permissions"""
    USER = "user"
    PREMIUM_USER = "premium_user"
    AGENT = "agent"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.USER: {
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.PROPERTY_READ,
        Permission.SOCIAL_READ,
    },
    Role.PREMIUM_USER: {
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.PROPERTY_READ,
        Permission.PROPERTY_WRITE,
        Permission.SOCIAL_READ,
        Permission.SOCIAL_WRITE,
        Permission.ANALYTICS_READ,
    },
    Role.AGENT: {
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.PROPERTY_READ,
        Permission.PROPERTY_WRITE,
        Permission.PROPERTY_DELETE,
        Permission.SOCIAL_READ,
        Permission.SOCIAL_WRITE,
        Permission.SOCIAL_DELETE,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_WRITE,
    },
    Role.ADMIN: {
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_DELETE,
        Permission.ADMIN_READ,
        Permission.ADMIN_WRITE,
        Permission.PROPERTY_READ,
        Permission.PROPERTY_WRITE,
        Permission.PROPERTY_DELETE,
        Permission.SOCIAL_READ,
        Permission.SOCIAL_WRITE,
        Permission.SOCIAL_DELETE,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_WRITE,
        Permission.SYSTEM_READ,
    },
    Role.SUPER_ADMIN: {
        # Super admin has all permissions
        *[perm for perm in Permission],
    }
}


class ScopeValidator:
    """Scope-based authorization validator"""
    
    def __init__(self, required_permissions: List[Permission], require_all: bool = True):
        self.required_permissions = set(required_permissions)
        self.require_all = require_all
    
    async def __call__(self, current_user: User = Depends(get_current_user)):
        """Validate user permissions"""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=create_auth_error(
                    ErrorCodes.INVALID_CREDENTIALS,
                    "Authentication required"
                ).model_dump()
            )
        
        # Get user permissions
        user_permissions = await self._get_user_permissions(current_user)
        
        # Check permissions
        if self.require_all:
            # User must have all required permissions
            if not self.required_permissions.issubset(user_permissions):
                missing_permissions = self.required_permissions - user_permissions
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_auth_error(
                        ErrorCodes.INSUFFICIENT_PERMISSIONS,
                        f"Missing required permissions: {', '.join([p.value for p in missing_permissions])}",
                        suggestions=[
                            "Contact your administrator to request additional permissions",
                            "Upgrade your account to access this feature"
                        ]
                    ).model_dump()
                )
        else:
            # User must have at least one required permission
            if not self.required_permissions.intersection(user_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_auth_error(
                        ErrorCodes.INSUFFICIENT_PERMISSIONS,
                        f"None of the required permissions found: {', '.join([p.value for p in self.required_permissions])}",
                        suggestions=[
                            "Contact your administrator to request additional permissions",
                            "Upgrade your account to access this feature"
                        ]
                    ).model_dump()
                )
        
        return current_user
    
    async def _get_user_permissions(self, user: User) -> Set[Permission]:
        """Get user permissions based on role and custom permissions"""
        permissions = set()
        
        # Get role-based permissions
        user_role = await self._get_user_role(user)
        if user_role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[user_role])
        
        # Add custom permissions if any
        custom_permissions = await self._get_custom_permissions(user)
        permissions.update(custom_permissions)
        
        return permissions
    
    async def _get_user_role(self, user: User) -> Role:
        """Get user role from user model"""
        # This would typically come from the user model or a separate roles table
        # For now, we'll use a simple mapping based on user properties
        
        if user.is_superuser:
            return Role.SUPER_ADMIN
        elif hasattr(user, 'is_admin') and user.is_admin:
            return Role.ADMIN
        elif hasattr(user, 'is_agent') and user.is_agent:
            return Role.AGENT
        elif hasattr(user, 'is_premium') and user.is_premium:
            return Role.PREMIUM_USER
        else:
            return Role.USER
    
    async def _get_custom_permissions(self, user: User) -> Set[Permission]:
        """Get custom permissions for user"""
        # This would typically come from a database table
        # For now, return empty set
        return set()


class PermissionChecker:
    """Utility class for checking permissions"""
    
    @staticmethod
    async def has_permission(user: User, permission: Permission) -> bool:
        """Check if user has specific permission"""
        validator = ScopeValidator([permission])
        try:
            await validator(user)
            return True
        except HTTPException:
            return False
    
    @staticmethod
    async def has_any_permission(user: User, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        validator = ScopeValidator(permissions, require_all=False)
        try:
            await validator(user)
            return True
        except HTTPException:
            return False
    
    @staticmethod
    async def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions"""
        validator = ScopeValidator(permissions, require_all=True)
        try:
            await validator(user)
            return True
        except HTTPException:
            return False


# Convenience dependency functions
def require_permission(permission: Permission):
    """Dependency factory for single permission requirement"""
    return ScopeValidator([permission])


def require_permissions(permissions: List[Permission], require_all: bool = True):
    """Dependency factory for multiple permission requirements"""
    return ScopeValidator(permissions, require_all)


def require_role(role: Role):
    """Dependency factory for role requirement"""
    required_permissions = ROLE_PERMISSIONS.get(role, set())
    return ScopeValidator(list(required_permissions))


def require_admin():
    """Dependency for admin access"""
    return require_role(Role.ADMIN)


def require_super_admin():
    """Dependency for super admin access"""
    return require_role(Role.SUPER_ADMIN)


def require_agent():
    """Dependency for agent access"""
    return require_role(Role.AGENT)


def require_premium():
    """Dependency for premium user access"""
    return require_role(Role.PREMIUM_USER)


# OAuth scope mapping
OAUTH_SCOPE_PERMISSIONS: Dict[str, List[Permission]] = {
    "read": [Permission.USER_READ, Permission.PROPERTY_READ],
    "write": [Permission.USER_WRITE, Permission.PROPERTY_WRITE],
    "admin": [Permission.ADMIN_READ, Permission.ADMIN_WRITE],
    "social": [Permission.SOCIAL_READ, Permission.SOCIAL_WRITE],
    "analytics": [Permission.ANALYTICS_READ, Permission.ANALYTICS_WRITE],
    "system": [Permission.SYSTEM_READ, Permission.SYSTEM_WRITE],
}


class OAuthScopeValidator:
    """OAuth scope-based authorization"""
    
    def __init__(self, required_scopes: List[str]):
        self.required_scopes = required_scopes
    
    async def __call__(self, current_user: User = Depends(get_current_user)):
        """Validate OAuth scopes"""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=create_auth_error(
                    ErrorCodes.INVALID_CREDENTIALS,
                    "Authentication required"
                ).model_dump()
            )
        
        # Get user's OAuth scopes
        user_scopes = await self._get_user_oauth_scopes(current_user)
        
        # Check if user has required scopes
        missing_scopes = set(self.required_scopes) - set(user_scopes)
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_auth_error(
                    ErrorCodes.INSUFFICIENT_PERMISSIONS,
                    f"Missing required OAuth scopes: {', '.join(missing_scopes)}",
                    suggestions=[
                        "Re-authorize the application with additional scopes",
                        "Contact support if you believe this is an error"
                    ]
                ).model_dump()
            )
        
        return current_user
    
    async def _get_user_oauth_scopes(self, user: User) -> List[str]:
        """Get user's OAuth scopes"""
        # This would typically come from the OAuth token or user's connected accounts
        # For now, return default scopes based on user role
        user_role = await self._get_user_role(user)
        
        if user_role == Role.SUPER_ADMIN:
            return ["read", "write", "admin", "social", "analytics", "system"]
        elif user_role == Role.ADMIN:
            return ["read", "write", "admin", "social", "analytics"]
        elif user_role == Role.AGENT:
            return ["read", "write", "social", "analytics"]
        elif user_role == Role.PREMIUM_USER:
            return ["read", "write", "social", "analytics"]
        else:
            return ["read"]


# Resource-based authorization
class ResourcePermission:
    """Resource-specific permission checker"""
    
    def __init__(self, resource_type: str, action: str):
        self.resource_type = resource_type
        self.action = action
    
    async def check(self, user: User, resource_id: str = None) -> bool:
        """Check if user can perform action on resource"""
        # Get user permissions
        user_permissions = await self._get_user_permissions(user)
        
        # Check general permission
        required_permission = Permission(f"{self.resource_type}:{self.action}")
        if required_permission not in user_permissions:
            return False
        
        # Check resource-specific permissions if resource_id provided
        if resource_id:
            return await self._check_resource_access(user, resource_id)
        
        return True
    
    async def _get_user_permissions(self, user: User) -> Set[Permission]:
        """Get user permissions"""
        validator = ScopeValidator([])
        return await validator._get_user_permissions(user)
    
    async def _check_resource_access(self, user: User, resource_id: str) -> bool:
        """Check if user has access to specific resource"""
        # This would typically check ownership, sharing, or other access rules
        # For now, return True for all authenticated users
        return True


# Middleware for automatic permission checking
class AuthorizationMiddleware:
    """Middleware for automatic authorization checking"""
    
    def __init__(self, app):
        self.app = app
        self.permission_map = {
            # Map routes to required permissions
            "/api/v1/admin": [Permission.ADMIN_READ],
            "/api/v1/users": [Permission.USER_READ],
            "/api/v1/properties": [Permission.PROPERTY_READ],
            "/api/v1/social": [Permission.SOCIAL_READ],
            "/api/v1/analytics": [Permission.ANALYTICS_READ],
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Check if route requires authorization
        path = scope["path"]
        required_permissions = self._get_required_permissions(path)
        
        if required_permissions:
            # This would integrate with the request processing
            # For now, just pass through
            pass
        
        await self.app(scope, receive, send)
    
    def _get_required_permissions(self, path: str) -> List[Permission]:
        """Get required permissions for path"""
        for route_prefix, permissions in self.permission_map.items():
            if path.startswith(route_prefix):
                return permissions
        return []


# Helper function to get current user (placeholder)
async def get_current_user() -> Optional[User]:
    """Get current authenticated user"""
    # This would integrate with the actual authentication system
    # For now, return None
    return None
