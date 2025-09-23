# Automatic Token Expiry Logout

## Overview

This implementation provides automatic logout functionality when authentication tokens expire. When any API call returns a 401 Unauthorized response, the system will automatically log out the user and redirect them to the login page.

## How It Works

### 1. Authentication Interceptor
- **File**: `frontend/lib/auth/interceptor.ts`
- **Purpose**: Global HTTP interceptor that monitors all API responses for 401 errors
- **Key Features**:
  - Detects 401 responses from any API endpoint
  - Automatically triggers logout when token expires
  - Shows user-friendly notification
  - Redirects to login page
  - Prevents logout loops during login/register operations

### 2. Enhanced Fetch Function
- **Function**: `fetchWithAuthInterceptor()`
- **Purpose**: Replacement for standard `fetch()` that includes automatic token expiry handling
- **Usage**: All API clients now use this instead of direct `fetch()` calls

### 3. Updated API Clients
All API service files have been updated to use the auth interceptor:
- `frontend/lib/api/unified-client.ts` - Main API client
- `frontend/lib/crm-api.ts` - CRM API service
- `frontend/lib/auth/api.ts` - Authentication API
- `frontend/lib/properties/api.ts` - Properties API
- `frontend/lib/social_publishing/api.ts` - Social publishing API
- `frontend/lib/posts/api.ts` - Posts API
- `frontend/lib/agent/api.ts` - Agent API
- `frontend/lib/api.ts` - Legacy API (deprecated)

## Implementation Details

### Token Expiration Detection
```typescript
// 401 response detected
if (response.status === 401 && !this.isLoggingOut) {
    const currentState = authManager.getState();
    
    // Skip auto-logout for login/register endpoints
    const isAuthEndpoint = originalUrl && (
        originalUrl.includes('/auth/login') || 
        originalUrl.includes('/auth/register')
    );
    
    // Only auto-logout if user was authenticated and it's not an auth endpoint
    if (currentState.isAuthenticated && currentState.token && !isAuthEndpoint) {
        await this.handleTokenExpiration();
    }
}
```

### Automatic Logout Process
1. **Detect 401**: Interceptor catches 401 response
2. **Verify State**: Check if user was previously authenticated
3. **Log Out**: Call `authManager.logout()` to clear auth state
4. **Notify User**: Show "Session expired" notification
5. **Redirect**: Navigate to login page if not already there

### User Notification
- Shows a red notification: "Your session has expired. Please log in again."
- Notification automatically disappears after 5 seconds
- Uses native DOM methods to avoid circular dependencies

## Benefits

1. **Seamless UX**: Users are automatically logged out without manual intervention
2. **Security**: Prevents unauthorized API calls with expired tokens
3. **Consistency**: Works across all API endpoints uniformly
4. **No Loops**: Smart detection prevents logout during login attempts
5. **User Feedback**: Clear notification explains what happened

## Testing

The implementation can be tested by:
1. Logging in to the application
2. Manually expiring the token (or waiting for natural expiry)
3. Making any API call that requires authentication
4. Observing automatic logout and redirect to login page

## Error Handling

- **Network Errors**: Only handles 401 authentication errors, other errors pass through
- **Login Endpoints**: Skips auto-logout for `/auth/login` and `/auth/register` 
- **Logout Prevention**: Prevents multiple simultaneous logout attempts
- **Graceful Degradation**: Works even if logout API call fails

## Future Enhancements

Potential improvements could include:
- Token refresh attempts before logout
- Configurable retry logic
- Different handling for different token types
- User choice to extend session before logout

## Usage Example

```typescript
// All API calls now automatically handle token expiry
const response = await fetchWithAuthInterceptor('/api/v1/properties', {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` }
});

// If token is expired (401), user will be automatically logged out
// No additional code needed in components or services
```
