# Authentication Module

## Overview
This is a clean, centralized authentication module with perfect separation of concerns. It replaces the scattered auth logic and provides a single source of truth for authentication.

## Structure

```
lib/auth/
├── index.ts          # Main exports
├── types.ts          # Type definitions
├── api.ts            # API calls
├── manager.ts        # Auth state management
└── README.md         # This file
```

## Usage

### Basic Usage
```typescript
import { authManager } from '@/lib/auth';

// Register user
const result = await authManager.register({
  email: 'user@example.com',
  password: 'password123',
  first_name: 'John',
  last_name: 'Doe'
});

// Login user
const result = await authManager.login({
  email: 'user@example.com',
  password: 'password123'
});

// Logout user
await authManager.logout();

// Check authentication
const isAuth = await authManager.isAuthenticated();
```

### React Hook Usage
```typescript
import { useAuth } from '@/lib/auth';

function MyComponent() {
  const { isAuthenticated, user, login, logout } = useAuth();
  
  if (isAuthenticated) {
    return <div>Welcome, {user?.first_name}!</div>;
  }
  
  return <LoginForm onLogin={login} />;
}
```

### State Subscription
```typescript
import { authManager } from '@/lib/auth';

// Subscribe to auth state changes
const unsubscribe = authManager.subscribe((state) => {
  console.log('Auth state changed:', state);
});

// Unsubscribe when done
unsubscribe();
```

## API Endpoints

The module uses these FastAPI Users endpoints:
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout user

## Features

- ✅ **Clean Separation**: Auth logic isolated in dedicated module
- ✅ **Type Safety**: Full TypeScript support
- ✅ **State Management**: Centralized auth state
- ✅ **Token Management**: Automatic token refresh
- ✅ **Error Handling**: Comprehensive error handling
- ✅ **React Integration**: Hooks for React components
- ✅ **Backward Compatibility**: Legacy auth.ts still works

## Migration

### From Old Auth System
```typescript
// OLD
import { authManager } from '@/lib/auth';

// NEW (same import, but cleaner implementation)
import { authManager } from '@/lib/auth';
```

### From useAuth Hook
```typescript
// OLD
import { useAuth } from '@/hooks/useAuth';

// NEW
import { useAuth } from '@/lib/auth';
```

## Configuration

Set the API base URL in your environment:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Error Handling

All auth operations return a result object:
```typescript
const result = await authManager.login(credentials);

if (result.success) {
  // Login successful
  console.log('User:', result.user);
} else {
  // Login failed
  console.error('Error:', result.error);
}
```

## Token Management

- Tokens are automatically stored in localStorage
- Automatic token refresh before expiration
- Automatic logout on token validation failure
- Secure token handling with proper headers

## Testing

The module is designed to be easily testable:
- All dependencies are injected
- State changes are observable
- API calls are abstracted
- Mock implementations available
