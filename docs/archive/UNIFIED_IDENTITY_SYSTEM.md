# Unified Identity System

## 🎯 Overview

The Unified Identity System provides a clean, token-driven architecture that separates internal user identity from external agent identity. This eliminates the confusion and errors that occurred with the previous mixed approach.

## 🏗️ Architecture

### Core Principles

1. **User Token** = Internal identity for dashboard/API access (JWT with user_id)
2. **Agent Slug** = External identity for public websites (unique URL-friendly string)
3. **One-to-One Mapping** = Each user has exactly one agent profile
4. **Token-Driven** = All dashboard operations use user tokens

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │    Database     │
│                 │    │                  │    │                 │
│ unified-auth.ts │◄──►│ unified-auth.py  │◄──►│ users           │
│                 │    │                  │    │ agent_profiles  │
│ Token Storage   │    │ JWT Validation   │    │ agent_public_   │
│ User State      │    │ Identity Service │    │ profiles        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔐 Authentication Flow

### 1. User Login
```typescript
// Frontend
const authResponse = await unifiedAuthService.login(email, password);
// Returns: { access_token, user }
```

### 2. Token Storage
```typescript
// Automatically stored in localStorage
localStorage.setItem('unified_auth_token', access_token);
localStorage.setItem('unified_auth_user', JSON.stringify(user));
```

### 3. API Requests
```typescript
// All API requests automatically include token
const response = await unifiedAuthService.authenticatedRequest(url, options);
```

### 4. Backend Validation
```python
# Backend automatically validates token and extracts user_id
@router.get("/content/")
async def get_content(current_user: dict = Depends(get_current_user_token)):
    user_id = current_user["_id"]  # Always consistent
```

## 🎭 Identity Mapping

### User Identity (Internal)
- **Purpose**: Dashboard access, API authentication
- **Storage**: JWT token with user_id
- **Access**: `/api/v1/agent/profile` (requires token)

### Agent Identity (External)
- **Purpose**: Public website, marketing materials
- **Storage**: Unique slug in agent_profiles collection
- **Access**: `/api/v1/agent/public/{slug}` (no authentication)

### Mapping Service
```python
# Get complete user-agent mapping
mapping = await unified_identity_service.get_user_agent_mapping(user_id)
# Returns: { user: {...}, agent_profile: {...}, has_agent_profile: bool }
```

## 📡 API Endpoints

### Dashboard Endpoints (Token Required)
```
GET  /api/v1/agent/profile          # Get current agent profile
POST /api/v1/agent/profile          # Create agent profile
PUT  /api/v1/agent/profile          # Update agent profile
GET  /api/v1/agent/mapping          # Get user-agent mapping
GET  /api/v1/agent/slug             # Get agent slug
GET  /api/v1/content/               # Get content items
GET  /api/v1/publishing-logs/       # Get publishing logs
```

### Public Endpoints (No Authentication)
```
GET  /api/v1/agent/public/{slug}    # Get agent by slug
```

## 🔧 Implementation

### Backend Services

#### UnifiedIdentityService
```python
class UnifiedIdentityService:
    async def get_user_by_token(self, user_id: str) -> Optional[Dict[str, Any]]
    async def get_agent_profile_by_user_token(self, user_id: str) -> Optional[Dict[str, Any]]
    async def get_agent_by_slug(self, slug: str) -> Optional[Dict[str, Any]]
    async def create_agent_profile(self, user_id: str, profile_data: Dict[str, Any])
    async def update_agent_profile(self, user_id: str, profile_data: Dict[str, Any])
```

#### UnifiedAuthService
```python
class UnifiedAuthService:
    def create_access_token(self, user_id: str, email: str) -> str
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]
    async def get_current_user_by_token(self, token: str) -> Optional[Dict[str, Any]]
    async def get_current_agent_by_token(self, token: str) -> Optional[Dict[str, Any]]
```

### Frontend Service

#### UnifiedAuthService
```typescript
class UnifiedAuthService {
    async login(email: string, password: string): Promise<AuthResponse>
    async register(email: string, password: string): Promise<AuthResponse>
    async logout(): Promise<void>
    async getCurrentUser(): Promise<User | null>
    async getCurrentAgentProfile(): Promise<AgentProfile | null>
    async getUserAgentMapping(): Promise<UserAgentMapping | null>
    async createAgentProfile(profileData: Partial<AgentProfile>): Promise<AgentProfile>
    async updateAgentProfile(profileData: Partial<AgentProfile>): Promise<AgentProfile>
    async getAgentBySlug(slug: string): Promise<AgentProfile | null>
    async getAgentSlug(): Promise<string | null>
    async authenticatedRequest(url: string, options: RequestInit): Promise<Response>
}
```

## 🚀 Usage Examples

### Frontend Usage

#### Login and Get Profile
```typescript
// Login
await unifiedAuthService.login('user@example.com', 'password');

// Get current user
const user = await unifiedAuthService.getCurrentUser();

// Get agent profile
const agentProfile = await unifiedAuthService.getCurrentAgentProfile();

// Get complete mapping
const mapping = await unifiedAuthService.getUserAgentMapping();
```

#### Create Agent Profile
```typescript
const agentProfile = await unifiedAuthService.createAgentProfile({
    username: 'john-doe',
    email: 'john@example.com',
    bio: 'Real estate expert',
    tagline: 'Your trusted real estate partner'
});
```

#### Make Authenticated Requests
```typescript
// All requests automatically include authentication
const response = await unifiedAuthService.authenticatedRequest(
    '/api/v1/content/',
    { method: 'GET' }
);
```

### Backend Usage

#### Protected Endpoints
```python
@router.get("/content/")
async def get_content(
    current_user: dict = Depends(get_current_user_token),
    service: ContentService = Depends(get_content_service)
):
    # current_user["_id"] is always the correct user_id
    content = await service.get_content_by_user(current_user["_id"])
    return content
```

#### Agent Profile Management
```python
@router.post("/agent/profile")
async def create_agent_profile(
    profile_data: AgentProfileCreate,
    current_user: dict = Depends(get_current_user_token)
):
    # Automatically creates profile for the authenticated user
    agent_profile = await unified_identity_service.create_agent_profile(
        current_user["_id"],
        profile_data.dict()
    )
    return agent_profile
```

## 🔒 Security Features

### Token Security
- JWT tokens with expiration
- Automatic token validation
- Secure token storage
- Automatic logout on token expiry

### Access Control
- Users can only access their own resources
- Agent profiles are automatically linked to users
- Public access only through slugs
- No direct database access from frontend

### Data Validation
- Consistent user_id across all operations
- Automatic user-agent mapping validation
- Input sanitization and validation
- Error handling with proper HTTP status codes

## 🎯 Benefits

### For Developers
- **Consistent API**: All endpoints use the same authentication pattern
- **Type Safety**: Strong typing for all data structures
- **Error Handling**: Consistent error responses
- **Documentation**: Clear API documentation

### For Users
- **Reliable Access**: No more authentication issues
- **Fast Performance**: Optimized token-based authentication
- **Secure**: Proper security measures in place
- **User-Friendly**: Clear error messages

### For System
- **Scalable**: Token-based authentication scales well
- **Maintainable**: Clean separation of concerns
- **Debuggable**: Clear logging and error tracking
- **Future-Proof**: Easy to extend and modify

## 🔄 Migration from Old System

### What Changed
1. **Authentication**: Now uses JWT tokens instead of session-based auth
2. **User Identity**: Consistent user_id across all operations
3. **Agent Profiles**: Properly linked to users via user_id
4. **API Endpoints**: All use unified authentication

### What Stays the Same
1. **Database Schema**: Existing data is compatible
2. **Frontend Components**: Can be gradually migrated
3. **Business Logic**: Core functionality remains the same
4. **Public Access**: Agent slugs still work for public websites

## 🚀 Getting Started

### 1. Update Frontend Components
```typescript
// Old way
const response = await fetch('/api/v1/content/', {
    headers: { 'Authorization': `Bearer ${token}` }
});

// New way
const response = await unifiedAuthService.authenticatedRequest('/api/v1/content/');
```

### 2. Update Backend Endpoints
```python
# Old way
@router.get("/content/")
async def get_content(current_user: User = Depends(current_active_user)):
    user_id = str(current_user.id)

# New way
@router.get("/content/")
async def get_content(current_user: dict = Depends(get_current_user_token)):
    user_id = current_user["_id"]
```

### 3. Test the System
```bash
# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Test protected endpoint
curl -X GET http://localhost:8000/api/v1/agent/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📚 Additional Resources

- [JWT Authentication Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Next.js Authentication Patterns](https://nextjs.org/docs/authentication)

---

This unified system ensures that the authentication issues you experienced will never happen again. The system is designed to be robust, scalable, and maintainable for long-term use.
