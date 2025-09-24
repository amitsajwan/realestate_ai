# Authentication System Migration Guide

## Overview

This guide outlines the migration from the current authentication system to the new refactored OAuth authentication architecture. The new system addresses critical security issues and provides a production-ready foundation.

## Key Improvements

### 1. Security Enhancements
- **Eliminated Development Bypass**: Removed the dangerous mock authentication system
- **Token Rotation**: Implemented rolling refresh token rotation
- **Enhanced Rate Limiting**: Intelligent rate limiting with Redis backend
- **Input Validation**: Comprehensive security validation and sanitization
- **Centralized Security**: Unified security management across all components

### 2. Architecture Improvements
- **Repository Pattern**: Clean data access layer abstraction
- **Service Layer**: Proper separation of concerns
- **Error Standardization**: Consistent error responses across all endpoints
- **Health Monitoring**: Comprehensive system health monitoring and alerting

### 3. OAuth Enhancements
- **Multi-Provider Support**: Strategy pattern for multiple OAuth providers
- **Scope-Based Authorization**: Granular permission system
- **Token Lifecycle Management**: Complete token lifecycle with monitoring
- **Social Token Management**: Enhanced social media token handling

## Migration Steps

### Phase 1: Foundation (Week 1-2)

#### 1.1 Install Dependencies
```bash
pip install redis psutil httpx
```

#### 1.2 Update Configuration
Add to your `.env` file:
```env
# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=
REDIS_DB=0

# Enhanced Security
ENABLE_TOKEN_ROTATION=true
MAX_REFRESH_TOKENS_PER_USER=5
SECURITY_ALERTING_ENABLED=true
```

#### 1.3 Database Updates
The new system requires additional collections. Run the database initialization:

```python
# Add to your database initialization
from app.utils.database_init import initialize_authentication_collections

async def initialize_database():
    # ... existing initialization ...
    await initialize_authentication_collections(db)
```

### Phase 2: Token Management (Week 3-4)

#### 2.1 Update User Model
Add token-related fields to your user model:

```python
# Add to User model
class User(Document):
    # ... existing fields ...
    
    # Token management
    active_tokens_count: int = 0
    last_token_refresh: Optional[datetime] = None
    
    # OAuth connections
    oauth_connections: Dict[str, Dict[str, Any]] = {}
    
    # Security
    failed_login_attempts: int = 0
    last_failed_login: Optional[datetime] = None
    account_locked_until: Optional[datetime] = None
```

#### 2.2 Update Authentication Endpoints
Replace existing authentication endpoints with the new system:

```python
# Replace in your main app
from app.core.auth_integration import initialize_authentication_system

async def startup():
    # ... existing startup code ...
    await initialize_authentication_system(app, database)
```

### Phase 3: OAuth Enhancement (Week 5-6)

#### 3.1 Update OAuth Configuration
Configure OAuth providers in your settings:

```python
# Add to settings
class Settings(BaseSettings):
    # ... existing settings ...
    
    # OAuth Providers
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
```

#### 3.2 Update Frontend Integration
Update your frontend to use the new OAuth endpoints:

```javascript
// New OAuth flow
const initiateOAuth = async (provider) => {
    const response = await fetch(`/api/v1/auth/oauth/${provider}/login`);
    const { auth_url } = await response.json();
    window.location.href = auth_url;
};

const handleOAuthCallback = async (provider, code, state) => {
    const response = await fetch(`/api/v1/auth/oauth/${provider}/callback?code=${code}&state=${state}`);
    const result = await response.json();
    // Handle authentication result
};
```

### Phase 4: Security Hardening (Week 7-8)

#### 4.1 Update Middleware
Replace existing security middleware:

```python
# Remove old middleware and add new
from app.core.enhanced_security import SecurityMiddleware

app.add_middleware(SecurityMiddleware)
```

#### 4.2 Update Rate Limiting
Replace existing rate limiting with the new system:

```python
# The new system automatically handles rate limiting
# No additional configuration needed
```

## Breaking Changes

### 1. Authentication Dependencies
**Before:**
```python
from app.core.auth_backend import current_active_user

@router.get("/protected")
async def protected_endpoint(user: User = Depends(current_active_user)):
    pass
```

**After:**
```python
from app.core.refactored_auth_backend import get_current_user

@router.get("/protected")
async def protected_endpoint(user: User = Depends(get_current_user())):
    pass
```

### 2. Error Responses
**Before:**
```python
raise HTTPException(status_code=401, detail="Unauthorized")
```

**After:**
```python
from app.schemas.errors import create_auth_error, ErrorCodes

raise HTTPException(
    status_code=401,
    detail=create_auth_error(ErrorCodes.INVALID_CREDENTIALS).model_dump()
)
```

### 3. Token Management
**Before:**
```python
# Manual token handling
token = create_access_token(data={"sub": user_id})
```

**After:**
```python
from app.core.refactored_auth_backend import get_auth_service

auth_service = get_auth_service()
tokens = await auth_service.authenticate_user(email, password)
```

## Testing

### 1. Development Environment
The new system provides proper development support:

```python
# Get development tokens
GET /api/v1/auth/dev/tokens

# Response
{
    "access_token": "...",
    "refresh_token": "...",
    "user": {
        "id": "...",
        "email": "dev@example.com"
    }
}
```

### 2. Health Monitoring
Monitor system health:

```python
# Check authentication system health
GET /api/v1/auth/health

# Get health metrics
GET /api/v1/auth/health/metrics?hours=24
```

## Rollback Plan

If issues arise during migration:

1. **Immediate Rollback**: Revert to previous authentication backend
2. **Database Rollback**: Restore previous user collections
3. **Configuration Rollback**: Revert environment variables
4. **Frontend Rollback**: Revert OAuth integration changes

## Performance Considerations

### 1. Redis Requirements
- **Memory**: ~100MB for typical usage
- **CPU**: Minimal impact
- **Network**: Low latency connection recommended

### 2. Database Impact
- **Read Operations**: Slight increase due to repository pattern
- **Write Operations**: Minimal impact
- **Indexes**: Ensure proper indexing on user collections

### 3. Token Storage
- **Access Tokens**: Stored in JWT (stateless)
- **Refresh Tokens**: Stored in Redis with TTL
- **Metadata**: Stored in Redis for tracking

## Security Considerations

### 1. Secret Management
- **JWT Secrets**: Use strong, rotated secrets
- **OAuth Secrets**: Store securely in environment variables
- **Redis**: Use authentication if exposed

### 2. Token Security
- **Rotation**: Automatic refresh token rotation
- **Blacklisting**: Immediate token revocation
- **Monitoring**: Track token usage patterns

### 3. Rate Limiting
- **IP-based**: Automatic IP blocking for abuse
- **User-based**: Per-user rate limiting
- **Endpoint-based**: Granular endpoint protection

## Monitoring and Alerting

### 1. Health Checks
- **Database Connectivity**: MongoDB connection status
- **Redis Connectivity**: Redis connection status
- **Token Generation**: JWT creation and validation
- **OAuth Providers**: External provider status
- **Rate Limiting**: Rate limiter functionality

### 2. Metrics
- **Authentication Success Rate**: Login success percentage
- **Token Refresh Rate**: Token refresh frequency
- **Failed Login Attempts**: Security monitoring
- **OAuth Usage**: Social login statistics

### 3. Alerts
- **Critical Issues**: System failures
- **Security Events**: Suspicious activity
- **Performance Issues**: High response times
- **Resource Usage**: Memory/CPU thresholds

## Support and Troubleshooting

### 1. Common Issues
- **Redis Connection**: Check Redis server status
- **Token Validation**: Verify JWT secret configuration
- **OAuth Errors**: Check provider configuration
- **Rate Limiting**: Review rate limit settings

### 2. Debugging
- **Logs**: Check application logs for errors
- **Health Endpoints**: Use health check endpoints
- **Metrics**: Monitor system metrics
- **Redis**: Check Redis key expiration

### 3. Performance Tuning
- **Redis Memory**: Monitor Redis memory usage
- **Token TTL**: Adjust token expiration times
- **Rate Limits**: Tune rate limiting thresholds
- **Database Indexes**: Optimize database queries

## Conclusion

The new authentication system provides a robust, secure, and scalable foundation for your real estate AI platform. The migration should be performed in phases to minimize risk and ensure proper testing at each stage.

For questions or issues during migration, refer to the troubleshooting section or contact the development team.
